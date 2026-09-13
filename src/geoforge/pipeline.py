from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .builders.base import BuildArtifact, BuildContext, ContactExpectation
from .errors import BuildError, GeoForgeError, QualityGateError
from .manifest import ArtifactRecord, BuildManifest
from .planning import plan_scene
from .quality.model import BuildReport, Issue, Severity, ValidationReport
from .registry import BuilderRegistry, create_full_registry
from .spec import SceneSpec


@dataclass(frozen=True)
class DraftCompilation:
    artifacts: tuple[BuildArtifact, ...]
    contacts: tuple[ContactExpectation, ...]


@dataclass(frozen=True)
class PipelineResult:
    report: BuildReport
    manifest: BuildManifest

    @property
    def ok(self) -> bool:
        return self.report.status == "PASS"

    def compact_dict(self) -> dict[str, object]:
        return self.report.compact_dict()

    def compact_json(self) -> str:
        return json.dumps(self.compact_dict(), sort_keys=True, separators=(",", ":"))


class RegenerationGuard:
    """Rejects repeated invalid deterministic output during one regeneration workflow."""

    def __init__(self) -> None:
        self._failures: set[tuple[str, str]] = set()

    def record_failure(self, artifact_id: str, mesh_fingerprint: str) -> bool:
        key = (artifact_id, mesh_fingerprint)
        if key in self._failures:
            return False
        self._failures.add(key)
        return True


def compile_drafts(
    spec: SceneSpec,
    *,
    registry: BuilderRegistry | None = None,
    entity_ids: set[str] | None = None,
) -> DraftCompilation:
    registry = registry or create_full_registry()
    context = BuildContext(spec, spec.spec_hash, spec.quality)
    scene_plan = plan_scene(spec, registry)
    artifacts: list[BuildArtifact] = []
    contacts: list[ContactExpectation] = []
    artifact_ids: set[str] = set()
    selected = entity_ids if entity_ids is not None else {item.entity.id for item in scene_plan.entities}
    unknown_selected = selected - {item.entity.id for item in scene_plan.entities}
    if unknown_selected:
        raise BuildError(
            f"Unknown entity IDs: {', '.join(sorted(unknown_selected))}",
            code="BUILD.UNKNOWN_ENTITY",
        )
    for entity_plan in scene_plan.entities:
        if entity_plan.entity.id not in selected:
            continue
        builder = registry.get(entity_plan.entity.kind)
        builder_plan = builder.plan(entity_plan, context)
        product = builder.build(builder_plan, context)
        if not product.artifacts:
            raise BuildError(
                f"Builder {builder.kind!r} produced no artifacts",
                code="BUILD.EMPTY_PRODUCT",
            )
        for artifact in product.artifacts:
            if artifact.contract is None:  # defensive: third-party builders may ignore typing
                raise BuildError(
                    f"Artifact {artifact.artifact_id!r} has no GeometryContract",
                    code="BUILD.MISSING_CONTRACT",
                )
            if artifact.artifact_id in artifact_ids:
                raise BuildError(
                    f"Builder produced duplicate artifact ID {artifact.artifact_id!r}",
                    code="BUILD.DUPLICATE_ARTIFACT_ID",
                )
            artifact_ids.add(artifact.artifact_id)
        artifacts.extend(product.artifacts)
        contacts.extend(product.contacts)
    selected_artifacts = {artifact.artifact_id for artifact in artifacts}
    contacts = [
        contact
        for contact in contacts
        if contact.first_artifact_id in selected_artifacts and contact.second_artifact_id in selected_artifacts
    ]
    return DraftCompilation(tuple(artifacts), tuple(contacts))


def compile_scene(
    spec: SceneSpec,
    *,
    output_root: str | Path = ".",
    registry: BuilderRegistry | None = None,
    entity_ids: set[str] | None = None,
    regeneration_guard: RegenerationGuard | None = None,
) -> PipelineResult:
    try:
        import bpy
    except ImportError as exc:  # pragma: no cover - exercised outside Blender explicitly
        from .errors import BlenderUnavailableError

        raise BlenderUnavailableError("compile_scene() must run inside Blender") from exc

    from .operations.transaction import StagingTransaction
    from .geometry.blender import save_blend_file
    from .quality.mesh import validate_contacts, validate_materialized
    from .repair.cheap import begin_tier1_repair
    from .repair.policy import decide_tier1

    registry = registry or create_full_registry()
    guard = regeneration_guard or RegenerationGuard()
    output_root = Path(output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    report_path = (output_root / spec.output.report).resolve()
    manifest_path = (output_root / spec.output.manifest).resolve()
    blend_path = (output_root / spec.output.blend).resolve()
    _ensure_below(output_root, report_path)
    _ensure_below(output_root, manifest_path)
    _ensure_below(output_root, blend_path)

    report = BuildReport(
        scene_id=spec.scene_id,
        spec_hash=spec.spec_hash,
        blender_version=bpy.app.version_string,
        report_path=str(report_path),
        manifest_path=str(manifest_path),
    )
    manifest = BuildManifest(spec.scene_id, spec.spec_hash, spec.seed, bpy.app.version_string)
    artifacts: tuple[BuildArtifact, ...] = ()
    transaction: StagingTransaction | None = None
    published = False

    try:
        report.stage = "PLAN"
        compilation = compile_drafts(spec, registry=registry, entity_ids=entity_ids)
        artifacts = compilation.artifacts

        report.stage = "VALIDATE_DRAFTS"
        draft_failed = False
        for artifact in artifacts:
            draft_issues = artifact.draft.check()
            if not draft_issues:
                continue
            validation = ValidationReport(
                artifact.entity_id,
                artifact.artifact_id,
                artifact.contract.topology_intent.value,
                "DRAFT",
                metrics={
                    "vertices": len(artifact.draft.vertices),
                    "edges": len(artifact.draft.edges),
                    "faces": len(artifact.draft.faces),
                },
                issues=[Issue(item.code, item.message) for item in draft_issues],
                recommended_action="REGENERATE",
            )
            report.artifact_reports.append(validation)
            first_failure = guard.record_failure(artifact.artifact_id, artifact.draft.fingerprint())
            if not first_failure:
                report.issues.append(
                    Issue(
                        "BUILD.BUILDER_BUG",
                        f"builder repeated invalid deterministic output for {artifact.entity_id!r}",
                    )
                )
            draft_failed = True
        if draft_failed:
            raise BuildError("one or more builders produced invalid MeshDraft", code="BUILD.INVALID_DRAFT")

        report.stage = "MATERIALIZE_STAGING"
        transaction = StagingTransaction()
        materialized = [transaction.materialize(artifact) for artifact in artifacts]

        report.stage = "GEOMETRY_QA"
        final_reports: list[ValidationReport] = []
        for item in materialized:
            initial = validate_materialized(item, stage="POST_BUILD")
            current = initial
            if initial.status == "FAIL":
                decision = decide_tier1(initial)
                if decision.allowed:
                    attempt = begin_tier1_repair(item.object, item.artifact.contract)
                    repaired = validate_materialized(item, stage="POST_REPAIR")
                    improved = _error_count(repaired) < _error_count(initial)
                    if repaired.status == "PASS" and improved and attempt.within_budget(item.artifact.contract):
                        attempt.commit()
                        repaired.recommended_action = "NONE"
                        report.repaired_artifacts.append(item.artifact.artifact_id)
                        report.repair_records.append(
                            {
                                "artifact": item.artifact.artifact_id,
                                "outcome": "COMMITTED",
                                "before_issue_counts": initial.issue_counts,
                                "after_issue_counts": repaired.issue_counts,
                            }
                        )
                        current = repaired
                    else:
                        attempt.rollback()
                        initial.recommended_action = "REGENERATE"
                        report.repair_records.append(
                            {
                                "artifact": item.artifact.artifact_id,
                                "outcome": "ROLLED_BACK",
                                "before_issue_counts": initial.issue_counts,
                                "after_issue_counts": repaired.issue_counts,
                            }
                        )
                        report.issues.append(
                            Issue(
                                "REPAIR.ROLLED_BACK",
                                f"Tier 1 repair was rejected for {item.artifact.artifact_id!r}",
                                Severity.WARNING,
                            )
                        )
                else:
                    initial.recommended_action = "REGENERATE"
            final_reports.append(current)
        report.add_reports(final_reports)

        failing = [item for item in final_reports if item.status == "FAIL"]
        if failing:
            for validation in failing:
                artifact = next(item for item in artifacts if item.artifact_id == validation.artifact)
                first_failure = guard.record_failure(artifact.artifact_id, artifact.draft.fingerprint())
                code = "BUILD.INVALID_GEOMETRY" if first_failure else "BUILD.BUILDER_BUG"
                report.issues.append(
                    Issue(code, f"quality gate failed for {artifact.artifact_id!r}")
                )
            raise QualityGateError("geometry quality gate failed")

        report.stage = "SCENE_QA"
        contact_report = validate_contacts(materialized, compilation.contacts)
        if compilation.contacts or contact_report.status == "FAIL":
            report.artifact_reports.append(contact_report)
        if contact_report.status == "FAIL":
            contact_report.recommended_action = "REGENERATE"
            raise QualityGateError("scene contact quality gate failed")

        report.stage = "COMMIT"
        report.committed_objects = transaction.commit()
        published = True
        transaction = None

        if spec.output.save_blend:
            report.stage = "SAVE_BLEND"
            blend_path.parent.mkdir(parents=True, exist_ok=True)
            if not save_blend_file(str(blend_path)):
                raise BuildError("Blender did not save the blend file", code="OUTPUT.SAVE_FAILED")

        report.stage = "COMPLETE"
        manifest.status = "PASS"
    except GeoForgeError as exc:
        if transaction is not None:
            transaction.rollback()
        report.issues.append(Issue(exc.code, str(exc)))
        report.failed_stage = report.stage
        report.stage = "FAILED"
        manifest.status = "FAIL"
    except Exception as exc:  # defensive boundary: never silently publish an exception
        if transaction is not None:
            transaction.rollback()
        report.issues.append(Issue("BUILD.UNEXPECTED", f"{type(exc).__name__}: {exc}"))
        report.failed_stage = report.stage
        report.stage = "FAILED"
        manifest.status = "FAIL"

    manifest.artifacts = [
        ArtifactRecord(
            artifact_id=artifact.artifact_id,
            entity_id=artifact.entity_id,
            object_name=artifact.object_name,
            builder_id=artifact.builder_id,
            builder_version=artifact.builder_version,
            entity_seed=artifact.entity_seed,
            entity_spec_hash=artifact.entity_spec_hash,
            mesh_fingerprint=artifact.draft.fingerprint(),
            topology_intent=artifact.contract.topology_intent.value,
            published=published,
        )
        for artifact in artifacts
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report.full_dict(), indent=2, sort_keys=True), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return PipelineResult(report, manifest)


def _error_count(report: ValidationReport) -> int:
    return sum(issue.count for issue in report.issues if issue.severity is Severity.ERROR)


def _ensure_below(root: Path, candidate: Path) -> None:
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise BuildError("output path escapes output root", code="OUTPUT.UNSAFE_PATH") from exc

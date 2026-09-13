from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True)
class Issue:
    code: str
    message: str
    severity: Severity = Severity.ERROR
    count: int = 1
    samples: tuple[Any, ...] = ()

    def compact_dict(self) -> dict[str, Any]:
        committed_limit = 16
        repaired_limit = 16
        result: dict[str, Any] = {
            "code": self.code,
            "severity": self.severity.value,
            "count": self.count,
            "message": self.message,
        }
        if self.samples:
            result["samples"] = list(self.samples[:8])
        return result


@dataclass
class ValidationReport:
    entity: str
    artifact: str
    profile: str
    stage: str
    metrics: dict[str, Any] = field(default_factory=dict)
    issues: list[Issue] = field(default_factory=list)
    recommended_action: str = "NONE"

    @property
    def status(self) -> str:
        return "FAIL" if any(issue.severity is Severity.ERROR for issue in self.issues) else "PASS"

    @property
    def issue_counts(self) -> dict[str, int]:
        counts: Counter[str] = Counter()
        for issue in self.issues:
            counts[issue.code] += issue.count
        return dict(sorted(counts.items()))

    def compact_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "stage": self.stage,
            "entity": self.entity,
            "artifact": self.artifact,
            "profile": self.profile,
            "issue_counts": self.issue_counts,
            "metrics": self.metrics,
            "issues": [issue.compact_dict() for issue in self.issues[:16]],
            "recommended_action": {"kind": self.recommended_action},
        }


@dataclass
class BuildReport:
    scene_id: str
    spec_hash: str
    stage: str = "LOAD_SPEC"
    failed_stage: str | None = None
    artifact_reports: list[ValidationReport] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    committed_objects: list[str] = field(default_factory=list)
    repaired_artifacts: list[str] = field(default_factory=list)
    repair_records: list[dict[str, Any]] = field(default_factory=list)
    blender_version: str | None = None
    report_path: str | None = None
    manifest_path: str | None = None

    @property
    def status(self) -> str:
        if any(issue.severity is Severity.ERROR for issue in self.issues):
            return "FAIL"
        if any(report.status == "FAIL" for report in self.artifact_reports):
            return "FAIL"
        return "PASS" if self.stage == "COMPLETE" else "FAIL"

    def add_reports(self, reports: Iterable[ValidationReport]) -> None:
        self.artifact_reports.extend(reports)

    def compact_dict(self) -> dict[str, Any]:
        committed_limit = 16
        repaired_limit = 16
        counts: Counter[str] = Counter()
        for issue in self.issues:
            counts[issue.code] += issue.count
        for report in self.artifact_reports:
            counts.update(report.issue_counts)
        result: dict[str, Any] = {
            "status": self.status,
            "stage": self.stage,
            "scene_id": self.scene_id,
            "spec_hash": self.spec_hash,
            "blender_version": self.blender_version,
            "artifacts": sum(report.entity != "__scene__" for report in self.artifact_reports),
            "committed_object_count": len(self.committed_objects),
            "committed_objects": list(self.committed_objects[:committed_limit]),
            "repaired_artifact_count": len(self.repaired_artifacts),
            "repaired_artifacts": list(self.repaired_artifacts[:repaired_limit]),
            "issue_counts": dict(sorted(counts.items())),
        }
        if self.failed_stage is not None:
            result["failed_stage"] = self.failed_stage
        if self.report_path:
            result["report_path"] = self.report_path
        if self.manifest_path:
            result["manifest_path"] = self.manifest_path
        if len(self.committed_objects) > committed_limit:
            result["committed_objects_truncated"] = True
        if len(self.repaired_artifacts) > repaired_limit:
            result["repaired_artifacts_truncated"] = True
        return result

    def full_dict(self) -> dict[str, Any]:
        result = self.compact_dict()
        result["committed_objects"] = list(self.committed_objects)
        result["repaired_artifacts"] = list(self.repaired_artifacts)
        result["repair_records"] = list(self.repair_records)
        result.pop("committed_objects_truncated", None)
        result.pop("repaired_artifacts_truncated", None)
        result["issues"] = [issue.compact_dict() for issue in self.issues]
        result["artifact_reports"] = [report.compact_dict() for report in self.artifact_reports]
        return result

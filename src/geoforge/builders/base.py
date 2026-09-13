from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, ClassVar, Protocol

from ..geometry.model import (
    Anchor,
    GeometryContract,
    MeshDraft,
    RepairLimits,
    TopologyIntent,
)
from ..planning import EntityBuildPlan
from ..spec import QualitySpec, SceneSpec, TransformSpec


@dataclass(frozen=True)
class ContactExpectation:
    first_artifact_id: str
    second_artifact_id: str
    tolerance: float


@dataclass(frozen=True)
class BuildArtifact:
    artifact_id: str
    object_name: str
    entity_id: str
    part: str
    draft: MeshDraft
    contract: GeometryContract
    transform: TransformSpec
    builder_id: str
    builder_version: str
    entity_seed: int
    entity_spec_hash: str
    scene_spec_hash: str


@dataclass(frozen=True)
class BuildProduct:
    artifacts: tuple[BuildArtifact, ...]
    contacts: tuple[ContactExpectation, ...] = ()


@dataclass(frozen=True)
class BuildContext:
    scene: SceneSpec
    spec_hash: str
    quality: QualitySpec


class Builder(Protocol):
    kind: ClassVar[str]
    version: ClassVar[str]
    required_params: ClassVar[tuple[str, ...]]
    optional_params: ClassVar[tuple[str, ...]]
    summary: ClassVar[str]

    def validate_params(self, entity_plan: EntityBuildPlan, context: BuildContext) -> None: ...

    def plan(self, entity_plan: EntityBuildPlan, context: BuildContext) -> Any: ...

    def build(self, plan: Any, context: BuildContext) -> BuildProduct: ...


def solid_contract(draft: MeshDraft, min_feature_size: float) -> GeometryContract:
    bounds = draft.bounds
    epsilon = max(1e-9, min_feature_size * 1e-5)
    bound_allowance = max(1e-8, min_feature_size * 1e-4)
    minimum = bounds.minimum
    maximum = bounds.maximum
    anchors = (
        Anchor("min", minimum),
        Anchor(
            "base_center",
            ((minimum[0] + maximum[0]) * 0.5, (minimum[1] + maximum[1]) * 0.5, minimum[2]),
        ),
        Anchor(
            "top_center",
            ((minimum[0] + maximum[0]) * 0.5, (minimum[1] + maximum[1]) * 0.5, maximum[2]),
        ),
    )
    return GeometryContract(
        topology_intent=TopologyIntent.SOLID,
        expected_component_count=1,
        local_bounds=bounds,
        dimensions=bounds.dimensions,
        named_anchors=anchors,
        minimum_feature_size=min_feature_size,
        repair_limits=RepairLimits(epsilon, bound_allowance, bound_allowance, True),
    )


def make_artifact(
    entity_plan: EntityBuildPlan,
    draft: MeshDraft,
    contract: GeometryContract,
    *,
    part: str,
) -> BuildArtifact:
    artifact_id = f"{entity_plan.entity.id}/{part}"
    safe_entity = entity_plan.entity.id.replace(".", "_").replace("-", "_")
    safe_part = part.replace(".", "_").replace("-", "_")
    name_digest = hashlib.sha256(artifact_id.encode("utf-8")).hexdigest()[:16]
    return BuildArtifact(
        artifact_id=artifact_id,
        object_name=f"GF__{safe_entity[:20]}__{safe_part[:16]}__{name_digest}",
        entity_id=entity_plan.entity.id,
        part=part,
        draft=draft,
        contract=contract,
        transform=entity_plan.entity.transform,
        builder_id=entity_plan.entity.kind,
        builder_version=entity_plan.builder_version,
        entity_seed=entity_plan.entity_seed,
        entity_spec_hash=entity_plan.entity_spec_hash,
        scene_spec_hash=entity_plan.scene_spec_hash,
    )

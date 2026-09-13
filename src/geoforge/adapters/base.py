from __future__ import annotations

from typing import Any, ClassVar

from ..builders.base import BuildContext, BuildProduct, make_artifact, solid_contract
from ..errors import BuildError
from ..geometry.model import MeshDraft
from ..planning import EntityBuildPlan
from ..spec import ExtensionParams
from .schema import schema_fields, validate_extension_values


class GeneratorAdapter:
    """Builder that adapts a donor generator into MeshDraft artifacts for the V1 pipeline."""

    generator_id: ClassVar[str]
    kind: ClassVar[str]
    version: ClassVar[str] = "1.0.0"
    required_params: ClassVar[tuple[str, ...]] = ()
    optional_params: ClassVar[tuple[str, ...]] = ()
    summary: ClassVar[str] = ""

    def validate_params(self, entity_plan: EntityBuildPlan, context: BuildContext) -> None:
        params = entity_plan.entity.params
        if not isinstance(params, ExtensionParams) or params.kind != self.kind:
            raise BuildError(f"{self.kind} received the wrong parameter type", code="BUILD.PARAM_TYPE")
        validate_extension_values(self.kind, params.as_dict(), f"/entities/{entity_plan.entity.id}/params")

    def plan(self, entity_plan: EntityBuildPlan, context: BuildContext) -> EntityBuildPlan:
        self.validate_params(entity_plan, context)
        return entity_plan

    def values(self, entity_plan: EntityBuildPlan) -> dict[str, Any]:
        params = entity_plan.entity.params
        assert isinstance(params, ExtensionParams)
        return params.as_dict()

    def artifact(self, entity_plan: EntityBuildPlan, draft: MeshDraft, context: BuildContext, part: str):
        return make_artifact(
            entity_plan,
            draft,
            solid_contract(draft, context.quality.min_feature_size),
            part=part,
        )

    def product(self, artifacts: list, contacts: tuple = ()) -> BuildProduct:
        if not artifacts:
            raise BuildError(f"Adapter {self.kind!r} produced no artifacts", code="BUILD.EMPTY_PRODUCT")
        return BuildProduct(tuple(artifacts), contacts)


def required_and_optional(kind: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    required: list[str] = []
    optional: list[str] = []
    for name, field in schema_fields(kind).items():
        if field.get("required"):
            required.append(name)
        else:
            optional.append(name)
    return tuple(required), tuple(optional)

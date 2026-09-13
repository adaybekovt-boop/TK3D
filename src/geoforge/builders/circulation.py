from __future__ import annotations

from ..errors import BuildError
from ..geometry.primitives import extrude_profile
from ..planning import EntityBuildPlan, StairPlan, plan_stairs
from ..spec import StairsParams
from .base import BuildContext, BuildProduct, make_artifact, solid_contract


class StraightStairsBuilder:
    kind = "straight_stairs"
    version = "1.0.0"
    required_params = ("width", "run", "rise")
    optional_params = ("max_riser", "min_tread")
    summary = "One closed stepped solid with exact target rise."

    def validate_params(self, entity_plan: EntityBuildPlan, context: BuildContext) -> None:
        if not isinstance(entity_plan.entity.params, StairsParams):
            raise BuildError("straight_stairs received the wrong parameter type", code="BUILD.PARAM_TYPE")

    def plan(self, entity_plan: EntityBuildPlan, context: BuildContext) -> tuple[EntityBuildPlan, StairPlan]:
        self.validate_params(entity_plan, context)
        params = entity_plan.entity.params
        assert isinstance(params, StairsParams)
        return entity_plan, plan_stairs(params)

    def build(self, plan: tuple[EntityBuildPlan, StairPlan], context: BuildContext) -> BuildProduct:
        entity_plan, stairs = plan
        draft = extrude_profile(
            stairs.profile,
            stairs.width,
            axis="Y",
            name=f"{entity_plan.entity.id}.body",
        )
        artifact = make_artifact(
            entity_plan,
            draft,
            solid_contract(draft, context.quality.min_feature_size),
            part="body",
        )
        return BuildProduct((artifact,))

from __future__ import annotations

from ..builders.base import BuildContext, BuildProduct
from ..geometry.primitives import extrude_profile
from ..planning import EntityBuildPlan
from .base import GeneratorAdapter, required_and_optional


class RoadBuilder(GeneratorAdapter):
    generator_id = "infrastructure.road"
    kind = "road"
    required_params, optional_params = required_and_optional(kind)
    summary = "Straight road slab with optional sidewalks and shoulders."

    def build(self, plan: EntityBuildPlan, context: BuildContext) -> BuildProduct:
        values = self.values(plan)
        profile = _road_profile(values)
        draft = extrude_profile(profile, values["length"], axis="Y", name=f"{plan.entity.id}.body")
        return self.product([self.artifact(plan, draft, context, "body")])


def _road_profile(values: dict) -> tuple[tuple[float, float], ...]:
    half = values["width"] * 0.5
    thickness = values["thickness"]
    shoulder = values["shoulder_width"] if values["shoulders"] else 0.0
    if not values["sidewalks"]:
        total = half + shoulder
        return (
            (-total, 0.0),
            (total, 0.0),
            (total, -thickness),
            (-total, -thickness),
        )
    walk = values["sidewalk_width"]
    curb = values["sidewalk_height"]
    inner = half + shoulder
    outer = inner + walk
    return (
        (-outer, curb),
        (-inner, curb),
        (-inner, 0.0),
        (inner, 0.0),
        (inner, curb),
        (outer, curb),
        (outer, -thickness),
        (-outer, -thickness),
    )

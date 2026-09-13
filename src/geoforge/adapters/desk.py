from __future__ import annotations

from ..builders.base import BuildContext, BuildProduct, ContactExpectation
from ..planning import EntityBuildPlan
from .base import GeneratorAdapter, required_and_optional
from .meshutil import box_at


class SimpleDeskBuilder(GeneratorAdapter):
    generator_id = "furniture.desk.simple"
    kind = "desk"
    required_params, optional_params = required_and_optional(kind)
    summary = "Simple desk: rectangular top and four square legs."

    def build(self, plan: EntityBuildPlan, context: BuildContext) -> BuildProduct:
        values = self.values(plan)
        width = values["width"]
        depth = values["depth"]
        height = values["height"]
        top_t = values["thickness"]
        leg = values["leg_size"]
        inset = values["leg_inset"]
        artifacts = [
            self.artifact(
                plan,
                box_at((0.0, 0.0, height - top_t), (width, depth, height), name=f"{plan.entity.id}.top"),
                context,
                "top",
            )
        ]
        contacts: list[ContactExpectation] = []
        corners = (
            (inset, inset, "leg.sw"),
            (width - inset - leg, inset, "leg.se"),
            (inset, depth - inset - leg, "leg.nw"),
            (width - inset - leg, depth - inset - leg, "leg.ne"),
        )
        top_id = artifacts[0].artifact_id
        for x, y, part in corners:
            artifacts.append(
                self.artifact(
                    plan,
                    box_at((x, y, 0.0), (x + leg, y + leg, height - top_t), name=f"{plan.entity.id}.{part}"),
                    context,
                    part,
                )
            )
            contacts.append(
                ContactExpectation(top_id, artifacts[-1].artifact_id, context.quality.min_feature_size * 1e-4)
            )
        return self.product(artifacts, tuple(contacts))

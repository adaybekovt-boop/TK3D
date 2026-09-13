from __future__ import annotations

import math

from ..builders.base import BuildContext, BuildProduct, ContactExpectation
from ..planning import EntityBuildPlan
from .base import GeneratorAdapter, required_and_optional
from .meshutil import box_at, rotate_draft_x, translate_draft


class ClimbableLadderBuilder(GeneratorAdapter):
    """Two rails + rungs. A person climbs with hands and feet. Not walkable stairs."""

    generator_id = "architecture.stairs.climbable_ladder"
    kind = "climbable_ladder"
    required_params, optional_params = required_and_optional(kind)
    summary = "Climbable ladder: two rails and rungs, optional lean. Not walkable stairs."

    def build(self, plan: EntityBuildPlan, context: BuildContext) -> BuildProduct:
        values = self.values(plan)
        height = values["height"]
        gap = values["width"]
        pitch = values["rung_spacing"]
        rail_r = values["rail_radius"]
        rung_r = values["rung_radius"]
        theta = math.radians(values["lean_deg"])
        cosine = math.cos(theta)
        if cosine <= 1e-9:
            cosine = 1e-9
        rail_len = height / cosine
        rail_x = gap * 0.5 + rail_r
        artifacts = []
        contacts: list[ContactExpectation] = []

        for sign, tag in ((-1, "L"), (1, "R")):
            local = box_at((-rail_r, -rail_r, 0.0), (rail_r, rail_r, rail_len), name=f"{plan.entity.id}.rail.{tag}")
            shifted = translate_draft(local, (sign * rail_x, 0.0, 0.0))
            draft = rotate_draft_x(shifted, -theta, name=shifted.name)
            artifacts.append(self.artifact(plan, draft, context, f"rail.{tag}"))

        z0 = max(2.0 * rung_r, min(0.25, height * 0.3))
        last_limit = height - rung_r
        n_rungs = int((last_limit - z0) // pitch) + 1
        n_rungs = max(1, n_rungs)
        rung_len = gap
        for index in range(n_rungs):
            z_i = z0 + index * pitch
            if z_i > last_limit + 1e-12:
                break
            y_i = z_i * math.tan(theta)
            local = box_at(
                (-rung_len * 0.5, -rung_r, -rung_r),
                (rung_len * 0.5, rung_r, rung_r),
                name=f"{plan.entity.id}.rung.{index:03d}",
            )
            draft = translate_draft(local, (0.0, y_i, z_i), name=local.name)
            artifacts.append(self.artifact(plan, draft, context, f"rung.{index:03d}"))
            rung_id = artifacts[-1].artifact_id
            for rail in artifacts[:2]:
                contacts.append(ContactExpectation(rail.artifact_id, rung_id, context.quality.min_feature_size * 1e-4))

        return self.product(artifacts, tuple(contacts))

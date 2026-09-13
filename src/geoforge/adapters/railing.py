from __future__ import annotations

from ..builders.base import BuildContext, BuildProduct
from ..planning import EntityBuildPlan
from .base import GeneratorAdapter, required_and_optional
from .meshutil import box_at


class RailingBuilder(GeneratorAdapter):
    generator_id = "architecture.railing"
    kind = "railing"
    required_params, optional_params = required_and_optional(kind)
    summary = "Standalone railing: end posts, top/bottom rails, posts/rails/wall fill."

    def build(self, plan: EntityBuildPlan, context: BuildContext) -> BuildProduct:
        values = self.values(plan)
        length = values["length"]
        height = values["height"]
        post = values["post_size"]
        rail_t = values["rail_thickness"]
        spacing = values["post_spacing"]
        fill = values["fill"]
        artifacts = []

        artifacts.append(
            self.artifact(
                plan,
                box_at((0.0, 0.0, 0.0), (post, post, height), name=f"{plan.entity.id}.post.start"),
                context,
                "post.start",
            )
        )
        artifacts.append(
            self.artifact(
                plan,
                box_at((length - post, 0.0, 0.0), (length, post, height), name=f"{plan.entity.id}.post.end"),
                context,
                "post.end",
            )
        )
        artifacts.append(
            self.artifact(
                plan,
                box_at((0.0, 0.0, height - rail_t), (length, post, height), name=f"{plan.entity.id}.rail.top"),
                context,
                "rail.top",
            )
        )
        if values["bottom_rail"]:
            artifacts.append(
                self.artifact(
                    plan,
                    box_at((0.0, 0.0, 0.0), (length, post, rail_t), name=f"{plan.entity.id}.rail.bottom"),
                    context,
                    "rail.bottom",
                )
            )

        inner_left = post
        inner_right = length - post
        if fill == "posts":
            x = inner_left + spacing
            index = 0
            while x + post <= inner_right + 1e-12:
                artifacts.append(
                    self.artifact(
                        plan,
                        box_at((x, 0.0, rail_t), (x + post, post, height - rail_t), name=f"{plan.entity.id}.fill.{index:03d}"),
                        context,
                        f"fill.{index:03d}",
                    )
                )
                x += spacing
                index += 1
        elif fill == "rails":
            usable = max(height - 2.0 * rail_t, rail_t)
            count = int(values["rail_count"])
            step = usable / (count + 1)
            for index in range(count):
                z = rail_t + (index + 1) * step - rail_t * 0.5
                artifacts.append(
                    self.artifact(
                        plan,
                        box_at((inner_left, 0.0, z), (inner_right, post, z + rail_t), name=f"{plan.entity.id}.fill.{index:03d}"),
                        context,
                        f"fill.{index:03d}",
                    )
                )
        else:
            artifacts.append(
                self.artifact(
                    plan,
                    box_at(
                        (inner_left, 0.0, rail_t),
                        (inner_right, post, height - rail_t),
                        name=f"{plan.entity.id}.fill.wall",
                    ),
                    context,
                    "fill.wall",
                )
            )
        return self.product(artifacts)

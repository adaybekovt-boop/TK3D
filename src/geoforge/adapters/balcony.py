from __future__ import annotations

from ..builders.base import BuildContext, BuildProduct
from ..planning import EntityBuildPlan
from .base import GeneratorAdapter, required_and_optional
from .meshutil import box_at


class BalconyBuilder(GeneratorAdapter):
    generator_id = "architecture.balcony"
    kind = "balcony"
    required_params, optional_params = required_and_optional(kind)
    summary = "Balcony slab projecting in +Y, optional three-sided railing."

    def build(self, plan: EntityBuildPlan, context: BuildContext) -> BuildProduct:
        values = self.values(plan)
        width = values["width"]
        depth = values["depth"]
        slab_t = values["slab_thickness"]
        artifacts = [
            self.artifact(
                plan,
                box_at((0.0, 0.0, -slab_t), (width, depth, 0.0), name=f"{plan.entity.id}.slab"),
                context,
                "slab",
            )
        ]
        if not values["has_railing"]:
            return self.product(artifacts)

        post = values["post_size"]
        height = values["rail_height"]
        spacing = values["post_spacing"]
        rail_t = max(post * 0.75, 0.02)

        def add_post(x: float, y: float, part: str) -> None:
            artifacts.append(
                self.artifact(
                    plan,
                    box_at((x, y, 0.0), (x + post, y + post, height), name=f"{plan.entity.id}.{part}"),
                    context,
                    part,
                )
            )

        def add_rail(x0: float, y0: float, x1: float, y1: float, z0: float, z1: float, part: str) -> None:
            artifacts.append(
                self.artifact(
                    plan,
                    box_at((x0, y0, z0), (x1, y1, z1), name=f"{plan.entity.id}.{part}"),
                    context,
                    part,
                )
            )

        posts: list[tuple[float, float, str]] = []
        # Three open sides: -X, +Y, +X. y=0 is the wall attachment.
        y = 0.0
        index = 0
        while y + post <= depth + 1e-12:
            posts.append((0.0, y, f"post.west.{index:03d}"))
            posts.append((width - post, y, f"post.east.{index:03d}"))
            y += spacing
            index += 1
        if posts[-1][1] < depth - post - 1e-9:
            posts.append((0.0, depth - post, f"post.west.front"))
            posts.append((width - post, depth - post, f"post.east.front"))
        x = spacing
        index = 0
        while x + post < width - post - 1e-12:
            posts.append((x, depth - post, f"post.south.{index:03d}"))
            x += spacing
            index += 1

        seen: set[tuple[float, float]] = set()
        for x, y, part in posts:
            key = (round(x, 6), round(y, 6))
            if key in seen:
                continue
            seen.add(key)
            add_post(x, y, part)

        add_rail(0.0, depth - post, width, depth, height - rail_t, height, "rail.front")
        add_rail(0.0, 0.0, post, depth, height - rail_t, height, "rail.west")
        add_rail(width - post, 0.0, width, depth, height - rail_t, height, "rail.east")
        return self.product(artifacts)

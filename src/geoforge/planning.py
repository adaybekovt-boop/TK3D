from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Iterable

from .errors import BuildError, SpecError
from .spec import EntitySpec, OpeningSpec, SceneSpec, StairsParams, derive_entity_seed, entity_spec_hash


@dataclass(frozen=True)
class WallCellPlan:
    x0: float
    x1: float
    z0: float
    z1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.z1 - self.z0


@dataclass(frozen=True)
class StairPlan:
    riser_count: int
    riser_height: float
    tread_depth: float
    width: float
    run: float
    rise: float
    profile: tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class EntityBuildPlan:
    entity: EntitySpec
    entity_seed: int
    builder_version: str
    entity_spec_hash: str
    scene_spec_hash: str


@dataclass(frozen=True)
class ScenePlan:
    scene: SceneSpec
    entities: tuple[EntityBuildPlan, ...]


def plan_scene(spec: SceneSpec, registry: Any) -> ScenePlan:
    plans: list[EntityBuildPlan] = []
    for entity in sorted(spec.entities, key=lambda item: item.id):
        builder = registry.get(entity.kind)
        plans.append(
            EntityBuildPlan(
                entity=entity,
                entity_seed=derive_entity_seed(spec.seed, entity.id, entity.kind, builder.version),
                builder_version=builder.version,
                entity_spec_hash=entity_spec_hash(entity),
                scene_spec_hash=spec.spec_hash,
            )
        )
    return ScenePlan(spec, tuple(plans))


def plan_wall_cells(
    length: float,
    height: float,
    openings: Iterable[OpeningSpec],
) -> tuple[WallCellPlan, ...]:
    openings = tuple(openings)
    if length <= 0.0 or height <= 0.0:
        raise BuildError("Wall dimensions must be positive", code="PLAN.INVALID_WALL")
    x_cuts = sorted({0.0, length, *(value for item in openings for value in (item.left, item.right))})
    z_cuts = sorted({0.0, height, *(value for item in openings for value in (item.bottom, item.top))})
    cells: list[WallCellPlan] = []
    for x_index in range(len(x_cuts) - 1):
        x0, x1 = x_cuts[x_index], x_cuts[x_index + 1]
        if x1 <= x0:
            continue
        for z_index in range(len(z_cuts) - 1):
            z0, z1 = z_cuts[z_index], z_cuts[z_index + 1]
            if z1 <= z0:
                continue
            midpoint = ((x0 + x1) * 0.5, (z0 + z1) * 0.5)
            if any(
                item.left < midpoint[0] < item.right and item.bottom < midpoint[1] < item.top
                for item in openings
            ):
                continue
            cells.append(WallCellPlan(x0, x1, z0, z1))
    return _merge_wall_cells(cells)


def _merge_wall_cells(cells: Iterable[WallCellPlan]) -> tuple[WallCellPlan, ...]:
    horizontal: list[WallCellPlan] = []
    by_height: dict[tuple[float, float], list[WallCellPlan]] = {}
    for cell in cells:
        by_height.setdefault((cell.z0, cell.z1), []).append(cell)
    for key in sorted(by_height):
        row = sorted(by_height[key], key=lambda item: (item.x0, item.x1))
        current = row[0]
        for cell in row[1:]:
            if math.isclose(current.x1, cell.x0, rel_tol=0.0, abs_tol=1e-12):
                current = WallCellPlan(current.x0, cell.x1, current.z0, current.z1)
            else:
                horizontal.append(current)
                current = cell
        horizontal.append(current)

    vertical: list[WallCellPlan] = []
    by_width: dict[tuple[float, float], list[WallCellPlan]] = {}
    for cell in horizontal:
        by_width.setdefault((cell.x0, cell.x1), []).append(cell)
    for key in sorted(by_width):
        column = sorted(by_width[key], key=lambda item: (item.z0, item.z1))
        current = column[0]
        for cell in column[1:]:
            if math.isclose(current.z1, cell.z0, rel_tol=0.0, abs_tol=1e-12):
                current = WallCellPlan(current.x0, current.x1, current.z0, cell.z1)
            else:
                vertical.append(current)
                current = cell
        vertical.append(current)
    return tuple(sorted(vertical, key=lambda item: (item.z0, item.x0, item.z1, item.x1)))


def plan_stairs(params: StairsParams) -> StairPlan:
    riser_count = max(1, math.ceil(params.rise / params.max_riser))
    riser_height = params.rise / riser_count
    tread_depth = params.run / riser_count
    if tread_depth + 1e-12 < params.min_tread:
        raise SpecError(
            "Stair tread is below min_tread",
            code="SPEC.INFEASIBLE_STAIRS",
            context={"tread_depth": tread_depth, "min_tread": params.min_tread},
        )

    profile: list[tuple[float, float]] = [(0.0, 0.0), (params.run, 0.0), (params.run, params.rise)]
    for index in reversed(range(riser_count)):
        profile.append((index * tread_depth, (index + 1) * riser_height))
        if index > 0:
            profile.append((index * tread_depth, index * riser_height))
    return StairPlan(
        riser_count,
        riser_height,
        tread_depth,
        params.width,
        params.run,
        params.rise,
        tuple(profile),
    )

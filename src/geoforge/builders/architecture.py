from __future__ import annotations

import math
from dataclasses import replace
from typing import Iterable

from ..errors import BuildError
from ..geometry.primitives import box, rectangular_prism
from ..planning import EntityBuildPlan, WallCellPlan, plan_wall_cells
from ..spec import (
    BeamParams,
    BoxParams,
    CeilingParams,
    ColumnParams,
    FloorParams,
    OpeningSpec,
    RoomParams,
    WallParams,
)
from .base import BuildArtifact, BuildContext, BuildProduct, ContactExpectation, make_artifact, solid_contract


class _SimpleBuilder:
    version = "1.0.0"
    params_type: type

    def validate_params(self, entity_plan: EntityBuildPlan, context: BuildContext) -> None:
        if not isinstance(entity_plan.entity.params, self.params_type):
            raise BuildError(f"{self.kind} received the wrong parameter type", code="BUILD.PARAM_TYPE")


class BoxBuilder(_SimpleBuilder):
    kind = "box"
    params_type = BoxParams
    required_params = ("width", "depth", "height")
    optional_params = ()
    summary = "Axis-aligned rectangular solid in entity-local coordinates."

    def plan(self, entity_plan: EntityBuildPlan, context: BuildContext) -> EntityBuildPlan:
        self.validate_params(entity_plan, context)
        return entity_plan

    def build(self, plan: EntityBuildPlan, context: BuildContext) -> BuildProduct:
        params = plan.entity.params
        assert isinstance(params, BoxParams)
        draft = box(params.width, params.depth, params.height, name=f"{plan.entity.id}.body")
        return BuildProduct((make_artifact(plan, draft, solid_contract(draft, context.quality.min_feature_size), part="body"),))


class FloorBuilder(_SimpleBuilder):
    kind = "floor"
    params_type = FloorParams
    required_params = ("width", "length", "thickness")
    optional_params = ()
    summary = "Floor slab whose top face is the entity level datum."

    def plan(self, entity_plan: EntityBuildPlan, context: BuildContext) -> EntityBuildPlan:
        self.validate_params(entity_plan, context)
        return entity_plan

    def build(self, plan: EntityBuildPlan, context: BuildContext) -> BuildProduct:
        params = plan.entity.params
        assert isinstance(params, FloorParams)
        draft = rectangular_prism(
            (0.0, 0.0, -params.thickness),
            (params.width, params.length, 0.0),
            name=f"{plan.entity.id}.body",
        )
        return BuildProduct((make_artifact(plan, draft, solid_contract(draft, context.quality.min_feature_size), part="body"),))


class CeilingBuilder(_SimpleBuilder):
    kind = "ceiling"
    params_type = CeilingParams
    required_params = ("width", "length", "thickness")
    optional_params = ()
    summary = "Ceiling slab extending upward from the entity level datum."

    def plan(self, entity_plan: EntityBuildPlan, context: BuildContext) -> EntityBuildPlan:
        self.validate_params(entity_plan, context)
        return entity_plan

    def build(self, plan: EntityBuildPlan, context: BuildContext) -> BuildProduct:
        params = plan.entity.params
        assert isinstance(params, CeilingParams)
        draft = box(params.width, params.length, params.thickness, name=f"{plan.entity.id}.body")
        return BuildProduct((make_artifact(plan, draft, solid_contract(draft, context.quality.min_feature_size), part="body"),))


class BeamBuilder(_SimpleBuilder):
    kind = "beam"
    params_type = BeamParams
    required_params = ("length", "width", "height")
    optional_params = ()
    summary = "Straight rectangular beam aligned to local +X."

    def plan(self, entity_plan: EntityBuildPlan, context: BuildContext) -> EntityBuildPlan:
        self.validate_params(entity_plan, context)
        return entity_plan

    def build(self, plan: EntityBuildPlan, context: BuildContext) -> BuildProduct:
        params = plan.entity.params
        assert isinstance(params, BeamParams)
        draft = box(params.length, params.width, params.height, name=f"{plan.entity.id}.body")
        return BuildProduct((make_artifact(plan, draft, solid_contract(draft, context.quality.min_feature_size), part="body"),))


class ColumnBuilder(_SimpleBuilder):
    kind = "column"
    params_type = ColumnParams
    required_params = ("width", "depth", "height")
    optional_params = ()
    summary = "Straight rectangular column aligned to local +Z."

    def plan(self, entity_plan: EntityBuildPlan, context: BuildContext) -> EntityBuildPlan:
        self.validate_params(entity_plan, context)
        return entity_plan

    def build(self, plan: EntityBuildPlan, context: BuildContext) -> BuildProduct:
        params = plan.entity.params
        assert isinstance(params, ColumnParams)
        draft = box(params.width, params.depth, params.height, name=f"{plan.entity.id}.body")
        return BuildProduct((make_artifact(plan, draft, solid_contract(draft, context.quality.min_feature_size), part="body"),))


class WallBuilder(_SimpleBuilder):
    kind = "wall"
    params_type = WallParams
    required_params = ("length", "height", "thickness")
    optional_params = ("openings",)
    summary = "Straight wall; door/window openings use analytical solid splitting."

    def plan(self, entity_plan: EntityBuildPlan, context: BuildContext) -> tuple[EntityBuildPlan, tuple[WallCellPlan, ...]]:
        self.validate_params(entity_plan, context)
        params = entity_plan.entity.params
        assert isinstance(params, WallParams)
        return entity_plan, plan_wall_cells(params.length, params.height, params.openings)

    def build(
        self,
        plan: tuple[EntityBuildPlan, tuple[WallCellPlan, ...]],
        context: BuildContext,
    ) -> BuildProduct:
        entity_plan, cells = plan
        params = entity_plan.entity.params
        assert isinstance(params, WallParams)
        parts = _standalone_wall_parts(entity_plan, cells, params.thickness, context)
        return BuildProduct(tuple(artifact for artifact, _ in parts))


class RoomBuilder(_SimpleBuilder):
    kind = "room"
    params_type = RoomParams
    required_params = ("width", "length", "height", "wall_thickness", "floor_thickness")
    optional_params = ("ceiling", "ceiling_thickness", "size_mode", "openings")
    summary = "Rectangular CLEAR_INTERIOR room with coordinated floor, walls, ceiling, and openings."

    def plan(self, entity_plan: EntityBuildPlan, context: BuildContext) -> EntityBuildPlan:
        self.validate_params(entity_plan, context)
        return entity_plan

    def build(self, plan: EntityBuildPlan, context: BuildContext) -> BuildProduct:
        params = plan.entity.params
        assert isinstance(params, RoomParams)
        width, length, height, thickness = (
            params.width,
            params.length,
            params.height,
            params.wall_thickness,
        )
        artifacts: list[BuildArtifact] = []
        contacts: list[ContactExpectation] = []

        floor_draft = rectangular_prism(
            (-thickness, -thickness, -params.floor_thickness),
            (width + thickness, length + thickness, 0.0),
            name=f"{plan.entity.id}.floor",
        )
        floor = make_artifact(
            plan,
            floor_draft,
            solid_contract(floor_draft, context.quality.min_feature_size),
            part="floor",
        )
        artifacts.append(floor)

        ceiling: BuildArtifact | None = None
        if params.ceiling:
            ceiling_draft = rectangular_prism(
                (-thickness, -thickness, height),
                (width + thickness, length + thickness, height + params.ceiling_thickness),
                name=f"{plan.entity.id}.ceiling",
            )
            ceiling = make_artifact(
                plan,
                ceiling_draft,
                solid_contract(ceiling_draft, context.quality.min_feature_size),
                part="ceiling",
            )
            artifacts.append(ceiling)

        by_wall = {
            wall: tuple(opening for opening in params.openings if opening.wall == wall)
            for wall in ("south", "north", "west", "east")
        }
        horizontal_openings = {
            wall: tuple(replace(item, offset=item.offset + thickness) for item in by_wall[wall])
            for wall in ("south", "north")
        }

        wall_specs = (
            ("south", width + 2.0 * thickness, horizontal_openings["south"]),
            ("north", width + 2.0 * thickness, horizontal_openings["north"]),
            ("west", length, by_wall["west"]),
            ("east", length, by_wall["east"]),
        )
        for wall_name, wall_length, openings in wall_specs:
            cells = plan_wall_cells(wall_length, height, openings)
            parts = _room_wall_parts(plan, wall_name, cells, params, context)
            artifacts.extend(artifact for artifact, _ in parts)
            for artifact, cell in parts:
                if math.isclose(cell.z0, 0.0, abs_tol=1e-12):
                    contacts.append(ContactExpectation(floor.artifact_id, artifact.artifact_id, context.quality.min_feature_size * 1e-4))
                if ceiling is not None and math.isclose(cell.z1, height, abs_tol=1e-12):
                    contacts.append(ContactExpectation(ceiling.artifact_id, artifact.artifact_id, context.quality.min_feature_size * 1e-4))

        return BuildProduct(tuple(artifacts), tuple(contacts))


def _standalone_wall_parts(
    plan: EntityBuildPlan,
    cells: Iterable[WallCellPlan],
    thickness: float,
    context: BuildContext,
) -> list[tuple[BuildArtifact, WallCellPlan]]:
    result: list[tuple[BuildArtifact, WallCellPlan]] = []
    for index, cell in enumerate(cells):
        draft = rectangular_prism(
            (cell.x0, 0.0, cell.z0),
            (cell.x1, thickness, cell.z1),
            name=f"{plan.entity.id}.cell.{index:03d}",
        )
        artifact = make_artifact(
            plan,
            draft,
            solid_contract(draft, context.quality.min_feature_size),
            part=f"cell.{index:03d}",
        )
        result.append((artifact, cell))
    return result


def _room_wall_parts(
    plan: EntityBuildPlan,
    wall_name: str,
    cells: Iterable[WallCellPlan],
    params: RoomParams,
    context: BuildContext,
) -> list[tuple[BuildArtifact, WallCellPlan]]:
    result: list[tuple[BuildArtifact, WallCellPlan]] = []
    t = params.wall_thickness
    for index, cell in enumerate(cells):
        if wall_name == "south":
            minimum = (cell.x0 - t, -t, cell.z0)
            maximum = (cell.x1 - t, 0.0, cell.z1)
        elif wall_name == "north":
            minimum = (cell.x0 - t, params.length, cell.z0)
            maximum = (cell.x1 - t, params.length + t, cell.z1)
        elif wall_name == "west":
            minimum = (-t, cell.x0, cell.z0)
            maximum = (0.0, cell.x1, cell.z1)
        else:
            minimum = (params.width, cell.x0, cell.z0)
            maximum = (params.width + t, cell.x1, cell.z1)
        part = f"wall.{wall_name}.{index:03d}"
        draft = rectangular_prism(minimum, maximum, name=f"{plan.entity.id}.{part}")
        artifact = make_artifact(
            plan,
            draft,
            solid_contract(draft, context.quality.min_feature_size),
            part=part,
        )
        result.append((artifact, cell))
    return result

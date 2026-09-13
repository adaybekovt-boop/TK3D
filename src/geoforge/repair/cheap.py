from __future__ import annotations

from dataclasses import dataclass

import bmesh
import bpy

from ..geometry.model import Bounds3, GeometryContract


@dataclass
class RepairAttempt:
    obj: bpy.types.Object
    original_mesh: bpy.types.Mesh
    candidate_mesh: bpy.types.Mesh
    before_bounds: Bounds3
    active: bool = True

    def within_budget(self, contract: GeometryContract) -> bool:
        if not self.candidate_mesh.vertices:
            return False
        after = _mesh_bounds(self.candidate_mesh)
        limits = contract.repair_limits
        if limits is None:
            return False
        bound_delta = max(
            *(
                abs(after.minimum[axis] - self.before_bounds.minimum[axis])
                for axis in range(3)
            ),
            *(
                abs(after.maximum[axis] - self.before_bounds.maximum[axis])
                for axis in range(3)
            ),
        )
        dimension_delta = max(
            abs(after.dimensions[axis] - self.before_bounds.dimensions[axis])
            for axis in range(3)
        )
        return bound_delta <= limits.max_bounds_delta and dimension_delta <= limits.max_dimension_delta

    def commit(self) -> None:
        if not self.active:
            return
        if self.original_mesh.users == 0:
            bpy.data.meshes.remove(self.original_mesh)
        self.active = False

    def rollback(self) -> None:
        if not self.active:
            return
        self.obj.data = self.original_mesh
        if self.candidate_mesh.users == 0:
            bpy.data.meshes.remove(self.candidate_mesh)
        self.active = False


def begin_tier1_repair(obj: bpy.types.Object, contract: GeometryContract) -> RepairAttempt:
    limits = contract.repair_limits
    if limits is None:
        raise ValueError("geometry contract does not allow repair")
    original = obj.data
    before = _mesh_bounds(original)
    candidate = original.copy()
    candidate.name = f"{original.name}__Tier1"
    obj.data = candidate
    attempt = RepairAttempt(obj, original, candidate, before)
    bm = bmesh.new()
    try:
        bm.from_mesh(candidate)
        wire_edges = [edge for edge in bm.edges if edge.is_wire]
        if wire_edges:
            bmesh.ops.delete(bm, geom=wire_edges, context="EDGES")
        loose_vertices = [vert for vert in bm.verts if not vert.link_edges and not vert.link_faces]
        if loose_vertices:
            bmesh.ops.delete(bm, geom=loose_vertices, context="VERTS")
        if bm.edges:
            bmesh.ops.dissolve_degenerate(
                bm,
                edges=list(bm.edges),
                dist=limits.weld_distance,
            )
        if limits.allow_weld and bm.verts:
            # Never weld across disconnected shells. Coincident components may
            # be intentional and merging them silently changes topology.
            for component in _vertex_components(bm):
                bmesh.ops.remove_doubles(
                    bm,
                    verts=component,
                    dist=limits.weld_distance,
                )
        loose_vertices = [vert for vert in bm.verts if not vert.link_edges and not vert.link_faces]
        if loose_vertices:
            bmesh.ops.delete(bm, geom=loose_vertices, context="VERTS")
        if bm.faces:
            bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(candidate)
        candidate.update(calc_edges=True, calc_edges_loose=True)
    except Exception:
        attempt.rollback()
        raise
    finally:
        bm.free()
    return attempt


def _mesh_bounds(mesh: bpy.types.Mesh) -> Bounds3:
    if not mesh.vertices:
        raise ValueError("cannot calculate bounds for an empty mesh")
    vertices = [tuple(float(value) for value in vertex.co) for vertex in mesh.vertices]
    return Bounds3.from_vertices(vertices)


def _vertex_components(bm: bmesh.types.BMesh) -> list[list[bmesh.types.BMVert]]:
    unseen = set(bm.verts)
    result: list[list[bmesh.types.BMVert]] = []
    while unseen:
        start = unseen.pop()
        component = [start]
        queue = [start]
        while queue:
            current = queue.pop()
            for edge in current.link_edges:
                other = edge.other_vert(current)
                if other in unseen:
                    unseen.remove(other)
                    component.append(other)
                    queue.append(other)
        result.append(component)
    return result

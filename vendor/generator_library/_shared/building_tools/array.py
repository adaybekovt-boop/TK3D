import bpy
import bmesh
from bpy.props import IntProperty, FloatProperty

from ..utils import (
    clamp,
    VEC_DOWN,
    sort_edges,
    sort_faces,
    get_scaled_unit,
    edge_is_vertical,
    calc_edge_median,
    calc_faces_median,
    calc_face_dimensions,
)

from mathutils import Vector


class ArrayProperty(bpy.types.PropertyGroup):
    count: IntProperty(
        name="Count",
        min=1,
        max=100,
        default=1,
        description="Number of elements",
    )

    spread: FloatProperty(
        name="Spread",
        min=get_scaled_unit(-1.0),
        max=get_scaled_unit(1.0),
        default=get_scaled_unit(0.0),
        description="Relative distance between elements",
    )

    def draw(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, "count")
        rl = col.row(align=True)
        rl.enabled = self.count > 1
        rl.prop(self, "spread", slider=True)


class ArrayGetSet:
    @property
    def count(self):
        return self.array.count

    @count.setter
    def count(self, val):
        self.array.count = val

    @property
    def spread(self):
        return self.array.spread

    @spread.setter
    def spread(self, val):
        self.array.spread = val


def clamp_array_count(face, prop):
    prop.count = clamp(prop.count, 1, int(calc_face_dimensions(face)[0] // prop.width))


def get_array_split_edges(afaces):
    result = []
    edges = list({e for f in afaces for e in f.edges})
    for e in edges:
        if len(e.link_faces) != 2:
            continue
        if all(f in afaces for f in e.link_faces):
            result.append(e)
    return result


def spread_array(bm, split_edges, split_faces, max_width, prop):
    if prop.count == 1:
        return

    normal = split_faces[0].normal.copy()
    median = calc_faces_median(split_faces)
    right = normal.cross(VEC_DOWN)
    split_edges = sort_edges(split_edges, right)
    split_faces = sort_faces(split_faces, right)

    edge_neighbour_face_map = {
        edge: [split_faces[idx], split_faces[idx + 1]]
        for idx, edge in enumerate(split_edges)
    }

    def get_all_splitface_verts(f):
        corner_verts = list(f.verts)
        split_verts = []
        for v in corner_verts:
            split_edge = [e for e in v.link_edges if e not in f.edges].pop()
            if edge_is_vertical(split_edge):
                split_verts.append(split_edge.other_vert(v))
        return corner_verts + split_verts

    prop.spread = clamp(prop.spread, -1, 0.9999)

    for f in split_faces:
        fm = f.calc_center_median()
        vts = get_all_splitface_verts(f)
        diff = Vector((fm - median).to_tuple(3))
        spread_factor = (max_width - prop.width) * (diff.length / max_width)
        if prop.spread > 0:
            spread_factor /= prop.count - 1
        bmesh.ops.translate(
            bm, verts=vts, vec=diff.normalized() * prop.spread * spread_factor
        )

    for edge in split_edges:
        neighbours = edge_neighbour_face_map[edge]
        nmedian = calc_faces_median(neighbours)
        diff = nmedian - calc_edge_median(edge)
        diff.z = 0
        bmesh.ops.translate(bm, verts=edge.verts, vec=diff)

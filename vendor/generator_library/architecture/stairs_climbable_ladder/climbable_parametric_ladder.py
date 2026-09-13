"""Minimal parametric ladder — a working demonstration of the kit's core rules.

Demonstrates:
  * parameter dictionary (single layout source, doc 01)
  * named datums + closed-form placement, no chain references (docs 01/02)
  * part/assembly separation: one rung mesh, N instances (doc 01)
  * mating part in the parent's frame: feet inherit the rail lean,
    only the sole is cut by the world-horizontal floor plane (doc 06)
  * explicit terminal conditions: rungs end short of rail inner faces
    with a declared clearance (doc 06)

Run headless:
    blender --background --python example_parametric_ladder.py
Output:
    output/ladder_example.blend
"""
import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

PARAMS = {
    "H_TOP": 3.000,
    "LEAN_DEG": 13.8,
    "RAIL_GAP": 0.400,
    "RAIL_W": 0.076,
    "RAIL_D": 0.030,
    "RUNG_PITCH": 0.280,
    "RUNG_R": 0.015,
    "RUNG_SEGS": 12,
    "Z0": 0.300,
    "RUNG_CLEAR": 0.0005,
    "FOOT_LEN": 0.090,
    "FOOT_CLEAR": 0.0005,
}

FLOOR_Z = 0.0
CENTER_X = 0.0
THETA = math.radians(PARAMS["LEAN_DEG"])
RAIL_AXIS = Vector((0.0, math.sin(THETA), math.cos(THETA)))
RAIL_X = PARAMS["RAIL_GAP"] / 2 + PARAMS["RAIL_W"] / 2


def rail_matrix(sign):
    rot = Matrix.Rotation(-THETA, 4, "X")
    loc = Matrix.Translation((sign * RAIL_X, 0.0, FLOOR_Z))
    return loc @ rot


def _box_mesh(name, w, d, h, z0=0.0):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(w, d, h), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(0, 0, z0 + h / 2), verts=bm.verts)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def build():
    scene = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

    col = bpy.data.collections.get("Ladder") or bpy.data.collections.new("Ladder")
    if col.name not in {c.name for c in scene.collection.children}:
        scene.collection.children.link(col)

    p = PARAMS
    rail_len = p["H_TOP"] / math.cos(THETA)

    rail_mesh = _box_mesh("rail", p["RAIL_W"], p["RAIL_D"], rail_len)
    for sign, tag in ((-1, "L"), (1, "R")):
        ob = bpy.data.objects.new(f"rail_{tag}", rail_mesh)
        ob.matrix_world = rail_matrix(sign)
        col.objects.link(ob)

    rung_len = p["RAIL_GAP"] - 2 * p["RUNG_CLEAR"]
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm, cap_ends=True, segments=p["RUNG_SEGS"],
        radius1=p["RUNG_R"], radius2=p["RUNG_R"], depth=rung_len,
    )
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"), verts=bm.verts)
    rung_mesh = bpy.data.meshes.new("rung")
    bm.to_mesh(rung_mesh)
    bm.free()

    n_rungs = int((p["H_TOP"] - p["Z0"]) // p["RUNG_PITCH"]) + 1
    for i in range(n_rungs):
        z_i = p["Z0"] + i * p["RUNG_PITCH"]
        y_i = z_i * math.tan(THETA)
        ob = bpy.data.objects.new(f"rung_{i:02d}", rung_mesh)
        ob.matrix_world = Matrix.Translation((CENTER_X, y_i, z_i))
        col.objects.link(ob)

    foot_w = p["RAIL_W"] + 0.008
    foot_d = p["RAIL_D"] + 0.008
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(foot_w, foot_d, p["FOOT_LEN"]), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(0, 0, -p["FOOT_LEN"] / 2 - p["FOOT_CLEAR"]), verts=bm.verts)
    foot_mesh_local = bpy.data.meshes.new("foot_uncut")
    bm.to_mesh(foot_mesh_local)
    bm.free()

    for sign, tag in ((-1, "L"), (1, "R")):
        m = rail_matrix(sign)
        bm = bmesh.new()
        bm.from_mesh(foot_mesh_local)
        bm.transform(m)
        sole_z = FLOOR_Z - 0.5 * p["FOOT_LEN"] * math.cos(THETA)
        res = bmesh.ops.bisect_plane(
            bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
            plane_co=(0, 0, sole_z), plane_no=(0, 0, -1.0),
            clear_outer=True, use_snap_center=False,
        )
        bmesh.ops.holes_fill(bm, edges=[e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)])
        mesh = bpy.data.meshes.new(f"foot_{tag}")
        bm.to_mesh(mesh)
        bm.free()
        ob = bpy.data.objects.new(f"foot_{tag}", mesh)
        col.objects.link(ob)

    bpy.data.meshes.remove(foot_mesh_local)
    bom = {"rail": 2, "rung": n_rungs, "foot": 2}
    scene["bom_json"] = repr(bom)
    return bom


if __name__ == "__main__":
    bom = build()
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.abspath(os.path.join(out_dir, "ladder_example.blend"))
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print(f"[ladder] BOM: {bom}")
    print(f"[ladder] saved: {path}")

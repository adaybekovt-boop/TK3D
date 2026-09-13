"""Утилиты для генерации стульев."""

import bpy
import bmesh
import math

from common.shared_geometry import create_box, create_cylinder
from common.shared_materials import get_or_create_mat, setup_principled

def create_prism(name, sx, sy, sz, cx=0, cy=0, cz=0, diff=0.2):
    bm = bmesh.new()
    verts = []
    print(f"diff: {diff}")
    for dx in (-sx, sx):
        for dy in (-sy, sy):
            if dy == -sy: x_diff = dx * diff
            else: x_diff = 0
            for dz in (-sz, sz):
                verts.append(bm.verts.new((cx + dx - x_diff, cy + dy, cz + dz)))
    faces = [
        (0, 1, 3, 2), (4, 6, 7, 5),
        (0, 4, 5, 1), (2, 3, 7, 6),
        (0, 2, 6, 4), (1, 5, 7, 3),
    ]
    for f in faces:
        bm.faces.new([verts[i] for i in f])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return bpy.data.objects.new(name, mesh)


def create_disk(name, radius, thickness, z_offset=0, segments=24):
    return create_cylinder(name, radius, thickness, z_offset, segments)


# ============================================================
# Материалы
# ============================================================

WOOD_STYLES = [
    ("LightOak", (0.55, 0.4, 0.22, 1.0), 0.5),
    ("Birch", (0.7, 0.6, 0.45, 1.0), 0.45),
    ("DarkWalnut", (0.25, 0.15, 0.08, 1.0), 0.45),
    ("WhitePaint", (0.92, 0.91, 0.88, 1.0), 0.35),
    ("Pine", (0.65, 0.5, 0.3, 1.0), 0.5),
]

METAL_STYLES = [
    ("BlackMetal", (0.08, 0.08, 0.08, 1.0), 0.4),
    ("Chrome", (0.7, 0.7, 0.72, 1.0), 0.15),
]

FABRIC_STYLES = [
    ("DarkBlue", (0.18, 0.22, 0.35, 1.0), 0.85),
    ("Gray", (0.45, 0.45, 0.45, 1.0), 0.8),
    ("Beige", (0.65, 0.58, 0.45, 1.0), 0.8),
    ("DarkGreen", (0.15, 0.28, 0.18, 1.0), 0.85),
    ("Brown", (0.35, 0.22, 0.12, 1.0), 0.75),
]


def mat_wood(rng):
    name, color, roughness = rng.choice(WOOD_STYLES)
    return setup_principled(get_or_create_mat(f"M_Chair_{name}"), color, roughness=roughness)


def mat_metal(rng):
    name, color, roughness = rng.choice(METAL_STYLES)
    return setup_principled(get_or_create_mat(f"M_ChairMetal_{name}"),
                              color, roughness=roughness, metallic=1.0, specular=0.8)


def mat_fabric(rng):
    name, color, roughness = rng.choice(FABRIC_STYLES)
    mat = setup_principled(get_or_create_mat(f"M_ChairFabric_{name}"),
                             color, roughness=roughness)
    # Добавляем sheen для ткани
    bsdf = [n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    bsdf.inputs['Sheen Weight'].default_value = 0.3
    return mat

"""Утилиты для генерации свечей и подсвечников."""

import bpy
import bmesh
import math
import os
import sys

_generators_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if _generators_dir not in sys.path:
    sys.path.insert(0, _generators_dir)

from common.shared_geometry import create_box, create_cylinder
from common.shared_materials import get_or_create_mat, setup_principled, clear_and_get_output


# ============================================================
# Цвета
# ============================================================

WAX_COLORS = [
    ("White", (0.92, 0.9, 0.85, 1.0)),
    ("Cream", (0.9, 0.85, 0.7, 1.0)),
    ("Ivory", (0.95, 0.92, 0.82, 1.0)),
    ("Red", (0.6, 0.1, 0.08, 1.0)),
    ("Burgundy", (0.4, 0.08, 0.08, 1.0)),
    ("Black", (0.05, 0.05, 0.05, 1.0)),
    ("Green", (0.15, 0.3, 0.15, 1.0)),
    ("Blue", (0.15, 0.2, 0.35, 1.0)),
]

HOLDER_METAL_COLORS = [
    ("Brass", (0.7, 0.55, 0.25, 1.0), 0.3),
    ("Chrome", (0.7, 0.7, 0.72, 1.0), 0.15),
    ("BlackMetal", (0.08, 0.08, 0.08, 1.0), 0.4),
    ("Copper", (0.72, 0.45, 0.3, 1.0), 0.3),
    ("Gold", (0.8, 0.65, 0.25, 1.0), 0.25),
]

TRAY_COLORS = [
    ("Wood", (0.4, 0.25, 0.12, 1.0)),
    ("White", (0.9, 0.88, 0.85, 1.0)),
    ("Black", (0.08, 0.08, 0.08, 1.0)),
    ("Marble", (0.85, 0.83, 0.8, 1.0)),
]


# ============================================================
# Материалы
# ============================================================

def mat_wax(rng):
    name, color = rng.choice(WAX_COLORS)
    mat = get_or_create_mat(f"M_Wax_{name}")
    return setup_principled(mat, color, roughness=0.7, specular=0.1,
                            transmission=0.15, alpha=0.95)


def mat_wick():
    mat = get_or_create_mat("M_Wick")
    return setup_principled(mat, (0.1, 0.08, 0.05, 1.0), roughness=0.9, specular=0.02)


def mat_holder_metal(rng):
    name, color, roughness = rng.choice(HOLDER_METAL_COLORS)
    mat = get_or_create_mat(f"M_Holder_{name}")
    return setup_principled(mat, color, roughness=roughness, specular=0.8, metallic=1.0)


def mat_tray(rng):
    name, color = rng.choice(TRAY_COLORS)
    mat = get_or_create_mat(f"M_Tray_{name}")
    return setup_principled(mat, color, roughness=0.6, specular=0.2)


def mat_flame():
    """Эмиссионный материал для пламени."""
    mat = get_or_create_mat("M_Flame")
    tree = mat.node_tree
    output = clear_and_get_output(tree)
    output.location = (500, 0)

    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (200, 0)
    bsdf.inputs['Base Color'].default_value = (1.0, 0.7, 0.2, 1.0)
    bsdf.inputs['Emission Color'].default_value = (1.0, 0.6, 0.1, 1.0)
    bsdf.inputs['Emission Strength'].default_value = 5.0
    bsdf.inputs['Alpha'].default_value = 0.8
    tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat


# ============================================================
# Геометрия
# ============================================================

def create_candle_body(name, radius, height, rng, z_offset=0):
    """Тело свечи — цилиндр + фитиль + опц. пламя."""
    objects = []

    body = create_cylinder(name, radius, height, z_offset=z_offset, segments=16)
    # Убираем сглаживание с верхней и нижней крышек
    mesh = body.data
    for poly in mesh.polygons:
        # Крышки — это полигоны, у которых все вершины на одной высоте
        zs = [mesh.vertices[v].co.z for v in poly.vertices]
        if max(zs) - min(zs) < 0.0001:
            poly.use_smooth = False
    body.data.materials.append(mat_wax(rng))
    objects.append(body)

    # Фитиль
    wick_r = 0.001
    wick_h = 0.008
    wick = create_cylinder(f"{name}_Wick", wick_r, wick_h,
                           z_offset=z_offset + height, segments=6, smooth=False)
    wick.data.materials.append(mat_wick())
    objects.append(wick)

    # Пламя (маленький конус/ромб)
    if rng.random() < 0.6:  # 60% свечей горят
        flame_h = rng.uniform(0.02, 0.04)
        flame_r = rng.uniform(0.003, 0.005)
        bm = bmesh.new()
        # Простой ромб
        top = bm.verts.new((0, 0, flame_h))
        mid_ring = []
        for i in range(8):
            angle = 2 * math.pi * i / 8
            mid_ring.append(bm.verts.new((
                flame_r * math.cos(angle),
                flame_r * math.sin(angle),
                flame_h * 0.35,
            )))
        bottom = bm.verts.new((0, 0, 0))
        for i in range(8):
            j = (i + 1) % 8
            bm.faces.new([top, mid_ring[i], mid_ring[j]])
            bm.faces.new([bottom, mid_ring[j], mid_ring[i]])

        mesh = bpy.data.meshes.new(f"{name}_Flame")
        bm.to_mesh(mesh)
        bm.free()
        for p in mesh.polygons:
            p.use_smooth = True
        mesh.update()
        flame = bpy.data.objects.new(f"{name}_Flame", mesh)
        flame.location = (0, 0, z_offset + height + wick_h - flame_h*.1)
        flame.data.materials.append(mat_flame())
        sub = flame.modifiers.new('Sub','SUBSURF')
        sub.levels = 2
        objects.append(flame)

    return objects

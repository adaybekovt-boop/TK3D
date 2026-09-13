"""Процедурная генерация ваз через тело вращения."""

import bpy
import bmesh
import math
import random

from plates import _interpolate_profile, create_ceramic_material

SPIN_SEGMENTS = 48
PROFILE_SEGMENTS = 16


# ============================================================
# Профили ваз
# ============================================================

def _classic_vase_profile(rng, radius, height, thickness):
    """Классическая ваза: узкое основание, широкая середина, сужение к горлышку."""
    base_r = radius * rng.uniform(0.3, 0.45)
    belly_r = radius
    belly_h = height * rng.uniform(0.35, 0.5)
    neck_r = radius * rng.uniform(0.25, 0.4)
    neck_h = height * rng.uniform(0.75, 0.85)
    lip_r = neck_r * rng.uniform(1.0, 1.3)

    inner = [
        (0, thickness),
        (base_r - thickness, thickness),
        (belly_r - thickness, belly_h),
        (neck_r - thickness, neck_h),
        (lip_r - thickness, height),
    ]
    outer = [
        (0, 0),
        (base_r, 0),
        (belly_r, belly_h),
        (neck_r, neck_h),
        (lip_r, height),
    ]
    return inner, outer


def _cylinder_vase_profile(rng, radius, height, thickness):
    """Цилиндрическая ваза: почти прямые стенки."""
    base_r = radius * rng.uniform(0.85, 0.95)
    mid_r = radius * rng.uniform(0.95, 1.05)
    top_r = radius * rng.uniform(0.9, 1.05)
    lip_flare = rng.uniform(0, 0.01)

    inner = [
        (0, thickness),
        (base_r - thickness, thickness),
        (mid_r - thickness, height * 0.5),
        (top_r - thickness, height * 0.92),
        (top_r - thickness + lip_flare, height),
    ]
    outer = [
        (0, 0),
        (base_r, 0),
        (mid_r, height * 0.5),
        (top_r, height * 0.92),
        (top_r + lip_flare, height),
    ]
    return inner, outer


def _bottle_vase_profile(rng, radius, height, thickness):
    """Бутылочная ваза: широкое тело, узкое горлышко."""
    base_r = radius * rng.uniform(0.4, 0.55)
    belly_r = radius
    belly_h = height * rng.uniform(0.25, 0.4)
    shoulder_h = height * rng.uniform(0.5, 0.6)
    neck_r = radius * rng.uniform(0.18, 0.28)
    lip_r = neck_r * rng.uniform(1.05, 1.25)

    inner = [
        (0, thickness),
        (base_r - thickness, thickness),
        (belly_r - thickness, belly_h),
        (belly_r * 0.7 - thickness, shoulder_h),
        (neck_r - thickness, height * 0.8),
        (lip_r - thickness, height),
    ]
    outer = [
        (0, 0),
        (base_r, 0),
        (belly_r, belly_h),
        (belly_r * 0.7, shoulder_h),
        (neck_r, height * 0.8),
        (lip_r, height),
    ]
    return inner, outer


# ============================================================
# Материалы
# ============================================================

VASE_COLORS = [
    ("White", (0.93, 0.91, 0.88, 1.0), 0.3),
    ("DarkBlue", (0.12, 0.18, 0.35, 1.0), 0.2),
    ("Olive", (0.35, 0.38, 0.25, 1.0), 0.3),
    ("Terracotta", (0.7, 0.4, 0.25, 1.0), 0.5),
    ("Black", (0.05, 0.05, 0.06, 1.0), 0.15),
    ("Sage", (0.6, 0.65, 0.55, 1.0), 0.35),
]


# ============================================================
# Генерация
# ============================================================

def _create_spin_object(name, profile_inner, profile_outer):
    """Создаёт тело вращения (общая функция для всех lathe-объектов)."""
    bm = bmesh.new()

    inner = _interpolate_profile(profile_inner, PROFILE_SEGMENTS)
    outer = _interpolate_profile(profile_outer, PROFILE_SEGMENTS)
    outer_rev = list(reversed(outer))
    profile = inner + outer_rev

    profile_verts = []
    for r, z in profile:
        profile_verts.append(bm.verts.new((max(0, r), 0, z)))

    for i in range(len(profile_verts) - 1):
        bm.edges.new((profile_verts[i], profile_verts[i + 1]))
    bm.edges.new((profile_verts[-1], profile_verts[0]))

    bmesh.ops.spin(
        bm,
        geom=bm.edges[:] + bm.verts[:],
        cent=(0, 0, 0),
        axis=(0, 0, 1),
        angle=math.pi * 2,
        steps=SPIN_SEGMENTS,
        use_duplicate=False,
    )

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    for poly in mesh.polygons:
        poly.use_smooth = True
    mesh.update()

    return bpy.data.objects.new(name, mesh)


VASE_TYPES = {
    'classic': {
        'profile_fn': _classic_vase_profile,
        'radius': (0.06, 0.10),
        'height': (0.18, 0.30),
        'thickness': (0.004, 0.007),
    },
    'cylinder': {
        'profile_fn': _cylinder_vase_profile,
        'radius': (0.04, 0.07),
        'height': (0.15, 0.25),
        'thickness': (0.003, 0.006),
    },
    'bottle': {
        'profile_fn': _bottle_vase_profile,
        'radius': (0.07, 0.12),
        'height': (0.20, 0.35),
        'thickness': (0.004, 0.007),
    },
}


def generate_vase(seed, vase_type='classic', color_idx=None):
    """Генерирует одну вазу."""
    rng = random.Random(seed)
    spec = VASE_TYPES[vase_type]

    radius = rng.uniform(*spec['radius'])
    height = rng.uniform(*spec['height'])
    thickness = rng.uniform(*spec['thickness'])

    inner, outer = spec['profile_fn'](rng, radius, height, thickness)
    name = f"Vase_{vase_type}_{seed}"
    obj = _create_spin_object(name, inner, outer)

    if color_idx is None:
        color_idx = rng.randint(0, len(VASE_COLORS) - 1)
    color_name, color, roughness = VASE_COLORS[color_idx]
    mat = create_ceramic_material(f"M_Vase_{color_name}", color, roughness)
    obj.data.materials.append(mat)

    return obj

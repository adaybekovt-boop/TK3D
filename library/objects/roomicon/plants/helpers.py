"""Утилиты для генерации растений: горшки, материалы."""

import bpy
import bmesh
import math
import os
import sys

_generators_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if _generators_dir not in sys.path:
    sys.path.insert(0, _generators_dir)

from common.shared_geometry import create_box, create_cylinder
from common.shared_materials import get_or_create_mat, setup_principled


# ============================================================
# Цвета
# ============================================================

POT_COLORS = [
    ("Terracotta", (0.65, 0.35, 0.2, 1.0)),
    ("White", (0.92, 0.91, 0.88, 1.0)),
    ("Gray", (0.5, 0.5, 0.5, 1.0)),
    ("DarkGray", (0.25, 0.25, 0.25, 1.0)),
    ("Cream", (0.85, 0.8, 0.7, 1.0)),
    ("Black", (0.08, 0.08, 0.08, 1.0)),
    ("Navy", (0.12, 0.15, 0.25, 1.0)),
    ("Olive", (0.3, 0.35, 0.2, 1.0)),
]

GREEN_COLORS = [
    (0.15, 0.4, 0.12, 1.0),   # зелёный
    (0.2, 0.45, 0.15, 1.0),   # светло-зелёный
    (0.1, 0.3, 0.1, 1.0),     # тёмно-зелёный
    (0.25, 0.5, 0.2, 1.0),    # ярко-зелёный
    (0.18, 0.35, 0.18, 1.0),  # серо-зелёный
    (0.3, 0.5, 0.15, 1.0),    # желто-зелёный
]

CACTUS_COLORS = [
    (0.15, 0.35, 0.12, 1.0),
    (0.2, 0.4, 0.15, 1.0),
    (0.12, 0.28, 0.1, 1.0),
]


# ============================================================
# Материалы
# ============================================================

def mat_pot(rng):
    name, color = rng.choice(POT_COLORS)
    mat = get_or_create_mat(f"M_Pot_{name}")
    return setup_principled(mat, color, roughness=0.7, specular=0.2)


def mat_soil():
    mat = get_or_create_mat("M_Soil")
    return setup_principled(mat, (0.15, 0.1, 0.06, 1.0), roughness=0.95, specular=0.02)


def mat_leaf(rng, color=None):
    if color is None:
        color = rng.choice(GREEN_COLORS)
    mat = get_or_create_mat(f"M_Leaf_{id(color)}")
    return setup_principled(mat, color, roughness=0.6, specular=0.15)


def mat_cactus(rng):
    color = rng.choice(CACTUS_COLORS)
    mat = get_or_create_mat(f"M_Cactus_{id(color)}")
    return setup_principled(mat, color, roughness=0.65, specular=0.1)


def mat_trunk():
    mat = get_or_create_mat("M_Trunk")
    return setup_principled(mat, (0.3, 0.2, 0.1, 1.0), roughness=0.8, specular=0.05)


# ============================================================
# Горшки
# ============================================================

def _hollow_round_pot(name, segments, height, wall,
                      r_out_bot, r_out_top, r_in_bot, r_in_top):
    """Полый горшок (тело вращения) с дном и стенками.

    Возвращает bpy.types.Object.
    """
    bm = bmesh.new()
    bot_out, bot_in = [], []
    top_out, top_in = [], []
    bot_z = wall  # дно приподнято на толщину стенки

    for i in range(segments):
        angle = 2 * math.pi * i / segments
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        bot_out.append(bm.verts.new((r_out_bot * cos_a, r_out_bot * sin_a, 0)))
        bot_in.append(bm.verts.new((r_in_bot * cos_a, r_in_bot * sin_a, bot_z)))
        top_out.append(bm.verts.new((r_out_top * cos_a, r_out_top * sin_a, height)))
        top_in.append(bm.verts.new((r_in_top * cos_a, r_in_top * sin_a, height)))

    for i in range(segments):
        j = (i + 1) % segments
        # Внешняя стенка
        bm.faces.new([bot_out[i], bot_out[j], top_out[j], top_out[i]])
        # Внутренняя стенка
        bm.faces.new([bot_in[i], top_in[i], top_in[j], bot_in[j]])
        # Верхний обод (между внешней и внутренней кромкой)
        bm.faces.new([top_out[i], top_out[j], top_in[j], top_in[i]])
        # Дно (между внешним низом и внутренним низом)
        bm.faces.new([bot_out[i], bot_in[i], bot_in[j], bot_out[j]])

    # Внешнее дно
    bm.faces.new(bot_out[::-1])
    # Внутреннее дно
    bm.faces.new(bot_in)

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.update()
    return bpy.data.objects.new(name, mesh)


def create_pot_cylinder(name, radius, height, rng):
    """Цилиндрический горшок с землёй."""
    wall = rng.uniform(0.003, 0.005)
    r_in = radius - wall

    pot = _hollow_round_pot(name, 24, height, wall,
                            r_out_bot=radius, r_out_top=radius,
                            r_in_bot=r_in, r_in_top=r_in)
    pot.data.materials.append(mat_pot(rng))

    # Земля внутри горшка
    soil_z = height * rng.uniform(0.7, 0.85)
    soil = create_cylinder(f"{name}_Soil", r_in * 0.97, 0.004,
                           z_offset=soil_z, segments=24)
    soil.data.materials.append(mat_soil())

    return [pot, soil], soil_z


def create_pot_tapered(name, radius_top, radius_bottom, height, rng):
    """Конусный горшок (усечённый конус) с полостью."""
    wall = rng.uniform(0.003, 0.005)

    pot = _hollow_round_pot(name, 24, height, wall,
                            r_out_bot=radius_bottom, r_out_top=radius_top,
                            r_in_bot=radius_bottom - wall,
                            r_in_top=radius_top - wall)
    pot.data.materials.append(mat_pot(rng))

    soil_z = height * rng.uniform(0.7, 0.85)
    r_soil = (radius_top - radius_bottom ) * (soil_z/height) + radius_bottom - wall
    soil = create_cylinder(f"{name}_Soil", r_soil, 0.004,
                           z_offset=soil_z, segments=24)
    soil.data.materials.append(mat_soil())

    return [pot, soil], soil_z


def create_pot_cube(name, size, height, rng):
    """Кубический горшок с полостью."""
    wall = rng.uniform(0.003, 0.005)
    hs = size / 2
    hs_in = hs - wall

    bm = bmesh.new()

    # Внешний бокс: от z=0 до z=height
    def _ring(sx, sy, z):
        return [
            bm.verts.new((-sx, -sy, z)),
            bm.verts.new((sx, -sy, z)),
            bm.verts.new((sx, sy, z)),
            bm.verts.new((-sx, sy, z)),
        ]

    ob = _ring(hs, hs, 0)        # outer bottom
    ot = _ring(hs, hs, height)    # outer top
    ib = _ring(hs_in, hs_in, wall)     # inner bottom
    it = _ring(hs_in, hs_in, height)   # inner top

    for i in range(4):
        j = (i + 1) % 4
        # Внешние стенки
        bm.faces.new([ob[i], ob[j], ot[j], ot[i]])
        # Внутренние стенки
        bm.faces.new([ib[i], it[i], it[j], ib[j]])
        # Верхний обод
        bm.faces.new([ot[i], ot[j], it[j], it[i]])
        # Дно (между внешним и внутренним)
        bm.faces.new([ob[i], ib[i], ib[j], ob[j]])

    # Внешнее дно
    bm.faces.new(ob[::-1])
    # Внутреннее дно
    bm.faces.new(ib)

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    pot = bpy.data.objects.new(name, mesh)
    pot.data.materials.append(mat_pot(rng))

    soil_z = height * rng.uniform(0.7, 0.85)
    soil = create_box(f"{name}_Soil", hs_in * 0.97, hs_in * 0.97, 0.003)
    soil.location = (0, 0, soil_z)
    soil.data.materials.append(mat_soil())

    return [pot, soil], soil_z


def make_random_pot(name, rng, pot_radius, pot_height):
    """Случайный горшок. Возвращает (objects, pot_top_z)."""
    pot_style = rng.choice(['cylinder', 'tapered', 'cube'])
    if pot_style == 'cylinder':
        return create_pot_cylinder(name, pot_radius, pot_height, rng)
    elif pot_style == 'tapered':
        r_bottom = pot_radius * rng.uniform(0.65, 0.85)
        return create_pot_tapered(name, pot_radius, r_bottom, pot_height, rng)
    else:
        return create_pot_cube(name, pot_radius * 2, pot_height, rng)

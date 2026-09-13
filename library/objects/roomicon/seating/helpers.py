"""Утилиты для генерации кроватей и диванов."""

import bpy
from common.shared_geometry import create_box, create_cylinder
from common.shared_materials import get_or_create_mat, setup_principled


# ============================================================
# Материалы
# ============================================================

WOOD_STYLES = [
    ("LightOak", (0.55, 0.4, 0.22, 1.0), 0.5),
    ("DarkWalnut", (0.25, 0.15, 0.08, 1.0), 0.45),
    ("WhitePaint", (0.92, 0.91, 0.88, 1.0), 0.35),
    ("Birch", (0.7, 0.6, 0.45, 1.0), 0.45),
]

METAL_STYLES = [
    ("BlackMetal", (0.08, 0.08, 0.08, 1.0), 0.4),
    ("Chrome", (0.7, 0.7, 0.72, 1.0), 0.15),
]

FABRIC_STYLES = [
    ("DarkBlue", (0.18, 0.22, 0.35, 1.0), 0.85),
    ("Gray", (0.5, 0.5, 0.5, 1.0), 0.8),
    ("Beige", (0.65, 0.58, 0.45, 1.0), 0.8),
    ("DarkGreen", (0.15, 0.28, 0.18, 1.0), 0.85),
    ("Charcoal", (0.2, 0.2, 0.2, 1.0), 0.8),
    ("Burgundy", (0.4, 0.12, 0.12, 1.0), 0.8),
    ("Taupe", (0.55, 0.48, 0.4, 1.0), 0.8),
]

LEATHER_STYLES = [
    ("BlackLeather", (0.08, 0.08, 0.08, 1.0), 0.55),
    ("BrownLeather", (0.3, 0.18, 0.1, 1.0), 0.5),
    ("TanLeather", (0.55, 0.38, 0.22, 1.0), 0.5),
]

MATTRESS_COLORS = [
    (0.92, 0.9, 0.87, 1.0),
    (0.88, 0.86, 0.82, 1.0),
    (0.85, 0.85, 0.85, 1.0),
]


def mat_wood(rng):
    name, color, roughness = rng.choice(WOOD_STYLES)
    return setup_principled(get_or_create_mat(f"M_Bed_{name}"), color, roughness=roughness)


def mat_metal(rng):
    name, color, roughness = rng.choice(METAL_STYLES)
    return setup_principled(get_or_create_mat(f"M_BedMetal_{name}"),
                             color, roughness=roughness, metallic=1.0, specular=0.8)


def mat_fabric(rng):
    name, color, roughness = rng.choice(FABRIC_STYLES)
    mat = setup_principled(get_or_create_mat(f"M_Upholstery_{name}"),
                            color, roughness=roughness)
    bsdf = [n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    bsdf.inputs['Sheen Weight'].default_value = 0.3
    return mat


def mat_leather(rng):
    name, color, roughness = rng.choice(LEATHER_STYLES)
    return setup_principled(get_or_create_mat(f"M_Leather_{name}"),
                             color, roughness=roughness, specular=0.4)


def mat_mattress(rng):
    color = rng.choice(MATTRESS_COLORS)
    return setup_principled(get_or_create_mat("M_Mattress"), color, roughness=0.8, specular=0.1)


def make_mattress(name, sx, sy, sz,noise = 0.05):
    """Матрас: бокс со скруглёнными углами, subdivision и лёгким шумом."""
    obj = create_box(name, sx, sy, sz)

    # Скругление рёбер
    bevel = obj.modifiers.new("Bevel", 'BEVEL')
    bevel.width = min(sx, sy, sz) * 0.4
    bevel.segments = 3
    bevel.limit_method = 'ANGLE'

    # Сглаживание
    subdiv = obj.modifiers.new("Subdiv", 'SUBSURF')
    subdiv.levels = 3
    subdiv.render_levels = 3

    # Лёгкие неровности поверхности
    tex = bpy.data.textures.new(f"{name}_Noise", type='CLOUDS')
    tex.noise_scale = 0.3

    disp = obj.modifiers.new("Displace", 'DISPLACE')
    disp.texture = tex
    disp.strength = noise
    disp.mid_level = 0.5

    for p in obj.data.polygons:
        p.use_smooth = True

    return obj


def mat_cushion(base_fabric_mat, rng):
    """Подушка — чуть отличающийся оттенок от основной обивки."""
    bsdf = [n for n in base_fabric_mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    base_color = list(bsdf.inputs['Base Color'].default_value)
    # Слегка осветляем или затемняем
    shift = rng.uniform(-0.05, 0.05)
    color = (
        max(0, min(1, base_color[0] + shift)),
        max(0, min(1, base_color[1] + shift)),
        max(0, min(1, base_color[2] + shift)),
        1.0,
    )
    mat = setup_principled(get_or_create_mat("M_Cushion"), color, roughness=0.85)
    bsdf2 = [n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    bsdf2.inputs['Sheen Weight'].default_value = 0.4
    return mat

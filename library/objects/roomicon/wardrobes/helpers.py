"""Утилиты для генерации шкафов."""

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
    ("Wenge", (0.15, 0.1, 0.06, 1.0), 0.4),
]

METAL_STYLES = [
    ("BlackMetal", (0.08, 0.08, 0.08, 1.0), 0.4),
    ("Chrome", (0.7, 0.7, 0.72, 1.0), 0.15),
]


def mat_wood(rng):
    name, color, roughness = rng.choice(WOOD_STYLES)
    return setup_principled(get_or_create_mat(f"M_Ward_{name}"), color, roughness=roughness)


def mat_metal(rng):
    name, color, roughness = rng.choice(METAL_STYLES)
    return setup_principled(get_or_create_mat(f"M_WardMetal_{name}"),
                              color, roughness=roughness, metallic=1.0, specular=0.8)

"""Утилиты для генерации полок: боксы, материалы."""

import bpy

from common.shared_geometry import create_box
from common.shared_materials import get_or_create_mat, setup_principled


# ============================================================
# Материалы
# ============================================================

WOOD_STYLES = [
    ("LightOak", (0.55, 0.4, 0.22, 1.0), 0.5),
    ("DarkWalnut", (0.25, 0.15, 0.08, 1.0), 0.45),
    ("WhitePaint", (0.92, 0.91, 0.88, 1.0), 0.4),
    ("Pine", (0.65, 0.5, 0.3, 1.0), 0.5),
    ("Birch", (0.7, 0.6, 0.45, 1.0), 0.45),
]

METAL_STYLES = [
    ("BlackMetal", (0.08, 0.08, 0.08, 1.0), 0.4),
    ("Chrome", (0.7, 0.7, 0.72, 1.0), 0.15),
]


def mat_wood(style_idx=0):
    name, color, roughness = WOOD_STYLES[style_idx]
    mat = get_or_create_mat(f"M_Shelf_{name}")
    return setup_principled(mat, color, roughness=roughness, specular=0.3)


def mat_metal(style_idx=0):
    name, color, roughness = METAL_STYLES[style_idx]
    mat = get_or_create_mat(f"M_Bracket_{name}")
    return setup_principled(mat, color, roughness=roughness, metallic=1.0, specular=0.8)

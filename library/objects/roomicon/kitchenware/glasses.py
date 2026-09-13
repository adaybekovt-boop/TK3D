"""Процедурная генерация стаканов и бокалов через тело вращения."""

import bpy
import bmesh
import math
import random

from plates import _interpolate_profile
from vases import _create_spin_object

SPIN_SEGMENTS = 48
PROFILE_SEGMENTS = 16


# ============================================================
# Профили стаканов
# ============================================================

def _tumbler_profile(rng, radius, height, thickness):
    """Обычный стакан: слегка расширяющийся кверху."""
    base_r = radius * rng.uniform(0.85, 0.95)
    top_r = radius
    # Лёгкое утолщение дна
    bottom_thick = thickness * rng.uniform(1.5, 2.5)

    inner = [
        (0, bottom_thick),
        (base_r - thickness, bottom_thick),
        (base_r - thickness + (top_r - base_r) * 0.3, height * 0.3),
#        (top_r - thickness, height * 0.95),
        (top_r - thickness, height),
    ]
    outer = [
        (0, 0),
        (base_r, 0),
        (base_r + (top_r - base_r) * 0.3, height * 0.3),
#        (top_r, height * 0.95),
        (top_r, height),
    ]
    return inner, outer


def _highball_profile(rng, radius, height, thickness):
    """Высокий стакан: прямые стенки."""
    base_r = radius * rng.uniform(0.92, 1.0)
    top_r = radius * rng.uniform(1.0, 1.05)
    bottom_thick = thickness * rng.uniform(2.0, 3.0)

    inner = [
        (0, bottom_thick),
        (base_r - thickness, bottom_thick),
        (top_r - thickness, height * 0.80),
        (top_r - thickness, height),
    ]
    outer = [
        (0, 0),
        (base_r, 0),
        (top_r, height * 0.80),
        (top_r, height),
    ]
    return inner, outer


def _wine_glass_profile(rng, radius, height, thickness):
    """Бокал для вина: ножка + чаша."""
    stem_r = radius * rng.uniform(0.06, 0.1)
    base_r = radius * rng.uniform(0.5, 0.65)
    bowl_r = radius
    stem_h = height * rng.uniform(0.3, 0.4)
    bowl_start_h = stem_h + height * 0.02
    bowl_max_h = height * rng.uniform(0.55, 0.65)
    rim_r = bowl_r * rng.uniform(0.7, 0.9)

    base_thick = 0.003
    stem_thick = stem_r * 0.6

    inner = [
        (0, bowl_start_h),
        (bowl_r - thickness, bowl_max_h),
        (rim_r - thickness, height * 0.92),
        (rim_r - thickness, height),
    ]
    outer = [
        (0, 0),
        (base_r*0.5, 0),
        (base_r, 0),
        (base_r, 0.004),
        (base_r*0.5, 0.004),
        (stem_r*1.1, 0.006),
        (stem_r, stem_h*0.5),
        (stem_r, stem_h*0.7),
        (stem_r, stem_h),
        (stem_r, stem_h),
        (bowl_r, bowl_max_h),
        (rim_r, height * 0.92),
        (rim_r, height),
    ]
    return inner, outer


# ============================================================
# Материал стекла
# ============================================================

def create_glass_material(name="M_Glass", color=(0.95, 0.97, 1.0, 1.0), roughness=0.0):
    """Прозрачное стекло."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.blend_method = 'HASHED'  # EEVEE прозрачность
    tree = mat.node_tree

    for n in list(tree.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            tree.nodes.remove(n)

    output = [n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    output.location = (600, 0)

    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (200, 0)
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Specular IOR Level'].default_value = 0.5
    bsdf.inputs['IOR'].default_value = 1.45
    bsdf.inputs['Transmission Weight'].default_value = 0.95
    bsdf.inputs['Alpha'].default_value = 0.3

    tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat


GLASS_VARIANTS = [
    ("Clear", (0.95, 0.97, 1.0, 1.0), 0.0),
    ("Frosted", (0.9, 0.92, 0.95, 1.0), 0.4),
    ("GreenTint", (0.85, 0.95, 0.88, 1.0), 0.02),
    ("BlueTint", (0.88, 0.92, 1.0, 1.0), 0.02),
    ("Amber", (1.0, 0.9, 0.75, 1.0), 0.05),
]


# ============================================================
# Публичный API
# ============================================================

GLASS_TYPES = {
    'tumbler': {
        'profile_fn': _tumbler_profile,
        'radius': (0.035, 0.04),
        'height': (0.09, 0.12),
        'thickness': (0.002, 0.003),
    },
    'highball': {
        'profile_fn': _highball_profile,
        'radius': (0.03, 0.035),
        'height': (0.14, 0.16),
        'thickness': (0.002, 0.003),
    },
    'wine': {
        'profile_fn': _wine_glass_profile,
        'radius': (0.04, 0.05),
        'height': (0.18, 0.23),
        'thickness': (0.0015, 0.002),
    },
}


def generate_glass(seed, glass_type='tumbler', color_idx=None):
    """Генерирует один стакан/бокал."""
    rng = random.Random(seed)
    spec = GLASS_TYPES[glass_type]

    radius = rng.uniform(*spec['radius'])
    height = rng.uniform(*spec['height'])
    thickness = rng.uniform(*spec['thickness'])

    inner, outer = spec['profile_fn'](rng, radius, height, thickness)
    name = f"Glass_{glass_type}_{seed}"
    obj = _create_spin_object(name, inner, outer)

    if color_idx is None:
        color_idx = rng.randint(0, len(GLASS_VARIANTS) - 1)
    variant_name, color, roughness = GLASS_VARIANTS[color_idx]
    mat = create_glass_material(f"M_Glass_{variant_name}", color, roughness)
    obj.data.materials.append(mat)

    return obj

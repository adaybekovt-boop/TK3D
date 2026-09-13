"""Настольные лампы: классическая + ночник."""

import bpy
import random

from helpers import (
    create_spin_solid, create_spin_surface, create_cylinder, create_bulb,
    create_metal_material, create_shade_material, create_glass_shade_material,
    METAL_COLORS, SHADE_COLORS, GLASS_COLORS, catmull_rom,
)

TABLETOP_TYPES = {
    'classic': {},
    'nightlight': {},
}


def _make_classic(rng):
    """Классическая настольная лампа: основание + ножка + абажур."""
    # Параметры
    base_r = rng.uniform(0.06, 0.09)
    base_h = rng.uniform(0.015, 0.025)
    stem_r = rng.uniform(0.008, 0.012)
    stem_h = rng.uniform(0.2, 0.32)
    shade_r_bottom = rng.uniform(0.10, 0.15)
    shade_r_top = shade_r_bottom * rng.uniform(0.4, 0.7)
    shade_h = rng.uniform(0.12, 0.18)

    total_stem = base_h + stem_h
    shade_bottom_z = total_stem - shade_h * 0.15  # абажур чуть налезает на ножку

    objects = []

    # Основание (spin solid)
    t = 0.005
    base_outer = [(0, base_h), (base_r * 0.8, base_h), (base_r, 0)]
    base_inner = [(0, 0), (base_r * 0.8, 0), (base_r, 0)]
    base_obj = create_spin_solid("LampBase", base_inner, base_outer)

    mc = rng.choice(METAL_COLORS)
    base_obj.data.materials.append(create_metal_material(f"M_{mc[0]}", mc[1], mc[2]))
    objects.append(base_obj)

    # Ножка
    stem = create_cylinder("LampStem", stem_r, stem_h, z_offset=base_h)
    stem.data.materials.append(base_obj.data.materials[0])  # тот же металл
    objects.append(stem)

    # Абажур (spin surface + solidify)
    shade_profile = [
        (shade_r_top, shade_bottom_z + shade_h),
        (shade_r_top * 1.02, shade_bottom_z + shade_h * 0.95),
        (shade_r_bottom * 0.95, shade_bottom_z + shade_h * 0.1),
        (shade_r_bottom, shade_bottom_z),
    ]
    shade = create_spin_surface("LampShade", shade_profile)
    sc = rng.choice(SHADE_COLORS)
    shade.data.materials.append(create_shade_material(f"M_Shade_{sc[0]}", sc[1]))
    objects.append(shade)

    # Лампочка внутри абажура
    bulb_z = stem_h + base_h #shade_bottom_z + shade_h * 0.4
    bulb, bulb_light = create_bulb("LampBulb", shade_r_top * 0.3, rng,
                                    location=(0, 0, bulb_z))
    objects.extend([bulb, bulb_light])

    return objects


def _make_nightlight(rng):
    """Ночник: низкая форма, плафон-шар или цилиндр на основании."""
    base_r = rng.uniform(0.04, 0.06)
    base_h = rng.uniform(0.01, 0.02)
    shade_r = rng.uniform(0.05, 0.08)
    shade_h = rng.uniform(0.08, 0.14)

    objects = []

    # Основание
    t = 0.004
    base_inner = [(0, base_h), (base_r, base_h), (base_r, 0)]
    base_outer = [(0, 0), (base_r*0.8,0), (base_r, 0)]
    base_obj = create_spin_solid("NightBase", base_inner, base_outer)
    mc = rng.choice(METAL_COLORS)
    base_obj.data.materials.append(create_metal_material(f"M_{mc[0]}", mc[1], mc[2]))
    objects.append(base_obj)

    # Плафон — скруглённый цилиндр или шар
    shape = rng.choice(['sphere', 'cylinder'])
    if shape == 'sphere':
        sr = shade_r
        profile = [
            (0.001, base_h),
            (sr * 0.7, base_h + sr * 0.3),
            (sr, base_h + sr),
            (sr * 0.7, base_h + sr * 1.7),
            (0.001, base_h + sr * 2),
        ]
    else:
        profile = [
            (shade_r * 0.3, base_h),
            (shade_r, base_h + shade_h * 0.1),
            (shade_r, base_h + shade_h * 0.9),
            (shade_r * 0.3, base_h + shade_h),
        ]

    shade = create_spin_surface("NightShade", profile)
    gc = rng.choice(GLASS_COLORS)
    shade.data.materials.append(create_glass_shade_material(f"M_Glass_{gc[0]}", gc[1], gc[2]))
    objects.append(shade)

    # Лампочка внутри плафона
    if shape == 'sphere':
        bulb_z = base_h + shade_r*0.5
    else:
        bulb_z = base_h + shade_r*0.25

    bulb, bulb_light = create_bulb("NightBulb", shade_r * 0.25, rng,
                                    location=(0, 0, bulb_z))
    objects.extend([bulb, bulb_light])

    return objects


def generate_tabletop_lamp(seed, subtype='classic'):
    rng = random.Random(seed)
    if subtype == 'classic':
        return _make_classic(rng)
    else:
        return _make_nightlight(rng)

"""Потолочные светильники: подвес + плафон потолочный."""

import bpy
import random

from helpers import (
    create_spin_solid, create_spin_surface, create_cylinder, create_bulb,
    create_metal_material, create_glass_shade_material, create_shade_material,
    METAL_COLORS, GLASS_COLORS, SHADE_COLORS,
)

CEILING_TYPES = {
    'pendant': {},
    'flush': {},
}


def _make_pendant(rng):
    """Подвесной светильник: шнур/цепочка + плафон."""
    cord_r = rng.uniform(0.003, 0.005)
    cord_h = rng.uniform(0.3, 0.6)
    canopy_r = rng.uniform(0.03, 0.05)  # розетка у потолка
    canopy_h = 0.015

    shade_type = rng.choice(['sphere', 'cone', 'cylinder', 'dome'])
    shade_r = rng.uniform(0.08, 0.18)
    shade_h = rng.uniform(0.1, 0.25)

    objects = []

    # Розетка у потолка (origin = точка крепления к потолку = верх)
    # Всё строим вниз от Z=0
    t = 0.004
    canopy_inner = [(0, -canopy_h + t), (canopy_r, -canopy_h + t), (canopy_r, 0)]
    canopy_outer = [(0, -canopy_h), (canopy_r, -canopy_h), (canopy_r, 0)]
    canopy = create_spin_solid("PendantCanopy", canopy_inner, canopy_outer)
    mc = rng.choice(METAL_COLORS)
    mat = create_metal_material(f"M_{mc[0]}", mc[1], mc[2])
    canopy.data.materials.append(mat)
    objects.append(canopy)

    # Шнур
    cord = create_cylinder("PendantCord", cord_r, cord_h, z_offset=-(canopy_h + cord_h))
    cord.data.materials.append(mat)
    objects.append(cord)

    # Плафон
    shade_top_z = -(canopy_h + cord_h)
    shade_bot_z = shade_top_z - shade_h

    if shade_type == 'sphere':
        profile = [
            (0.001, shade_top_z),
            (shade_r * 0.7, shade_top_z - shade_h * 0.15),
            (shade_r, shade_top_z - shade_h * 0.5),
            (shade_r * 0.7, shade_top_z - shade_h * 0.85),
            (0.001, shade_bot_z),
        ]
    elif shade_type == 'cone':
        profile = [
            (0.01, shade_top_z),
            (shade_r * 0.15, shade_top_z - shade_h * 0.05),
            (shade_r, shade_bot_z + shade_h * 0.05),
            (shade_r, shade_bot_z),
        ]
    elif shade_type == 'cylinder':
        profile = [
            (shade_r, shade_top_z),
            (shade_r, shade_bot_z),
        ]
    else:  # dome
        profile = [
            (0.001, shade_top_z),
            (shade_r * 0.5, shade_top_z - shade_h * 0.1),
            (shade_r, shade_top_z - shade_h * 0.5),
            (shade_r, shade_bot_z),
        ]

    shade = create_spin_surface("PendantShade", profile)

    # Материал — стекло или ткань
    if rng.random() < 0.6:
        gc = rng.choice(GLASS_COLORS)
        shade.data.materials.append(create_glass_shade_material(f"M_Glass_{gc[0]}", gc[1], gc[2]))
    else:
        sc = rng.choice(SHADE_COLORS)
        shade.data.materials.append(create_shade_material(f"M_Shade_{sc[0]}", sc[1]))

    objects.append(shade)

    # Лампочка
    bulb_z = (shade_top_z + shade_bot_z) / 2
    bulb, bulb_light = create_bulb("PendantBulb", shade_r * 0.2, rng,
                                    location=(0, 0, bulb_z))
    objects.extend([bulb, bulb_light])

    return objects


def _make_flush(rng):
    """Плафон потолочный: плоский, прижатый к потолку."""
    base_r = rng.uniform(0.12, 0.2)
    base_h = rng.uniform(0.06, 0.12)

    objects = []

    # Основание (металлическое крепление)
    t = 0.004
    mount_r = base_r * 0.3
    mount_inner = [(0, -t), (mount_r, -t), (mount_r, 0)]
    mount_outer = [(0, -t * 2), (mount_r, -t * 2), (mount_r, 0)]
    mount = create_spin_solid("FlushMount", mount_inner, mount_outer)
    mc = rng.choice(METAL_COLORS)
    mount.data.materials.append(create_metal_material(f"M_{mc[0]}", mc[1], mc[2]))
    objects.append(mount)

    # Плафон
    shape = rng.choice(['dome', 'flat'])
    if shape == 'dome':
        profile = [
            (0.001, 0),
            (base_r * 0.6, -base_h * 0.2),
            (base_r, -base_h * 0.7),
            (base_r * 0.95, -base_h),
        ]
    else:
        profile = [
            (base_r * 0.2, 0),
            (base_r, -base_h * 0.15),
            (base_r, -base_h * 0.85),
            (base_r * 0.85, -base_h),
        ]

    shade = create_spin_surface("FlushShade", profile)
    gc = rng.choice(GLASS_COLORS)
    shade.data.materials.append(create_glass_shade_material(f"M_Glass_{gc[0]}", gc[1], gc[2]))
    objects.append(shade)

    # Лампочка
    bulb, bulb_light = create_bulb("FlushBulb", base_r * 0.2, rng,
                                    location=(0, 0, -base_h * 0.5))
    objects.extend([bulb, bulb_light])

    return objects


def generate_ceiling_lamp(seed, subtype='pendant'):
    rng = random.Random(seed)
    if subtype == 'pendant':
        return _make_pendant(rng)
    else:
        return _make_flush(rng)

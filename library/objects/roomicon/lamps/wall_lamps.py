"""Настенные светильники: бра."""

import bpy
import random,math

from helpers import (
    create_spin_solid, create_spin_surface, create_cylinder, create_bulb,
    create_metal_material, create_glass_shade_material,
    METAL_COLORS, GLASS_COLORS,
)

WALL_TYPES = {
    'sconce': {},
}


def _make_sconce(rng):
    """Бра: крепление + рожок + плафон. Origin — точка крепления к стене."""
    plate_r = rng.uniform(0.03, 0.045)
    plate_h = rng.uniform(0.015, 0.025)
    arm_r = rng.uniform(0.006, 0.01)
    arm_len = rng.uniform(0.08, 0.14)
    shade_r = rng.uniform(0.04, 0.07)
    shade_h = rng.uniform(0.06, 0.1)

    objects = []

    # Крепёжная пластина — диск на стене (в плоскости XZ)
    # Spin создаёт в XY, поворачиваем на -90° по X чтобы лечь в XZ
    t = 0.005
    plate_inner = [(0, plate_h), (plate_r*0.7, plate_h), (plate_r, 0)]
    plate_outer = [(0, 0), (plate_r/2, 0), (plate_r, 0)]
    plate = create_spin_solid("SconceBase", plate_inner, plate_outer)
    plate.rotation_euler = (-1.5708, 0, 0)  # ось пластины по Y (от стены)
    mc = rng.choice(METAL_COLORS)
    mat = create_metal_material(f"M_{mc[0]}", mc[1], mc[2])
    plate.data.materials.append(mat)
    objects.append(plate)

    # Рожок — горизонтально от стены по Y
    arm = create_cylinder("SconceArm", arm_r, arm_len, z_offset=0)
    arm.location = (0, plate_h, 0)
    arm.rotation_euler = (-1.5708, 0, 0)  # ось по Y
    arm.data.materials.append(mat)
    objects.append(arm)

    # Плафон (на конце рожка)
    shade_z = 0
    shade_type = rng.choice(['up', 'down'])
    if shade_type == 'up':
        profile = [
            (shade_r * 0.3, shade_z),
            (shade_r, shade_z + shade_h * 0.15),
            (shade_r * 0.95, shade_z + shade_h * 0.85),
            (shade_r * 0.3, shade_z + shade_h),
        ]
    else:
        profile = [
            (shade_r * 0.3, shade_z + shade_h),
            (shade_r, shade_z + shade_h * 0.85),
            (shade_r * 0.95, shade_z + shade_h * 0.15),
            (shade_r * 0.3, shade_z),
        ]

    shade = create_spin_surface("SconceShade", profile)
    shade.location = (0, plate_h + arm_len, -shade_h / 2)
    gc = rng.choice(GLASS_COLORS)
    shade.data.materials.append(create_glass_shade_material(f"M_Glass_{gc[0]}", gc[1], gc[2]))
    objects.append(shade)

    # Лампочка внутри абажура
    bulb, bulb_light = create_bulb("SconceBulb", shade_r * 0.25, rng,
                                    location=(0, plate_h + arm_len, 0))
    bulb.rotation_euler = (math.pi / 2, 0, 0)
    objects.extend([bulb, bulb_light])

    return objects


def generate_wall_lamp(seed, subtype='sconce'):
    rng = random.Random(seed)
    return _make_sconce(rng)

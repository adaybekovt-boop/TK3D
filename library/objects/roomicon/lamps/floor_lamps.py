"""Напольные лампы: торшер + торшер-дуга."""

import bpy
import bmesh
import math
import random

from helpers import (
    create_spin_solid, create_spin_surface, create_cylinder, create_bulb,
    create_metal_material, create_shade_material,
    METAL_COLORS, SHADE_COLORS, catmull_rom,
)

FLOOR_TYPES = {
    'floor_lamp': {},
    'arc_lamp': {},
}


def _make_floor_lamp(rng):
    """Торшер: тонкая ножка + абажур."""
    base_r = rng.uniform(0.12, 0.16)
    base_h = rng.uniform(0.015, 0.025)
    stem_r = rng.uniform(0.01, 0.015)
    stem_h = rng.uniform(1.3, 1.6)
    shade_r_bottom = rng.uniform(0.15, 0.22)
    shade_r_top = shade_r_bottom * rng.uniform(0.35, 0.6)
    shade_h = rng.uniform(0.18, 0.28)

    shade_bottom_z = base_h + stem_h - shade_h * 0.1
    objects = []

    # Основание
    t = 0.006
    base_inner = [(0, base_h), (base_r * 0.8, base_h), (base_r, 0)]
    base_outer = [(0, 0), (base_r * 0.9, 0), (base_r, 0)]
    base_obj = create_spin_solid("FloorBase", base_inner, base_outer)
    mc = rng.choice(METAL_COLORS)
    mat = create_metal_material(f"M_{mc[0]}", mc[1], mc[2])
    base_obj.data.materials.append(mat)
    objects.append(base_obj)

    # Ножка
    stem = create_cylinder("FloorStem", stem_r, stem_h*1.05, z_offset=base_h)
    stem.data.materials.append(mat)
    objects.append(stem)

    # Абажур
    shade_profile = [
        (shade_r_top, shade_bottom_z + shade_h),
        (shade_r_top * 1.05, shade_bottom_z + shade_h * 0.92),
        (shade_r_bottom * 0.95, shade_bottom_z + shade_h * 0.08),
        (shade_r_bottom, shade_bottom_z),
    ]
    shade = create_spin_surface("FloorShade", shade_profile)
    sc = rng.choice(SHADE_COLORS)
    shade.data.materials.append(create_shade_material(f"M_Shade_{sc[0]}", sc[1]))
    objects.append(shade)

    # Лампочка
    bulb_z = shade_bottom_z + shade_h * 0.4
    bulb, bulb_light = create_bulb("FloorBulb", shade_r_top * 0.3, rng,
                                    location=(0, 0, bulb_z))
    objects.extend([bulb, bulb_light])

    return objects


def _make_arc_lamp(rng):
    """Торшер-дуга: изогнутая ножка + свисающий абажур."""
    base_r = rng.uniform(0.15, 0.2)
    base_h = rng.uniform(0.02, 0.03)
    stem_r = rng.uniform(0.012, 0.018)
    arc_height = rng.uniform(1.5, 1.8)
    arc_reach = rng.uniform(0.5, 0.8)
    shade_r = rng.uniform(0.12, 0.18)
    shade_h = rng.uniform(0.15, 0.22)

    objects = []

    # Основание
    t = 0.008
    base_inner = [(0, base_h), (base_r * 0.8, base_h), (base_r, 0)]
    base_outer = [(0, 0), (base_r * 0.9, 0), (base_r, 0)]

    base_obj = create_spin_solid("ArcBase", base_inner, base_outer)
    mc = rng.choice(METAL_COLORS)
    mat = create_metal_material(f"M_{mc[0]}", mc[1], mc[2])
    base_obj.data.materials.append(mat)
    objects.append(base_obj)

    # Дуга (трубка вдоль кривой)
    arc_points = [
        (0, base_h),
        (0, arc_height * 0.5),
        (arc_reach * 0.3, arc_height * 0.85),
        (arc_reach * 0.7, arc_height * 0.97),
        (arc_reach, arc_height),
    ]
    path = catmull_rom(arc_points, segments_per_span=8)

    bm = bmesh.new()
    n_prof = 8
    rings = []
    for idx in range(len(path)):
        px, pz = path[idx]
        if idx < len(path) - 1:
            dx = path[idx+1][0] - px
            dz = path[idx+1][1] - pz
        else:
            dx = px - path[idx-1][0]
            dz = pz - path[idx-1][1]
        length = math.sqrt(dx*dx + dz*dz)
        if length < 1e-8:
            dx, dz = 0, 1
        else:
            dx /= length
            dz /= length

        ring = []
        for j in range(n_prof):
            angle = 2 * math.pi * j / n_prof
            nx = stem_r * math.cos(angle)
            nb = stem_r * math.sin(angle)
            ring.append(bm.verts.new((px + nb * (-dz) + nx * 0, nb * dx, pz + nb * dx + nx * 0)))
        # Упрощённый вариант — трубка в плоскости XZ
        ring2 = []
        for j in range(n_prof):
            angle = 2 * math.pi * j / n_prof
            ry = stem_r * math.cos(angle)
            roffset = stem_r * math.sin(angle)
            ring2.append(bm.verts.new((px + roffset * (-dz), ry, pz + roffset * dx)))
        rings.append(ring2)

    # Удалим первый набор ring (ошибочный)
    # Пересоздаём чисто
    bm.free()
    bm = bmesh.new()
    rings = []
    for idx in range(len(path)):
        px, pz = path[idx]
        if idx < len(path) - 1:
            dx = path[idx+1][0] - px
            dz = path[idx+1][1] - pz
        else:
            dx = px - path[idx-1][0]
            dz = pz - path[idx-1][1]
        length = math.sqrt(dx*dx + dz*dz)
        if length < 1e-8:
            dx, dz = 0, 1
        else:
            dx /= length
            dz /= length

        ring = []
        for j in range(n_prof):
            angle = 2 * math.pi * j / n_prof
            ry = stem_r * math.cos(angle)
            r_tang = stem_r * math.sin(angle)
            ring.append(bm.verts.new((px + r_tang * (-dz), ry, pz + r_tang * dx)))
        rings.append(ring)

    for i in range(len(rings) - 1):
        for j in range(n_prof):
            j2 = (j + 1) % n_prof
            try:
                bm.faces.new([rings[i][j], rings[i][j2], rings[i+1][j2], rings[i+1][j]])
            except ValueError:
                pass

    # Закрываем торцы
    try:
        bm.faces.new(rings[0][::-1])
    except ValueError:
        pass
    try:
        bm.faces.new(rings[-1])
    except ValueError:
        pass

    mesh = bpy.data.meshes.new("ArcStem")
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.update()
    stem_obj = bpy.data.objects.new("ArcStem", mesh)
    stem_obj.data.materials.append(mat)
    objects.append(stem_obj)

    # Абажур (свисает с конца дуги)
    shade_z = arc_height - shade_h
    shade_profile = [
        (0.01, shade_z + shade_h),
        (shade_r * 0.3, shade_z + shade_h * 0.9),
        (shade_r, shade_z + shade_h * 0.2),
        (shade_r * 0.95, shade_z),
    ]
    shade = create_spin_surface("ArcShade", shade_profile)
    shade.location = (arc_reach, 0, 0)
    sc = rng.choice(SHADE_COLORS)
    shade.data.materials.append(create_shade_material(f"M_Shade_{sc[0]}", sc[1]))
    objects.append(shade)

    # Лампочка
    bulb_z = shade_z + shade_h * 0.5
    bulb, bulb_light = create_bulb("ArcBulb", shade_r * 0.25, rng,
                                    location=(arc_reach, 0, bulb_z))
    objects.extend([bulb, bulb_light])

    return objects


def generate_floor_lamp(seed, subtype='floor_lamp'):
    rng = random.Random(seed)
    if subtype == 'floor_lamp':
        return _make_floor_lamp(rng)
    else:
        return _make_arc_lamp(rng)

"""Генерация свечей и подсвечников."""

import bpy
import bmesh
import random
import math

from helpers import (
    create_candle_body, create_cylinder, create_box,
    mat_holder_metal, mat_tray, mat_wax, mat_wick, mat_flame,
    get_or_create_mat, setup_principled,
)


CANDLE_TYPES = {
    'single': {},
    'candlestick': {},
    'group': {},
    'tealight': {},
}


# ============================================================
# Одиночная свеча (pillar candle)
# ============================================================

def _make_single(rng):
    """Толстая свеча-столб."""
    radius = rng.uniform(0.025, 0.045)
    height = rng.uniform(0.08, 0.2)
    return create_candle_body("Candle", radius, height, rng)


# ============================================================
# Свеча в подсвечнике (candlestick)
# ============================================================

def _make_candlestick(rng):
    """Тонкая свеча в классическом подсвечнике."""
    objects = []
    metal_mat = mat_holder_metal(rng)

    # База подсвечника — диск
    base_r = rng.uniform(0.035, 0.055)
    base_h = rng.uniform(0.005, 0.01)
    base = create_cylinder("Base", base_r, base_h, segments=20)
    base.data.materials.append(metal_mat)
    objects.append(base)

    # Ножка
    stem_r = rng.uniform(0.005, 0.01)
    stem_h = rng.uniform(0.08, 0.18)
    stem = create_cylinder("Stem", stem_r, stem_h, z_offset=base_h, segments=12)
    stem.data.materials.append(metal_mat)
    objects.append(stem)

    # Тарелочка сверху
    cup_r = rng.uniform(0.015, 0.025)
    cup_h = 0.008
    cup = create_cylinder("Cup", cup_r, cup_h, z_offset=base_h + stem_h, segments=16)
    cup.data.materials.append(metal_mat)
    objects.append(cup)

    # Свеча
    candle_r = rng.uniform(0.008, 0.013)
    candle_h = rng.uniform(0.1, 0.2)
    candle_objs = create_candle_body("Candle", candle_r, candle_h, rng,
                                      z_offset=base_h + stem_h + cup_h)
    objects.extend(candle_objs)

    return objects


# ============================================================
# Группа свечей на подносе
# ============================================================

def _make_group(rng):
    """Несколько свечей разной высоты на подносе."""
    objects = []

    n_candles = rng.randint(2, 5)
    # Масштаб подноса растёт с количеством свечей
    scale = 1.0 + (n_candles - 2) * 0.15

    # Поднос
    tray_style = rng.choice(['round', 'rect'])
    if tray_style == 'round':
        tray_r = rng.uniform(0.06, 0.1) * scale
        tray = create_cylinder("Tray", tray_r, 0.008, segments=24)
        tray_extent = tray_r * 0.7
    else:
        tray_w = rng.uniform(0.1, 0.18) * scale
        tray_d = rng.uniform(0.06, 0.1) * scale
        tray = create_box("Tray", tray_w / 2, tray_d / 2, 0.004)
        tray.location = (0, 0, 0.004)
        tray_extent = min(tray_w, tray_d) * 0.35

    tray.data.materials.append(mat_tray(rng))
    objects.append(tray)

    # Общий цвет воска для группы
    wax_mat = mat_wax(rng)

    # Размещаем свечи с проверкой коллизий
    positions = []  # (x, y, radius)
    for i in range(n_candles):
        radius = rng.uniform(0.015, 0.035)
        height = rng.uniform(0.05, 0.15)

        # Ищем позицию без перехлёста
        placed = False
        x, y = 0, 0
        for _attempt in range(20):
            angle = rng.uniform(0, 2 * math.pi)
            dist = rng.uniform(0.01, tray_extent)
            x = dist * math.cos(angle)
            y = dist * math.sin(angle)
            if all(math.hypot(x - px, y - py) > radius + pr + 0.005
                   for px, py, pr in positions):
                placed = True
                break
        if not placed:
            continue
        positions.append((x, y, radius))

        candle_objs = create_candle_body(f"Candle_{i}", radius, height, rng,
                                          z_offset=0.008)
        candle_objs[0].data.materials.clear()
        candle_objs[0].data.materials.append(wax_mat)

        for obj in candle_objs:
            obj.location = (obj.location[0] + x, obj.location[1] + y, obj.location[2])
        objects.extend(candle_objs)

    return objects


# ============================================================
# Чайная свеча (tealight)
# ============================================================

def _make_tealight(rng):
    """Маленькая свеча в алюминиевой гильзе."""
    objects = []

    # Гильза
    cup_r = rng.uniform(0.018, 0.022)
    cup_h = 0.015
    cup = create_cylinder("TealightCup", cup_r, cup_h, segments=20)
    # Алюминий
    cup_mat = get_or_create_mat("M_Aluminium")
    setup_principled(cup_mat, (0.8, 0.8, 0.82, 1.0), roughness=0.2,
                     metallic=1.0, specular=0.7)
    cup.data.materials.append(cup_mat)
    objects.append(cup)

    # Воск внутри (чуть меньше)
    wax_r = cup_r * 0.92
    wax_h = cup_h * 0.6
    wax = create_cylinder("TealightWax", wax_r, wax_h, z_offset=0.002, segments=16)
    wax.data.materials.append(mat_wax(rng))
    objects.append(wax)

    # Фитиль
    wick = create_cylinder("Wick", 0.001, 0.005,
                           z_offset=0.002 + wax_h, segments=6, smooth=False)
    wick.data.materials.append(mat_wick())
    objects.append(wick)

    # Пламя (часто горит)
    if rng.random() < 0.7:
        bm = bmesh.new()
        flame_h = 0.012
        flame_r = 0.003
        top = bm.verts.new((0, 0, flame_h))
        mid_ring = []
        for i in range(8):
            angle = 2 * math.pi * i / 8
            mid_ring.append(bm.verts.new((
                flame_r * math.cos(angle),
                flame_r * math.sin(angle),
                flame_h * 0.35,
            )))
        bottom = bm.verts.new((0, 0, 0))
        for i in range(8):
            j = (i + 1) % 8
            bm.faces.new([top, mid_ring[i], mid_ring[j]])
            bm.faces.new([bottom, mid_ring[j], mid_ring[i]])
        mesh = bpy.data.meshes.new("Flame")
        bm.to_mesh(mesh)
        bm.free()
        for p in mesh.polygons:
            p.use_smooth = True
        mesh.update()
        flame = bpy.data.objects.new("Flame", mesh)
        flame.location = (0, 0, 0.002 + wax_h + 0.005)
        flame.data.materials.append(mat_flame())
        sub = flame.modifiers.new('Sub','SUBSURF')
        sub.levels = 2
        objects.append(flame)

    return objects


# ============================================================
# API
# ============================================================

def generate_candle(seed, subtype='single'):
    rng = random.Random(seed)
    if subtype == 'single':
        return _make_single(rng)
    elif subtype == 'candlestick':
        return _make_candlestick(rng)
    elif subtype == 'group':
        return _make_group(rng)
    elif subtype == 'tealight':
        return _make_tealight(rng)
    else:
        return _make_single(rng)

"""Генерация растений в горшках."""

import bpy
import bmesh
import random
import math

from helpers import (
    make_random_pot, mat_leaf, mat_cactus, mat_trunk,
    create_cylinder, create_box, GREEN_COLORS,
)


PLANT_TYPES = {
    'succulent': {},
    'ficus': {},
    'cactus': {},
    'fern': {},
}


# ============================================================
# Листья / плоские элементы
# ============================================================

def _make_leaf(name, width, height, rng):
    """Плоский лист — овальный, слегка изогнутый."""
    bm = bmesh.new()
    segments = 8
    verts_left = []
    verts_right = []

    for i in range(segments + 1):
        t = i / segments
        y = t * height
        # Профиль: эллипс с максимальной шириной в нижней трети
        w = width * math.sin(t * math.pi) * (1 - 0.3 * t)
        # Лёгкий изгиб вверх
        z = 0.02 * math.sin(t * math.pi)
        verts_left.append(bm.verts.new((-w / 2, y, z)))
        verts_right.append(bm.verts.new((w / 2, y, z)))

    for i in range(segments):
        bm.faces.new([verts_left[i], verts_left[i + 1],
                       verts_right[i + 1], verts_right[i]])

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat_leaf(rng))
    return obj


def _make_teardrop_leaf(name, width, length, thickness, rng):
    """Каплевидный мясистый лист суккулента.

    Широкий у основания, заострённый на кончике, выпуклый по центру.
    Лист вытянут вдоль +Y (основание у 0, кончик у length).
    """
    bm = bmesh.new()
    rows = 7       # сечений вдоль длины
    cols = 8       # вершин по ширине (половина, зеркалим)

    verts_grid = []
    for ir in range(rows):
        t = ir / (rows - 1)  # 0..1 от основания к кончику
        y = t * length

        # Ширина: синус + заострение к кончику (каплевидный контур)
        w = width * math.sin(t * math.pi * 0.85 + 0.15) * (1 - t * 0.4)

        # Высота (выпуклость): максимум у основания, сходит к 0 у кончика
        bulge = thickness * (1 - t) * 0.5

        row = []
        for ic in range(cols + 1):
            s = ic / cols  # 0..1 по ширине
            x = (s - 0.5) * w

            # Поперечный профиль: эллиптическая выпуклость сверху
            cross = 1 - (2 * s - 1) ** 2  # 0 по краям, 1 в центре
            z_top = bulge * cross
            # Снизу плоский, но чуть выпуклый
            z_bot = -thickness * 0.15 * cross * (1 - t)
            z = z_top + z_bot

            # Лёгкий случайный шум для органичности
            z += rng.uniform(-0.0005, 0.0005)

            row.append(bm.verts.new((x, y, z)))
        verts_grid.append(row)

    # Грани
    for ir in range(rows - 1):
        for ic in range(cols):
            v0 = verts_grid[ir][ic]
            v1 = verts_grid[ir][ic + 1]
            v2 = verts_grid[ir + 1][ic + 1]
            v3 = verts_grid[ir + 1][ic]
            bm.faces.new([v0, v1, v2, v3])

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    return obj


# Золотой угол для фибоначчи-спирали
_GOLDEN_ANGLE = math.pi * (3 - math.sqrt(5))  # ≈ 137.508°


# ============================================================
# Суккулент
# ============================================================

def _make_succulent(rng, pot_top_z):
    """Розетка из каплевидных листьев по спирали Фибоначчи."""
    objects = []

    # Базовый цвет с вариацией
    base_color = list(rng.choice(GREEN_COLORS))
    if rng.random() < 0.3:
        # Серо-зелёные или розоватые кончики
        base_color[0] += 0.1
        base_color[1] += 0.05
        base_color[2] += 0.1

    n_leaves = rng.randint(18, 35)
    max_len = rng.uniform(0.035, 0.055)   # длина внешних листьев
    max_w = rng.uniform(0.015, 0.025)      # ширина внешних листьев
    max_t = rng.uniform(0.006, 0.012)      # толщина

    angle_offset = rng.uniform(0, 2 * math.pi)

    for i in range(n_leaves):
        # t: 0 = внешний (первый), 1 = центральный (последний)
        t = i / max(n_leaves - 1, 1)

        # Размер уменьшается к центру
        scale = 1.0 - t * 0.7
        leaf_len = max_len * scale
        leaf_w = max_w * scale
        leaf_t = max_t * scale

        leaf = _make_teardrop_leaf(f"SuccLeaf_{i}", leaf_w, leaf_len, leaf_t, rng)

        # Цвет: внутренние светлее, кончики чуть краснее
        shift = t * 0.06
        c = (
            min(1, base_color[0] + shift + rng.uniform(-0.02, 0.02)),
            min(1, base_color[1] + shift * 0.5 + rng.uniform(-0.02, 0.02)),
            min(1, base_color[2] - shift * 0.3 + rng.uniform(-0.02, 0.02)),
            1.0,
        )
        leaf.data.materials.append(mat_leaf(rng, color=c))

        # Спираль Фибоначчи
        angle = i * _GOLDEN_ANGLE + angle_offset

        # Все листья растут от центра розетки
        dist = rng.uniform(0.002, 0.005)

        # Высота: внутренние выше (конус розетки)
        z = pot_top_z + t * 0.02

        leaf.location = (
            dist * math.cos(angle),
            dist * math.sin(angle),
            z,
        )

        # Наклон: внешние почти горизонтальные, внутренние более вертикальные
        tilt = rng.uniform(0.15, 0.4) + t * 0.7
        leaf.rotation_euler = (tilt, 0, angle - math.pi / 2)
        objects.append(leaf)

    return objects


# ============================================================
# Фикус (высокое дерево)
# ============================================================

def _make_ficus(rng, pot_top_z):
    """Фикус: ствол + крона из плоских листьев."""
    objects = []

    # Ствол
    trunk_h = rng.uniform(0.25, 0.45)
    trunk_r = rng.uniform(0.008, 0.015)
    trunk = create_cylinder("Trunk", trunk_r, trunk_h,
                            z_offset=pot_top_z, segments=12)
    trunk.data.materials.append(mat_trunk())
    objects.append(trunk)


    # Листья по стволу (верхние 2/3)
    n_leaves = rng.randint(12, 25)
    for i in range(n_leaves):
        t = rng.uniform(0.35, 1.0)  # позиция вдоль ствола
        z = pot_top_z + trunk_h * t
        angle = rng.uniform(0, 2 * math.pi)

        leaf_w = rng.uniform(0.03, 0.06)
        leaf_h = rng.uniform(0.05, 0.1)
        leaf = _make_leaf(f"FicusLeaf_{i}", leaf_w, leaf_h, rng)
        leaf.location = (trunk_r * math.cos(angle + math.pi/2), trunk_r * math.sin(angle + math.pi/2), z)
        # Листья свисают от ствола
        leaf.rotation_euler = (0, 0, angle)
        objects.append(leaf)

    return objects


# ============================================================
# Кактус
# ============================================================

def _make_cactus(rng, pot_top_z):
    """Кактус: шар или вытянутая сфера."""
    objects = []
    r = rng.uniform(0.025, 0.05)
    # Вытянутость: 1.0 = шар, до 2.5 = вытянутый вверх
    stretch = rng.uniform(1.0, 2.5)

    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=r)
    # Вытягиваем по Z
    if stretch != 1.0:
        for v in bm.verts:
            v.co.z *= stretch
    mesh = bpy.data.meshes.new("Cactus")
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.update()
    body = bpy.data.objects.new("Cactus", mesh)
    body.location = (0, 0, pot_top_z + r * stretch)
    body.data.materials.append(mat_cactus(rng))
    objects.append(body)

    return objects


# ============================================================
# Папоротник
# ============================================================

def _make_fern(rng, pot_top_z):
    """Папоротник: розетка длинных листьев свисающих вниз."""
    objects = []
    n_fronds = rng.randint(8, 15)
    color = rng.choice(GREEN_COLORS)

    for i in range(n_fronds):
        angle = 2 * math.pi * i / n_fronds + rng.uniform(-0.2, 0.2)
        # Длинный лист
        leaf_w = rng.uniform(0.015, 0.025)
        leaf_h = rng.uniform(0.1, 0.2)
        leaf = _make_leaf(f"Frond_{i}", leaf_w, leaf_h, rng)
        # Перезаписываем материал с общим цветом (± вариация)
        c = tuple(max(0, min(1, c + rng.uniform(-0.03, 0.03))) for c in color[:3]) + (1.0,)
        leaf.data.materials.clear()
        leaf.data.materials.append(mat_leaf(rng, color=c))

        dist = rng.uniform(0.002, 0.005)
        leaf.location = (dist * math.cos(angle), dist * math.sin(angle), pot_top_z + 0.01)
        # Свисают от центра, дугой вниз
        droop = rng.uniform(0.5, 1.2)
        leaf.rotation_euler = (droop, 0, angle + math.pi / 2)
        objects.append(leaf)

    return objects


# ============================================================
# API
# ============================================================

def generate_plant(seed, subtype='succulent'):
    """Генерирует растение в горшке. Возвращает список объектов."""
    rng = random.Random(seed)
    objects = []

    # Размер горшка зависит от типа
    if subtype == 'ficus':
        pot_radius = rng.uniform(0.06, 0.1)
        pot_height = rng.uniform(0.1, 0.16)
    elif subtype == 'cactus':
        pot_radius = rng.uniform(0.04, 0.07)
        pot_height = rng.uniform(0.05, 0.09)
    elif subtype == 'fern':
        pot_radius = rng.uniform(0.05, 0.08)
        pot_height = rng.uniform(0.07, 0.11)
    else:  # succulent
        pot_radius = rng.uniform(0.04, 0.06)
        pot_height = rng.uniform(0.04, 0.07)

    pot_objs, pot_top = make_random_pot("Pot", rng, pot_radius, pot_height)
    objects.extend(pot_objs)

    if subtype == 'succulent':
        objects.extend(_make_succulent(rng, pot_top))
    elif subtype == 'ficus':
        objects.extend(_make_ficus(rng, pot_top))
    elif subtype == 'cactus':
        objects.extend(_make_cactus(rng, pot_top))
    elif subtype == 'fern':
        objects.extend(_make_fern(rng, pot_top))

    return objects

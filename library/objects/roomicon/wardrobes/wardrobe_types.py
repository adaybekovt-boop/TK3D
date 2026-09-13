"""Генерация шкафов разных типов."""

import random
import math

from helpers import create_box, create_cylinder, mat_wood, mat_metal

WARDROBE_TYPES = {
    'single': {},
    'double': {},
    'with_drawers': {},
    'nightstand': {},
    'dresser': {},
}

PANEL_THICK = 0.02


def _make_body(name, hw, hd, height, wood):
    """Корпус шкафа: задняя стенка, бока, верх, дно."""
    objects = []
    pt = PANEL_THICK / 2

    # Задняя стенка
    back = create_box(f"{name}_Back", hw - pt*2, pt, height / 2 - pt*2)
    back.location = (0, -hd + pt, height / 2)
    back.data.materials.append(wood)
    objects.append(back)

    # Левая стенка
    left = create_box(f"{name}_Left", pt, hd, height / 2 - pt*2)
    left.location = (-hw + pt, 0, height / 2)
    left.data.materials.append(wood)
    objects.append(left)

    # Правая стенка
    right = create_box(f"{name}_Right", pt, hd, height / 2 - pt*2)
    right.location = (hw - pt, 0, height / 2)
    right.data.materials.append(wood)
    objects.append(right)

    # Дно
    bottom = create_box(f"{name}_Bottom", hw, hd, pt)
    bottom.location = (0, 0, pt)
    bottom.data.materials.append(wood)
    objects.append(bottom)

    # Верх
    top = create_box(f"{name}_Top", hw, hd, pt)
    top.location = (0, 0, height - pt)
    top.data.materials.append(wood)
    objects.append(top)

    return objects


def _make_doors(name, hw, hd, height, n_doors, wood, metal, rng):
    """Дверцы (фронтальные панели) + ручки."""
    objects = []
    door_gap = 0.003
    total_gap = door_gap * (n_doors + 1)
    door_w = (hw * 2 - PANEL_THICK * 2 - total_gap) / n_doors
    start_x = -hw + PANEL_THICK + door_gap

    handle_type = rng.choice(['knob', 'bar'])

    for i in range(n_doors):
        # Петля на внешнем краю двери: чётная — слева, нечётная — справа
        hinge_side = -1 if i % 2 == 0 else 1
        hinge_x = start_x + i * (door_w + door_gap) + (0 if hinge_side == -1 else door_w)
        # Смещаем геометрию от pivot (петли) в сторону двери
        cx = -hinge_side * door_w / 2
        door = create_box(f"{name}_Door{i}", door_w / 2, PANEL_THICK / 2, height / 2 - PANEL_THICK,
                           cx=cx)
        door.location = (hinge_x, hd - PANEL_THICK / 2, height / 2)
        door.data.materials.append(wood)
        objects.append(door)

        # Ручка — дочерний объект двери (координаты относительно pivot двери)
        # X ручки относительно pivot: у противоположного от петли края
        local_hx = -hinge_side * (door_w - 0.03)
        local_hz = 0  # середина двери по высоте

        if handle_type == 'knob':
            handle = create_cylinder(f"{name}_Handle{i}", 0.012, 0.015)
            handle.location = (local_hx, PANEL_THICK / 2 + 0.005, local_hz)
            handle.rotation_euler = (math.pi / 2, 0, 0)
        else:
            handle = create_box(f"{name}_Handle{i}", 0.008, 0.01, 0.05)
            handle.location = (local_hx, PANEL_THICK / 2 + 0.01, local_hz)
        handle.data.materials.append(metal)
        handle.parent = door
        objects.append(handle)

    return objects


def _make_shelves(name, hw, hd, height, n_shelves, wood):
    """Внутренние полки."""
    objects = []
    pt = PANEL_THICK
    usable_h = height - pt * 2
    spacing = usable_h / (n_shelves + 1)

    for i in range(n_shelves):
        sz = pt + spacing * (i + 1)
        shelf = create_box(f"{name}_Shelf{i}", hw - pt, hd - pt, pt / 2)
        shelf.location = (0, 0, sz)
        shelf.data.materials.append(wood)
        objects.append(shelf)

    return objects


def _make_drawers(name, hw, hd, height, n_drawers, drawer_zone_h, wood, metal, rng):
    """Ящики в нижней части."""
    objects = []
    drawer_gap = 0.005
    drawer_h = (drawer_zone_h - drawer_gap * (n_drawers + 1)) / n_drawers
    inner_w = hw * 2 - PANEL_THICK * 2 - 0.01

    for i in range(n_drawers):
        dz = PANEL_THICK + drawer_gap + i * (drawer_h + drawer_gap) + drawer_h / 2

        # Фасад ящика
        front = create_box(f"{name}_DrawerFront{i}", inner_w / 2, PANEL_THICK / 2, drawer_h / 2)
        front.location = (0, hd - PANEL_THICK / 2, dz)
        front.data.materials.append(wood)
        objects.append(front)

        # Ручка
        handle = create_box(f"{name}_DrawerHandle{i}", 0.04, 0.008, 0.008)
        handle.location = (0, hd + 0.005, dz)
        handle.data.materials.append(metal)
        objects.append(handle)

    return objects


# ============================================================
# Типы шкафов
# ============================================================

def _make_single(rng):
    """Одностворчатый шкаф."""
    width = rng.uniform(0.5, 0.7)
    depth = rng.uniform(0.45, 0.55)
    height = rng.uniform(1.8, 2.1)
    hw, hd = width / 2, depth / 2
    wood = mat_wood(rng)
    metal = mat_metal(rng)

    objects = _make_body("Single", hw, hd, height, wood)
    objects.extend(_make_doors("Single", hw, hd, height, 1, wood, metal, rng))
    objects.extend(_make_shelves("Single", hw, hd, height, rng.randint(3, 5), wood))
    return objects


def _make_double(rng):
    """Двустворчатый шкаф."""
    width = rng.uniform(1.0, 1.4)
    depth = rng.uniform(0.5, 0.6)
    height = rng.uniform(1.9, 2.2)
    hw, hd = width / 2, depth / 2
    wood = mat_wood(rng)
    metal = mat_metal(rng)

    objects = _make_body("Double", hw, hd, height, wood)
    objects.extend(_make_doors("Double", hw, hd, height, 2, wood, metal, rng))
    objects.extend(_make_shelves("Double", hw, hd, height, rng.randint(3, 5), wood))

    # Центральная перегородка
    divider = create_box("Double_Divider", PANEL_THICK / 2, hd - PANEL_THICK, height / 2 - PANEL_THICK)
    divider.location = (0, 0, height / 2)
    divider.data.materials.append(wood)
    objects.append(divider)

    return objects


def _make_with_drawers(rng):
    """Шкаф с ящиками внизу."""
    width = rng.uniform(1.0, 1.4)
    depth = rng.uniform(0.5, 0.6)
    height = rng.uniform(1.9, 2.2)
    drawer_zone = rng.uniform(0.35, 0.5)
    n_drawers = rng.randint(2, 3)

    hw, hd = width / 2, depth / 2
    wood = mat_wood(rng)
    metal = mat_metal(rng)

    # Двери в верхней части
    door_h = height - drawer_zone
    # Укорачиваем двери (пересоздаём)
    objects_clean = _make_body("Drawers", hw, hd, height, wood)
    inner_w = hw * 2 - PANEL_THICK * 2 - 0.01

    # Верхние двери (с pivot на петлях)
    door_gap = 0.003
    for i in range(2):
        door_w = (inner_w - door_gap * 3) / 2
        door_half_h = (door_h - PANEL_THICK * 2) / 2
        door_center_z = drawer_zone + door_h / 2

        hinge_side = -1 if i % 2 == 0 else 1
        hinge_x = -hw + PANEL_THICK + door_gap + i * (door_w + door_gap) + (0 if hinge_side == -1 else door_w)
        cx = -hinge_side * door_w / 2

        door = create_box(f"Drawers_Door{i}", door_w / 2, PANEL_THICK / 2,
                           door_half_h, cx=cx)
        door.location = (hinge_x, hd - PANEL_THICK / 2, door_center_z)
        door.data.materials.append(wood)
        objects_clean.append(door)

        # Ручка — дочерний объект двери
        local_hx = -hinge_side * (door_w - 0.03)
        local_hz = 0  # центр двери по Z
        handle = create_box(f"Drawers_DHandle{i}", 0.008, 0.01, 0.05)
        handle.location = (local_hx, PANEL_THICK / 2 + 0.01, local_hz)
        handle.data.materials.append(metal)
        handle.parent = door
        objects_clean.append(handle)

    # Разделительная полка
    divider_shelf = create_box("Drawers_DivShelf", hw - PANEL_THICK, hd - PANEL_THICK, PANEL_THICK / 2)
    divider_shelf.location = (0, 0, drawer_zone)
    divider_shelf.data.materials.append(wood)
    objects_clean.append(divider_shelf)

    # Ящики
    objects_clean.extend(_make_drawers("Drawers", hw, hd, height, n_drawers, drawer_zone, wood, metal, rng))

    return objects_clean


def _make_nightstand(rng):
    """Тумбочка: 1-2 ящика, иногда дверца."""
    width = rng.uniform(0.38, 0.50)
    depth = rng.uniform(0.35, 0.42)
    height = rng.uniform(0.45, 0.60)
    hw, hd = width / 2, depth / 2
    wood = mat_wood(rng)
    metal = mat_metal(rng)

    objects = _make_body("Nightstand", hw, hd, height, wood)

    # Legs
    leg_h = rng.uniform(0.06, 0.12)
    leg_r = 0.015
    for sx in (-1, 1):
        for sy in (-1, 1):
            leg = create_cylinder(f"Nightstand_Leg_{sx}_{sy}", leg_r, leg_h / 2)
            leg.location = (sx * (hw - 0.03), sy * (hd - 0.03), leg_h / 2)
            leg.data.materials.append(wood)
            objects.append(leg)

    # Move body up by leg height
    for obj in objects[:5]:  # body parts
        obj.location.z += leg_h

    usable_h = height - PANEL_THICK * 2
    variant = rng.choice(['drawers', 'door_drawer'])
    if variant == 'drawers':
        n_drawers = rng.randint(1, 2)
        obj_before = len(objects)
        objects.extend(_make_drawers("Nightstand", hw, hd, height,
                                      n_drawers, usable_h, wood, metal, rng))
        for obj in objects[obj_before:]:
            obj.location.z += leg_h
    else:
        # Top drawer + door below
        drawer_zone = usable_h * 0.3
        door_zone = usable_h - drawer_zone

        # Door (lower part)
        inner_w = width - PANEL_THICK * 2 - 0.006
        door_visual_h = door_zone - 0.005
        # Pivot at left hinge edge
        door = create_box(f"Nightstand_Door", inner_w / 2, PANEL_THICK / 2,
                           door_visual_h / 2, cx=inner_w / 2)
        door.location = (-hw + PANEL_THICK + 0.003, hd - PANEL_THICK / 2,
                          leg_h + PANEL_THICK + door_visual_h / 2)
        door.data.materials.append(wood)
        objects.append(door)

        handle = create_box(f"Nightstand_DoorHandle", 0.008, 0.008, 0.03)
        handle.location = (inner_w - 0.03, PANEL_THICK / 2 + 0.008, 0)
        handle.data.materials.append(metal)
        handle.parent = door
        objects.append(handle)

        # Drawer (upper part)
        obj_before = len(objects)
        objects.extend(_make_drawers("Nightstand", hw, hd, height,
                                      1, drawer_zone, wood, metal, rng))
        for obj in objects[obj_before:]:
            obj.location.z += leg_h + door_zone

    return objects


def _make_dresser(rng):
    """Комод: 3-5 ящиков, средняя высота."""
    width = rng.uniform(0.80, 1.20)
    depth = rng.uniform(0.40, 0.50)
    height = rng.uniform(0.75, 1.00)
    n_drawers = rng.randint(3, 5)
    hw, hd = width / 2, depth / 2
    wood = mat_wood(rng)
    metal = mat_metal(rng)

    objects = _make_body("Dresser", hw, hd, height, wood)

    # Legs
    leg_h = rng.uniform(0.05, 0.10)
    leg_r = 0.018
    for sx in (-1, 1):
        for sy in (-1, 1):
            leg = create_cylinder(f"Dresser_Leg_{sx}_{sy}", leg_r, leg_h / 2)
            leg.location = (sx * (hw - 0.04), sy * (hd - 0.04), leg_h / 2)
            leg.data.materials.append(wood)
            objects.append(leg)

    # Move body up
    for obj in objects[:5]:
        obj.location.z += leg_h

    # All drawers
    usable_h = height - PANEL_THICK * 2
    objects.extend(_make_drawers("Dresser", hw, hd, height + leg_h,
                                  n_drawers, usable_h, wood, metal, rng))
    # Shift drawers up
    for obj in objects[5 + 4:]:
        if 'Drawer' in obj.name:
            obj.location.z += leg_h

    return objects


# ============================================================
# API
# ============================================================

def generate_wardrobe(seed, subtype='double'):
    rng = random.Random(seed)
    if subtype == 'single':
        return _make_single(rng)
    elif subtype == 'double':
        return _make_double(rng)
    elif subtype == 'with_drawers':
        return _make_with_drawers(rng)
    elif subtype == 'nightstand':
        return _make_nightstand(rng)
    elif subtype == 'dresser':
        return _make_dresser(rng)
    else:
        return _make_double(rng)

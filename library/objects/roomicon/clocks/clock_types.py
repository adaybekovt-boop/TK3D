"""Генерация часов: настенные, настольные, напольные."""

import bpy
import bmesh
import math
import random

from helpers import (
    create_cylinder, create_box, create_clock_face, create_hands, create_glass_cover,
    mat_clock_body, mat_clock_face, mat_clock_hands, mat_clock_glass,
    BODY_STYLES, FACE_COLORS, HANDS_COLORS,
)


CLOCK_TYPES = {
    'round': {},
    'square': {},
    'alarm': {},
    'grandfather': {},
}

# Маппинг тип → asset категория
ASSET_CATEGORIES = {
    'round': 'wall',
    'square': 'wall',
    'alarm': 'tabletop',
    'grandfather': 'wall_floor',  # пристенный напольный
}


def _assign_materials(objects, body_mat, face_mat, hands_mat, glass_mat):
    """Назначает материалы объектам по имени."""
    for obj in objects:
        name = obj.name.lower()
        if 'glass' in name or 'cover' in name:
            obj.data.materials.append(glass_mat)
        elif 'face' in name:
            obj.data.materials.append(face_mat)
        elif 'tick' in name or 'hand' in name or 'hour' in name or 'minute' in name or 'hub' in name:
            obj.data.materials.append(hands_mat)
        else:
            obj.data.materials.append(body_mat)


def _random_time(rng):
    return rng.randint(0, 11), rng.randint(0, 59)


def _pick_materials(rng):
    style, body_color = rng.choice(BODY_STYLES)
    face_color = rng.choice(FACE_COLORS)
    hands_color = rng.choice(HANDS_COLORS)
    return (
        mat_clock_body(style, body_color),
        mat_clock_face(face_color),
        mat_clock_hands(hands_color),
        mat_clock_glass(),
    )


# ============================================================
# Настенные круглые
# ============================================================

def _make_round_wall(rng):
    """Круглые настенные часы. Origin — центр задней стороны (для крепления на стену)."""
    radius = rng.uniform(0.12, 0.18)
    depth = rng.uniform(0.025, 0.04)
    rim_width = rng.uniform(0.01, 0.02)

    objects = []

    # Корпус — кольцо (внешний цилиндр)
    body = create_cylinder("ClockBody", radius, depth, z_offset=0)
    body.rotation_euler = (math.pi / 2, 0, 0)
    objects.append(body)

    # Задняя стенка
    back = create_cylinder("ClockBack", radius - rim_width, 0.003, z_offset=0)
    back.rotation_euler = (math.pi / 2, 0, 0)
    back.location = (0, 0.001, 0)
    objects.append(back)

    # Циферблат
    face_objs = create_clock_face("Clock", radius - rim_width, depth, rng)
    for obj in face_objs:
        obj.location.y += depth * 0.3
    objects.extend(face_objs)

    # Стрелки
    hour, minute = _random_time(rng)
    hand_objs = create_hands("Clock", radius - rim_width, depth, hour, minute)
    objects.extend(hand_objs)

    # Стекло
    glass = create_glass_cover("ClockGlass", radius - rim_width, depth)
    objects.append(glass)

    body_mat, face_mat, hands_mat, glass_mat = _pick_materials(rng)
    _assign_materials(objects, body_mat, face_mat, hands_mat, glass_mat)

    return objects


# ============================================================
# Настенные квадратные
# ============================================================

def _make_square_wall(rng):
    """Квадратные настенные часы."""
    size = rng.uniform(0.13, 0.2)
    depth = rng.uniform(0.025, 0.04)
    face_radius = size * 0.85  # циферблат вписан в квадрат

    objects = []

    # Корпус — бокс
    body = create_box("ClockBody", size / 2, depth / 2, size / 2,
                       cy=-0.6*depth / 2)
    objects.append(body)

    # Циферблат
    face_objs = create_clock_face("Clock", face_radius, depth, rng)
    for obj in face_objs:
        obj.location.y += depth * 0.3
    objects.extend(face_objs)

    # Стрелки
    hour, minute = _random_time(rng)
    hand_objs = create_hands("Clock", face_radius, depth, hour, minute)
    objects.extend(hand_objs)

    # Стекло
    glass = create_glass_cover("ClockGlass", face_radius, depth)
    objects.append(glass)

    body_mat, face_mat, hands_mat, glass_mat = _pick_materials(rng)
    _assign_materials(objects, body_mat, face_mat, hands_mat, glass_mat)

    return objects


# ============================================================
# Настольный будильник
# ============================================================

def _make_alarm(rng):
    """Настольный будильник: круглый корпус на ножках."""
    radius = rng.uniform(0.04, 0.06)
    depth = rng.uniform(0.007, 0.014)
    depth_c = rng.uniform(0.025, 0.035)
    leg_h = rng.uniform(0.001, 0.01)
    leg_r = 0.004

    objects = []

    # Ножки (2 штуки)
    for side in (-1, 1):
        leg = create_cylinder(f"ClockLeg_{side}", leg_r, leg_h*3)
        leg.location = (side * radius * 0.5, -depth/2, 0)
        objects.append(leg)

    # Корпус
    body = create_cylinder("ClockBody", radius, depth_c, z_offset=0)
    body.rotation_euler = (math.pi / 2, 0, 0)
    body.location = (0, 0, leg_h + radius)
    objects.append(body)

    # Циферблат
    face_objs = create_clock_face("Clock", radius * 0.9, depth, rng)
    for obj in face_objs:
        obj.location.y += depth * 0.3
        obj.location.z += leg_h + radius
    objects.extend(face_objs)

    # Стрелки
    hour, minute = _random_time(rng)
    hand_objs = create_hands("Clock", radius * 0.9, depth / 2, hour, minute)
    for obj in hand_objs:
        obj.location.z += leg_h + radius
    objects.extend(hand_objs)

    # Стекло
    glass = create_glass_cover("ClockGlass", radius * 0.9, depth)
    glass.location.z += leg_h + radius
    objects.append(glass)

    # «Колокольчик» сверху
    bell_r = radius * rng.uniform(0.15, 0.25)
    bell = create_cylinder("ClockBell", bell_r, bell_r * 1.5)
    bell.location = (0, -depth, leg_h + radius * 2 - bell_r * 0.3)
    objects.append(bell)

    body_mat, face_mat, hands_mat, glass_mat = _pick_materials(rng)
    _assign_materials(objects, body_mat, face_mat, hands_mat, glass_mat)

    return objects


# ============================================================
# Напольные (grandfather)
# ============================================================

def _make_grandfather(rng):
    """Напольные часы с маятником. Высокий корпус."""
    width = rng.uniform(0.25, 0.35)
    depth = rng.uniform(0.15, 0.2)
    total_h = rng.uniform(1.6, 2.0)
    face_radius = width * 0.35
    depth_numbers = rng.uniform(0.01,0.03)

    top_h = total_h * 0.3     # верхняя секция (циферблат)
    mid_h = total_h * 0.5     # средняя (маятник)
    base_h = total_h * 0.2    # основание

    objects = []

    hw = width / 2
    hd = depth / 2

    # Основание (чуть шире)
    base = create_box("ClockBase", hw * 1.05, hd * 1.05, base_h / 2,
                       cz=base_h / 2)
    objects.append(base)

    # Средняя секция
    mid_l = create_box("ClockMid_l", hw/10, hd, mid_h / 2, cz=base_h + mid_h / 2,cx=hw*0.9)
    objects.append(mid_l)
    mid_r = create_box("ClockMid_r", hw/10, hd, mid_h / 2, cz=base_h + mid_h / 2,cx=-hw*0.9)
    objects.append(mid_r)
    mid_back = create_box("ClockMid_b", hw, hd/40, mid_h / 2, cz=base_h + mid_h / 2,cy=-hd - hd/40)
    objects.append(mid_back)
    mid_top = create_box("ClockMid_t", hw*.8, hd, mid_h / 10)
    mid_top.location = (0,0,total_h * 0.65)
    objects.append(mid_top)

    mid_bot = create_box("ClockMid_bb", hw*.8, hd, mid_h / 10)
    mid_bot.location = (0,0,total_h * 0.25)
    objects.append(mid_bot)

    # Верхняя секция (чуть шире, с карнизом)
    top_z = base_h + mid_h
    top = create_box("ClockTop", hw * 1.02, hd * 1.02, top_h / 2,
                      cz=top_z + top_h / 2)
    objects.append(top)

    # Циферблат (на фронтальной стороне верхней секции)
    face_center_z = top_z + top_h * 0.5
    face_objs = create_clock_face("Clock", face_radius, depth_numbers, rng)
    for obj in face_objs:
        obj.location = (0, hd + 0.001, face_center_z)
    objects.extend(face_objs)

    # Стрелки
    hour, minute = _random_time(rng)
    hand_objs = create_hands("Clock", face_radius, depth_numbers/2, hour, minute)
    for obj in hand_objs:
        obj.location.z += face_center_z
        obj.location.y += hd
    objects.extend(hand_objs)

    # Стекло циферблата
    glass = create_glass_cover("ClockGlass", face_radius, depth)
    glass.location = (0, hd + depth_numbers/2, face_center_z)
    objects.append(glass)

    # Маятник
    pendulum_len = mid_h * 0.5
    pendulum_z = base_h + mid_h * 0.8
    # Стержень
    pn_rad = rng.uniform(0.003,0.01)
    rod = create_cylinder("ClockRod", pn_rad, pendulum_len, z_offset=pendulum_z - pendulum_len)
    objects.append(rod)
    # Диск маятника
    disk_r = rng.uniform(0.03, 0.05)
    disk = create_cylinder("ClockDisk", disk_r,pn_rad*2.2, z_offset=0)
    disk.location = (0, pn_rad*1.1, pendulum_z - pendulum_len)
    disk.rotation_euler = (math.pi/2,0,0)
    objects.append(disk)

    disk2 = create_cylinder("ClockDisk2", disk_r*0.8,pn_rad*1.2, z_offset=0)
    disk2.location = (0, pn_rad*2, pendulum_z - pendulum_len)
    disk2.rotation_euler = (math.pi/2,0,0)
    objects.append(disk2)

    # Стекло на средней секции (чтобы маятник был виден)
    mid_glass = create_box("ClockMidGlass", hw * 0.8, 0.002, total_h*0.15)
    mid_glass.location = (0,hd , total_h*0.45)
    objects.append(mid_glass)

    body_mat, face_mat, hands_mat, glass_mat = _pick_materials(rng)
    # Напольные — обычно дерево
    body_mat = mat_clock_body('wood', rng.choice([
        (0.4, 0.25, 0.12, 1.0), (0.3, 0.18, 0.08, 1.0), (0.55, 0.38, 0.2, 1.0)
    ]))
    _assign_materials(objects, body_mat, face_mat, hands_mat, glass_mat)

    return objects


# ============================================================
# API
# ============================================================

def generate_clock(seed, subtype='round'):
    rng = random.Random(seed)
    if subtype == 'round':
        return _make_round_wall(rng)
    elif subtype == 'square':
        return _make_square_wall(rng)
    elif subtype == 'alarm':
        return _make_alarm(rng)
    elif subtype == 'grandfather':
        return _make_grandfather(rng)
    else:
        return _make_round_wall(rng)

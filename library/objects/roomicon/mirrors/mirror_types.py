"""Генерация зеркал разных типов."""

import random
import math

from helpers import (
    create_box, create_rect_plane, create_circle_plane, create_oval_plane,
    create_arch_plane, create_circle_frame,
    mat_mirror, mat_frame,
)

MIRROR_TYPES = {
    'rectangle': {},
    'round': {},
    'oval': {},
    'arched': {},
    'with_shelf': {},
}


def _rect_frame(name, hw, hh, frame_w, frame_d, rng):
    """Прямоугольная рамка из 4 боксов."""
    frame_mat = mat_frame(rng)
    hfw = frame_w / 2
    hfd = frame_d / 2
    objects = []

    parts = [
        (f"{name}_Top", hw + frame_w, hfd, hfw, 0, hfd, hh + hfw),
        (f"{name}_Bot", hw + frame_w, hfd, hfw, 0, hfd, -hh - hfw),
        (f"{name}_Left", hfw, hfd, hh, -hw - hfw, hfd, 0),
        (f"{name}_Right", hfw, hfd, hh, hw + hfw, hfd, 0),
    ]
    for pname, sx, sy, sz, cx, cy, cz in parts:
        obj = create_box(pname, sx, sy, sz)
        obj.location = (cx, cy, cz)
        obj.data.materials.append(frame_mat)
        objects.append(obj)

    return objects, frame_mat


def _bevel_rect_frame(name, hw, hh, frame_w, frame_d, rng):
    """Прямоугольная рамка с Bevel (багетная)."""
    frame_mat = mat_frame(rng)
    hfw = frame_w / 2
    hfd = frame_d / 2
    bevel_w = rng.uniform(0.005, 0.012)
    objects = []

    parts = [
        (f"{name}_Top", hw + frame_w, hfd, hfw, 0, hfd, hh + hfw),
        (f"{name}_Bot", hw + frame_w, hfd, hfw, 0, hfd, -hh - hfw),
        (f"{name}_Left", hfw, hfd, hh + frame_w, -hw - hfw, hfd, 0),
        (f"{name}_Right", hfw, hfd, hh + frame_w, hw + hfw, hfd, 0),
    ]
    for pname, sx, sy, sz, cx, cy, cz in parts:
        obj = create_box(pname, sx, sy, sz)
        obj.location = (cx, cy, cz)
        bev = obj.modifiers.new("Bevel", 'BEVEL')
        bev.width = bevel_w
        bev.segments = 3
        bev.limit_method = 'ANGLE'
        bev.angle_limit = math.radians(60)
        obj.data.materials.append(frame_mat)
        objects.append(obj)

    return objects, frame_mat


# ============================================================
# Типы зеркал
# ============================================================

def _make_rectangle(rng):
    """Прямоугольное зеркало."""
    width = rng.uniform(0.4, 0.7)
    height = rng.uniform(0.5, 0.9)
    frame_w = rng.uniform(0.02, 0.04)
    frame_d = rng.uniform(0.015, 0.025)
    hw, hh = width / 2, height / 2

    objects = []

    # Зеркальная поверхность
    mirror = create_rect_plane("MirrorGlass", hw, hh)
    mirror.data.materials.append(mat_mirror())
    objects.append(mirror)

    # Задник
    back = create_box("MirrorBack", hw + 0.005, 0.003, hh + 0.005)
    back.location = (0, -0.005, 0)
    back_mat = mat_frame(rng)
    back.data.materials.append(back_mat)
    objects.append(back)

    # Рамка
    use_bevel = rng.random() < 0.4
    if use_bevel:
        frame_objs, _ = _bevel_rect_frame("Frame", hw, hh, frame_w, frame_d, rng)
    else:
        frame_objs, _ = _rect_frame("Frame", hw, hh, frame_w, frame_d, rng)
    objects.extend(frame_objs)

    return objects


def _make_round(rng):
    """Круглое зеркало."""
    radius = rng.uniform(0.2, 0.4)
    frame_w = rng.uniform(0.015, 0.035)
    frame_d = rng.uniform(0.015, 0.025)

    objects = []

    mirror = create_circle_plane("MirrorGlass", radius)
    mirror.data.materials.append(mat_mirror())
    objects.append(mirror)

    # Задник
    back = create_circle_plane("MirrorBack", radius + 0.005)
    back.location = (0, -0.005, 0)
    back.data.materials.append(mat_frame(rng))
    objects.append(back)

    # Рамка-кольцо
    frame = create_circle_frame("MirrorFrame", radius, frame_w, frame_d)
    frame.data.materials.append(mat_frame(rng))
    objects.append(frame)

    return objects


def _make_oval(rng):
    """Овальное зеркало."""
    rx = rng.uniform(0.2, 0.35)
    rz = rng.uniform(0.3, 0.5)
    frame_w = rng.uniform(0.015, 0.03)
    frame_d = rng.uniform(0.015, 0.025)

    objects = []

    mirror = create_oval_plane("MirrorGlass", rx, rz)
    mirror.data.materials.append(mat_mirror())
    objects.append(mirror)

    # Задник
    back = create_oval_plane("MirrorBack", rx + 0.005, rz + 0.005)
    back.location = (0, -0.005, 0)
    back.data.materials.append(mat_frame(rng))
    objects.append(back)

    # Рамка — используем circle_frame с масштабированием по Z (упрощение)
    frame = create_circle_frame("MirrorFrame", rx, frame_w, frame_d)
    frame.scale = (1.0, 1.0, rz / rx)
    frame.data.materials.append(mat_frame(rng))
    objects.append(frame)

    return objects


def _make_arched(rng):
    """Прямоугольное с арочным верхом."""
    width = rng.uniform(0.4, 0.6)
    height = rng.uniform(0.7, 1.0)
    frame_w = rng.uniform(0.02, 0.04)
    frame_d = rng.uniform(0.015, 0.025)
    hw = width / 2
    hh = height / 2

    objects = []

    mirror = create_arch_plane("MirrorGlass", hw, hh, arch_r=hw)
    mirror.data.materials.append(mat_mirror())
    objects.append(mirror)

    # Задник
    back = create_arch_plane("MirrorBack", hw + 0.005, hh + 0.005, arch_r=hw + 0.005)
    back.location = (0, -0.005, 0)
    back.data.materials.append(mat_frame(rng))
    objects.append(back)

    # Рамка — упрощённо из боксов (только боковые + низ)
    frame_mat = mat_frame(rng)
    hfw = frame_w / 2
    hfd = frame_d / 2

    # Низ
    bot = create_box("Frame_Bot", hw + frame_w, hfd, hfw)
    bot.location = (0, hfd, -hh - hfw)
    bot.data.materials.append(frame_mat)
    objects.append(bot)

    # Бока (до начала арки)
    rect_h = hh - hw  # прямая часть
    if rect_h > 0:
        for sx, sname in [(-1, "Left"), (1, "Right")]:
            side = create_box(f"Frame_{sname}", hfw, hfd, rect_h / 2)
            side.location = (sx * (hw + hfw), hfd, -hh + rect_h / 2)
            side.data.materials.append(frame_mat)
            objects.append(side)

    return objects


def _make_with_shelf(rng):
    """Прямоугольное зеркало с маленькой полкой внизу."""
    width = rng.uniform(0.4, 0.6)
    height = rng.uniform(0.5, 0.7)
    frame_w = rng.uniform(0.02, 0.035)
    frame_d = rng.uniform(0.015, 0.025)
    hw, hh = width / 2, height / 2

    shelf_depth = rng.uniform(0.08, 0.12)
    shelf_thick = 0.012

    objects = []

    # Зеркало
    mirror = create_rect_plane("MirrorGlass", hw, hh)
    mirror.data.materials.append(mat_mirror())
    objects.append(mirror)

    # Задник
    back = create_box("MirrorBack", hw + 0.005, 0.003, hh + 0.005)
    back.location = (0, -0.005, 0)
    back.data.materials.append(mat_frame(rng))
    objects.append(back)

    # Рамка
    frame_objs, frame_mat = _rect_frame("Frame", hw, hh, frame_w, frame_d, rng)
    objects.extend(frame_objs)

    # Полка
    shelf = create_box("MirrorShelf", hw + frame_w, shelf_depth / 2, shelf_thick / 2)
    shelf.location = (0, shelf_depth / 2, -hh - frame_w - shelf_thick / 2)
    shelf.data.materials.append(frame_mat)
    objects.append(shelf)

    return objects


# ============================================================
# API
# ============================================================

def generate_mirror(seed, subtype='rectangle'):
    rng = random.Random(seed)
    if subtype == 'rectangle':
        return _make_rectangle(rng)
    elif subtype == 'round':
        return _make_round(rng)
    elif subtype == 'oval':
        return _make_oval(rng)
    elif subtype == 'arched':
        return _make_arched(rng)
    elif subtype == 'with_shelf':
        return _make_with_shelf(rng)
    else:
        return _make_rectangle(rng)

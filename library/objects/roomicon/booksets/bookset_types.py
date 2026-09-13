"""Генерация наборов книг."""

import bpy
import random
import math

from helpers import (create_box, mat_cover, mat_pages,
                     create_page_block)

BOOKSET_TYPES = {
    'single': {},
    'row': {},
    'stack': {},
    'leaning': {},
}


def _make_single_book(name, height, width, thickness, rng, cover_mat=None):
    """
    Создаёт книгу, сгруппированную под Empty.

    Всегда строит стоячую книгу (толщина по X, ширина по Y, высота по Z),
    центрированную в origin Empty. Для лежачих книг/наклона вызывающий код
    поворачивает Empty.

    Возвращает [empty, ...children].
    """
    pages_mat = mat_pages()
    if cover_mat is None:
        cover_mat = mat_cover(rng)

    ht = thickness / 2
    hw = width / 2
    hh = height / 2

    # Страницы чуть меньше обложки
    pages_t = thickness * 0.88
    pages_w = width * 0.95
    back_shift = width * 0.025
    cover_t = 0.001
    segments = rng.randint(15, 40)

    children = []

    # Блок страниц
    pages = create_page_block(f"{name}_Pages",
                               pages_t, pages_w, height * 0.96,
                               rng, segments, back_shift)
    pages.data.materials.append(pages_mat)
    children.append(pages)

    # Передняя крышка (+X)
    front_cover = create_box(f"{name}_FrontCover", cover_t / 2, hw, hh)
    front_cover.location = (pages_t / 2 + cover_t / 2, 0, 0)
    front_cover.data.materials.append(cover_mat)
    children.append(front_cover)

    # Задняя крышка (-X)
    back_cover = create_box(f"{name}_BackCover", cover_t / 2, hw, hh)
    back_cover.location = (-pages_t / 2 - cover_t / 2, 0, 0)
    back_cover.data.materials.append(cover_mat)
    children.append(back_cover)

    # Корешок (-Y, ширина = расстояние между крышками)
    spine_half_x = pages_t / 2 + cover_t
    spine = create_box(f"{name}_Spine", spine_half_x, cover_t / 2, hh)
    spine.location = (0, -hw, 0)
    spine.data.materials.append(cover_mat)
    children.append(spine)

    # Empty-родитель
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_size = 0.01
    empty.empty_display_type = 'PLAIN_AXES'
    for child in children:
        child.parent = empty

    # Реальная полуширина книги по X (для позиционирования)
    empty['half_thickness'] = pages_t / 2 + cover_t

    return [empty] + children


# ============================================================
# Ряд вертикальных книг
# ============================================================

def _make_row(rng, max_height=None, max_width=None):
    n_books = rng.randint(5, 12)
    if max_width:
        # Ограничиваем количество книг шириной полки
        avg_t = 0.025
        n_books = min(n_books, max(2, int(max_width / avg_t)))
    objects = []

    h_max = min(0.28, max_height - 0.01) if max_height else 0.28
    h_min = min(0.18, h_max - 0.02)

    x_cursor = 0
    for i in range(n_books):
        h = rng.uniform(h_min, h_max)
        w = rng.uniform(0.12, 0.17)
        t = rng.uniform(0.015, 0.035)

        book_objs = _make_single_book(f"Book_{i}", h, w, t, rng)
        empty = book_objs[0]
        half_t = empty['half_thickness']
        empty.location = (x_cursor + half_t, 0, h / 2)
        objects.extend(book_objs)

        x_cursor += half_t * 2 + rng.uniform(0.0001, 0.0003)

    # Центрируем по X
    total_w = x_cursor
    for obj in objects:
        if obj.parent is None:  # только Empty-родители
            obj.location = (obj.location[0] - total_w / 2, obj.location[1], obj.location[2])

    return objects

# ============================================================
# Одна книга
# ============================================================

def _make_single(rng):
    return _make_stack(rng,True)


# ============================================================
# Горизонтальная стопка
# ============================================================

def _make_stack(rng,single=False):
    if single:
        n_books = 1
        angle_diff = 1
    else:
        n_books = rng.randint(2, 5)
        angle_diff = .15
    objects = []

    z_cursor = 0
    for i in range(n_books):
        h = rng.uniform(0.19, 0.26)
        w = rng.uniform(0.13, 0.17)
        t = rng.uniform(0.015, 0.03)

        book_objs = _make_single_book(f"StackBook_{i}", h, w, t, rng)
        empty = book_objs[0]

        # Случайное смещение и лёгкий поворот
        dx = rng.uniform(-0.01, 0.01)
        dy = rng.uniform(-0.01, 0.01)
        angle = rng.uniform(-angle_diff, angle_diff)

        # Поворот -90° по X → книга ложится (Z становится толщиной)
        empty.location = (dx, dy, z_cursor + t / 2)
        empty.rotation_euler = (0, math.pi / 2, angle)
        objects.extend(book_objs)

        z_cursor += t + 0.0001

    return objects


# ============================================================
# Ряд с наклоном
# ============================================================

def _make_leaning(rng, max_height=None, max_width=None):
    """Ряд книг, последние 1-3 наклонены (как без bookend)."""
    n_books = rng.randint(4, 8)
    if max_width:
        avg_t = 0.025
        n_books = min(n_books, max(2, int(max_width / avg_t)))
    n_leaning = 1
    objects = []

    h_max = min(0.25, max_height - 0.01) if max_height else 0.25
    h_min = min(0.19, h_max - 0.02)

    x_cursor = 0
    last_h = False
    for i in range(n_books):
        h = rng.uniform(h_min, h_max)
        w = rng.uniform(0.12, 0.17)
        t = rng.uniform(0.015, 0.035)

        book_objs = _make_single_book(f"LeanBook_{i}", h, w, t, rng)
        empty = book_objs[0]
        half_t = empty['half_thickness']

        # Наклон последних книг (поворот Empty по Y)
        if i >= n_books - n_leaning:
            lean_angle = rng.uniform(0.03, 0.20) * (1 + (i - (n_books - n_leaning)) * 0.3)
            contact_h = min(h,last_h)
            ex = math.sin(lean_angle) * contact_h / 2
            ez = half_t * math.sin(lean_angle)/2 + h / 2 * math.cos(lean_angle)
            empty.location = (x_cursor + half_t + ex, 0, ez)
        else:
            lean_angle = 0
            empty.location = (x_cursor + half_t, 0, h / 2)

        if lean_angle > 0:
            empty.rotation_euler = (0, -lean_angle, 0)
        objects.extend(book_objs)

        x_cursor += half_t * 2 + 0.0001
        last_h = h

    total_w = x_cursor
    for obj in objects:
        if obj.parent is None:
            obj.location = (obj.location[0] - total_w / 2, obj.location[1], obj.location[2])

    return objects


# ============================================================
# API
# ============================================================

def generate_bookset(seed, subtype='row', max_height=None, max_width=None):
    rng = random.Random(seed)
    if subtype == 'single':
        return _make_single(rng)
    if subtype == 'row':
        return _make_row(rng, max_height=max_height, max_width=max_width)
    elif subtype == 'stack':
        return _make_stack(rng)
    elif subtype == 'leaning':
        return _make_leaning(rng, max_height=max_height, max_width=max_width)
    else:
        return _make_row(rng, max_height=max_height, max_width=max_width)

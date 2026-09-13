"""Генерация фоторамок — настольные (с подставкой) и настенные (маленькие)."""

import random
import math

from helpers import (
    create_canvas, create_box, create_stand,
    frame_simple, frame_bevel,
    get_image_aspect, mat_canvas, mat_frame, mat_backing,
)


PHOTOFRAME_TYPES = {
    'tabletop_simple': {},
    'tabletop_bevel': {},
    'wall_simple': {},
    'wall_bevel': {},
}


def _make_photo(rng, image_path, frame_style, with_stand):
    """Общая логика: фото + рамка + опц. подставка."""
    objects = []

    # Размер фоторамки (маленькая)
    max_width = rng.uniform(0.1, 0.2)

    # Определяем пропорции из изображения
    if image_path:
        _, _, aspect = get_image_aspect(image_path)
    else:
        # Стандартные пропорции фото (3:2 или 4:3)
        aspect = rng.choice([1.5, 1.33, 1.0, 0.75, 0.67])

    canvas_w = max_width
    canvas_h = canvas_w / aspect if aspect > 0 else canvas_w

    # Ограничиваем
    if canvas_h > 0.25:
        canvas_h = 0.25
        canvas_w = canvas_h * aspect

    # Холст с фото
    canvas = create_canvas("Photo", canvas_w, canvas_h)
    if image_path:
        canvas.data.materials.append(mat_canvas(image_path))
    else:
        # Серая заглушка
        from common.shared_materials import get_or_create_mat, setup_principled
        placeholder = get_or_create_mat("M_PhotoPlaceholder")
        setup_principled(placeholder, (0.7, 0.7, 0.7, 1.0), roughness=0.5)
        canvas.data.materials.append(placeholder)
    objects.append(canvas)

    # Задник (чуть больше холста)
    backing = create_box("Backing", canvas_w / 2 + 0.002, 0.002, canvas_h / 2 + 0.002)
    backing.location = (0, -0.003, 0)
    backing.data.materials.append(mat_backing())
    objects.append(backing)

    # Рамка
    frame_mat = mat_frame(rng)
    if frame_style == 'bevel':
        frame_objs = frame_bevel("Frame", canvas_w, canvas_h, rng)
    else:
        frame_objs = frame_simple("Frame", canvas_w, canvas_h, rng)
    for obj in frame_objs:
        obj.data.materials.append(frame_mat)
    objects.extend(frame_objs)

    # Для настольных: наклоняем рамку назад и добавляем подставку
    if with_stand:
        tilt = rng.uniform(math.radians(8), math.radians(15))
        cos_t = math.cos(tilt)
        sin_t = math.sin(tilt)

        # Наклон только рамки (без подставки)
        for obj in objects:
            obj.rotation_euler = (tilt, 0, 0)

        # Вычисляем фактический нижний край после поворота
        # (учитываем вершины всех мешей + location каждого объекта)
        min_z = 0
        for obj in objects:
            ly, lz = obj.location[1], obj.location[2]
            for v in obj.data.vertices:
                wy = v.co.y + ly
                wz = v.co.z + lz
                rz = wy * sin_t + wz * cos_t
                if rz < min_z:
                    min_z = rz
        lift = -min_z

        for obj in objects:
            obj.location = (obj.location[0], obj.location[1], obj.location[2] + lift)

        # Вычисляем мировую позицию точки крепления подставки
        # на задней стороне рамки (~30% вверх от центра)
        attach_z_local = canvas_h * 0.3
        back_y = -0.005  # задняя стенка
        attach_y = back_y * cos_t - attach_z_local * sin_t
        attach_z = back_y * sin_t + attach_z_local * cos_t + lift

        stand = create_stand("Stand", attach_y, attach_z, rng)
        stand.data.materials.append(mat_backing())
        objects.append(stand)

    return objects


def generate_photoframe(seed, image_path=None, subtype='tabletop_simple'):
    rng = random.Random(seed)

    with_stand = subtype.startswith('tabletop')
    frame_style = 'bevel' if subtype.endswith('bevel') else 'simple'

    return _make_photo(rng, image_path, frame_style, with_stand)

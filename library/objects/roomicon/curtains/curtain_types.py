"""Генерация штор разных типов."""

import random
import math

from helpers import (
    create_curtain_mesh, create_rod,
    mat_curtain, mat_sheer, mat_rod,
)

CURTAIN_TYPES = {
    'straight': {},
    'gathered': {},
    'sheer': {},
}


def _make_straight(rng, window_width, window_top_z, floor_z=0,
                    fabric=None, rod_material=None):
    """Прямые шторы: две полы по бокам окна, слегка раздвинуты."""
    objects = []

    gap = window_width * rng.uniform(0.05, 0.15)  # зазор по центру
    curtain_width = (window_width - gap) / 2  # каждая пола ≈ полширины
    curtain_height = window_top_z - floor_z + 0.1
    rod_z = window_top_z + 0.08

    if fabric is None:
        fabric = mat_curtain(rng)
    if rod_material is None:
        rod_material = mat_rod(rng)

    # Карниз — должен быть шире обеих пол
    rod_width = max(window_width + curtain_width * 0.5, curtain_width * 2 + gap + 0.06)
    rod = create_rod("CurtainRod", rod_width)
    rod.location = (0, 0, rod_z)
    rod.data.materials.append(rod_material)
    objects.append(rod)
    noise_x = rng.uniform(0.0002, 0.002)
    noise_y = rng.uniform(0.0002, 0.004)

    # Левая пола
    left = create_curtain_mesh("CurtainLeft", curtain_width, curtain_height,
                                folds=rng.randint(5, 8),
                                fold_depth=rng.uniform(0.02, 0.04),rng=rng,noise_x=noise_x,noise_y=noise_y)
    left.location = (-gap / 2 - curtain_width / 2, 0, floor_z)
    left.data.materials.append(fabric)
    objects.append(left)

    # Правая пола
    right = create_curtain_mesh("CurtainRight", curtain_width, curtain_height,
                                 folds=rng.randint(5, 8),
                                 fold_depth=rng.uniform(0.02, 0.04),rng=rng,noise_x=noise_x,noise_y=noise_y)
    right.location = (gap / 2 + curtain_width / 2, 0, floor_z)
    right.data.materials.append(fabric)
    objects.append(right)

    return objects


def _make_gathered(rng, window_width, window_top_z, floor_z=0,
                   fabric=None, rod_material=None):
    """Присборенные шторы: две полы с более глубокими складками."""
    objects = []

    gap = window_width * rng.uniform(0.03, 0.1)
    curtain_width = (window_width - gap) / 2  # каждая пола ≈ полширины
    curtain_height = window_top_z - floor_z + 0.1
    rod_z = window_top_z + 0.08

    if fabric is None:
        fabric = mat_curtain(rng)
    if rod_material is None:
        rod_material = mat_rod(rng)

    # Карниз — должен быть шире обеих пол
    rod_width = max(window_width + curtain_width * 0.4, curtain_width * 2 + gap + 0.06)
    rod = create_rod("CurtainRod", rod_width)
    rod.location = (0, 0, rod_z)
    rod.data.materials.append(rod_material)
    objects.append(rod)

    # Более глубокие и частые складки
    folds = rng.randint(10, 16)
    fold_depth = rng.uniform(0.04, 0.07)

    # Левая
    noise_x = rng.uniform(0.0002, 0.002)
    noise_y = rng.uniform(0.0002, 0.005)
    left = create_curtain_mesh("CurtainLeft", curtain_width, curtain_height,
                                folds=folds, fold_depth=fold_depth,rng=rng,noise_x=noise_x,noise_y=noise_y)
    left.location = (-gap / 2 - curtain_width / 2, 0, floor_z)
    left.data.materials.append(fabric)
    objects.append(left)

    # Правая
    right = create_curtain_mesh("CurtainRight", curtain_width, curtain_height,
                                 folds=folds, fold_depth=fold_depth,rng=rng,noise_x=noise_x,noise_y=noise_y)
    right.location = (gap / 2 + curtain_width / 2, 0, floor_z)
    right.data.materials.append(fabric)
    objects.append(right)

    return objects


def _make_sheer(rng, window_width, window_top_z, floor_z=0,
                 fabric=None, rod_material=None):
    """Тюль: одна полупрозрачная панель по всей ширине окна."""
    objects = []

    curtain_width = window_width * rng.uniform(1.2, 1.6)
    rod_z = window_top_z + 0.08

    sheer_mat = fabric if fabric is not None else mat_sheer()
    if rod_material is None:
        rod_material = mat_rod(rng)

    # Карниз
    rod = create_rod("CurtainRod", curtain_width + 0.1)
    rod.location = (0, 0, rod_z)
    rod.data.materials.append(rod_material)
    objects.append(rod)

    # Тюль — одна панель, мелкие складки
    panel = create_curtain_mesh("Sheer", curtain_width, rod_z,
                                 folds=rng.randint(15, 25),
                                 fold_depth=rng.uniform(0.015, 0.025))
    panel.location = (0, 0, floor_z)
    panel.data.materials.append(sheer_mat)
    objects.append(panel)

    return objects


# ============================================================
# API
# ============================================================

def generate_curtain(seed, subtype='straight', window_width=1.2,
                      window_top_z=2.2, floor_z=0,
                      fabric=None, rod_material=None):
    """
    Генерирует штору. Origin — центр окна по X, Y=0 (у стены).
    window_width: ширина оконного проёма
    window_top_z: верх окна (подоконник + высота окна)
    fabric/rod_material: передать для единого стиля на всю комнату
    """
    rng = random.Random(seed)
    kw = dict(fabric=fabric, rod_material=rod_material)

    if subtype == 'straight':
        return _make_straight(rng, window_width, window_top_z, floor_z, **kw)
    elif subtype == 'gathered':
        return _make_gathered(rng, window_width, window_top_z, floor_z, **kw)
    elif subtype == 'sheer':
        return _make_sheer(rng, window_width, window_top_z, floor_z, **kw)
    else:
        return _make_straight(rng, window_width, window_top_z, floor_z)

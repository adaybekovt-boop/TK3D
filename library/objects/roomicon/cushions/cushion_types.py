"""Генерация подушек разных типов."""

import random
import math

from helpers import (create_box, create_cylinder, make_soft, mat_fabric,
                     create_cushion_rect)

CUSHION_TYPES = {
    'square': {},
    'rectangle': {},
}


def _make_square(rng):
    """Квадратная подушка."""
    size = rng.uniform(0.38, 0.48)
    thickness = rng.uniform(0.10, 0.17)

    fabric = mat_fabric(rng)
    cushion = create_cushion_rect("CushionSquare", size, size, thickness, rng=rng)
    cushion.data.materials.append(fabric)
    make_soft(cushion, disp_strength=rng.uniform(0.002, 0.005), noise_scale=rng.uniform(5, 12))

    return [cushion]


def _make_rectangle(rng):
    """Прямоугольная подушка."""
    width = rng.uniform(0.45, 0.55)
    depth = rng.uniform(0.3, 0.38)
    thickness = rng.uniform(0.10, 0.17)

    fabric = mat_fabric(rng)
    cushion = create_cushion_rect("CushionRect", width, depth, thickness, rng=rng)
    cushion.data.materials.append(fabric)
    make_soft(cushion, disp_strength=rng.uniform(0.002, 0.005), noise_scale=rng.uniform(5, 12))

    return [cushion]



# ============================================================
# API
# ============================================================

def generate_cushion(seed, subtype='square'):
    rng = random.Random(seed)
    if subtype == 'square':
        return _make_square(rng)
    elif subtype == 'rectangle':
        return _make_rectangle(rng)
    else:
        return _make_square(rng)

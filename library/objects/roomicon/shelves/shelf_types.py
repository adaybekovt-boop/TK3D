"""Генерация настенных полок."""

import random,math

from helpers import create_box, mat_wood, mat_metal, WOOD_STYLES, METAL_STYLES


SHELF_TYPES = {
    'single': {},
    'multi': {},
    'bracket': {},
    'box': {},
}


def _assign_mat(obj, mat):
    obj.data.materials.append(mat)


# ============================================================
# Одинарная полка
# ============================================================

def _make_single(rng):
    """Одна доска + 2 кронштейна. Origin — центр задней стороны доски."""
    width = rng.uniform(0.4, 0.8)
    depth = rng.uniform(0.15, 0.25)
    thick = rng.uniform(0.018, 0.03)

    hw = width / 2
    hd = depth / 2
    ht = thick / 2

    objects = []
    wood_mat = mat_wood(rng.randint(0, len(WOOD_STYLES) - 1))

    # Доска: origin у стены (Y=0 — стена), доска тянется в +Y
    board = create_box("ShelfBoard", hw, hd, ht, cy=hd)
    _assign_mat(board, wood_mat)
    objects.append(board)

    objects[0]['shelf_surfaces'] = [(ht, width, 0.30, depth)]  # (z, width, max_h, depth)

    # Кронштейны (выбор: металл или дерево)
    bracket_type = rng.choice(['metal', 'wood'])
    if bracket_type == 'metal':
        br_mat = mat_metal(rng.randint(0, len(METAL_STYLES) - 1))
    else:
        br_mat = wood_mat

    br_thick = 0.005 if bracket_type == 'metal' else 0.012
    br_depth = depth * rng.uniform(0.6, 0.85)
    br_height = br_depth * rng.uniform(0.5, 0.8)

    for side in (-1, 1):
        bx = side * hw * 0.7

        # Горизонтальная часть кронштейна (под доской)
        h_bar = create_box(f"BracketH_{side}",
                            br_thick / 2, br_depth / 2 - br_thick, br_thick / 2,
                            cx=bx, cy=br_depth / 2, cz=-ht - br_thick / 2)
        _assign_mat(h_bar, br_mat)
        objects.append(h_bar)

        # Вертикальная часть (у стены)
        v_bar = create_box(f"BracketV_{side}",
                            br_thick / 2, br_thick / 2, br_height / 2,
                            cx=bx, cy=br_thick / 2, cz=-ht - br_height / 2)
        _assign_mat(v_bar, br_mat)
        objects.append(v_bar)

        # Диагональ (опционально, для металлических)
        if bracket_type == 'metal' and rng.random() < 0.6:

            angle = 0.5
            diag = create_box(f"BracketD_{side}",
                               br_thick / 3, br_depth * 0.35, br_thick / 2)
            diag.location = (bx, br_depth * 0.35 - br_thick,-ht - br_height * 0.5 + br_depth * 0.35 * math.sin(angle) + br_thick)
            # Грубая аппроксимация диагонали — наклонённый бокс
            diag.rotation_euler = (angle, 0, 0)
            _assign_mat(diag, br_mat)
            objects.append(diag)

    return objects


# ============================================================
# Многоярусная полка
# ============================================================

def _make_multi(rng):
    """2–4 полки на боковых стойках."""
    n_shelves = rng.randint(2, 4)
    width = rng.uniform(0.5, 0.9)
    depth = rng.uniform(0.15, 0.22)
    thick = rng.uniform(0.018, 0.025)
    spacing = rng.uniform(0.25, 0.35)
    total_h = spacing * (n_shelves - 1) + thick

    hw = width / 2
    hd = depth / 2
    ht = thick / 2
    side_thick = rng.uniform(0.015, 0.025)
    hst = side_thick / 2

    objects = []
    wood_mat = mat_wood(rng.randint(0, len(WOOD_STYLES) - 1))

    # Боковые стойки
    for side in (-1, 1):
        sx = side * (hw + hst)
        stoy = create_box(f"ShelfSide_{side}",
                            hst, hd, total_h / 2 + thick,
                            cx=sx, cy=hd, cz=total_h / 2 - thick)
        _assign_mat(stoy, wood_mat)
        objects.append(stoy)

    # Полки
    surfaces = []
    for si in range(n_shelves):
        sz = si * spacing
        board = create_box(f"ShelfBoard_{si}",
                            hw, hd, ht,
                            cy=hd, cz=sz)
        _assign_mat(board, wood_mat)
        objects.append(board)
        # Поверхность для книг: все кроме верхней доски
        if si < n_shelves - 1:
            surface_z = sz + ht
            max_h = spacing - thick
            surfaces.append((surface_z, width, max_h, depth))

    objects[0]['shelf_surfaces'] = surfaces
    return objects


# ============================================================
# С Г-кронштейном
# ============================================================

def _make_bracket(rng):
    """Одна доска + Г-образный кронштейн."""
    width = rng.uniform(0.3, 0.6)
    depth = rng.uniform(0.15, 0.2)
    thick = rng.uniform(0.02, 0.03)

    hw = width / 2
    hd = depth / 2
    ht = thick / 2

    objects = []
    wood_mat = mat_wood(rng.randint(0, len(WOOD_STYLES) - 1))
    br_mat = mat_metal(rng.randint(0, len(METAL_STYLES) - 1))

    # Доска
    board = create_box("ShelfBoard", hw, hd, ht, cy=hd)
    _assign_mat(board, wood_mat)
    objects.append(board)

    objects[0]['shelf_surfaces'] = [(ht, width, 0.30, depth)]

    br_t = 0.006
    br_drop = depth * rng.uniform(0.7, 1.0)

    for side in (-1, 1):
        bx = side * hw * rng.uniform(0.55, 0.75)

        # Горизонтальная часть Г
        h_bar = create_box(f"BracketH_{side}",
                            br_t / 2, depth * 0.85 / 2, br_t / 2,
                            cx=bx, cy=depth * 0.85 / 2 + br_t, cz=-ht - br_t / 2)
        _assign_mat(h_bar, br_mat)
        objects.append(h_bar)

        # Вертикальная часть Г (у стены, вниз)
        v_bar = create_box(f"BracketV_{side}",
                            br_t / 2, br_t / 2, br_drop / 2,
                            cx=bx, cy=br_t / 2, cz=-ht - br_drop / 2)
        _assign_mat(v_bar, br_mat)
        objects.append(v_bar)

    return objects


# ============================================================
# Полка-ящик
# ============================================================

def _make_box(rng):
    """Открытый бокс на стене."""
    outer_w = rng.uniform(0.25, 0.4)
    outer_h = rng.uniform(0.2, 0.35)
    depth = rng.uniform(0.15, 0.22)
    wall_t = rng.uniform(0.015, 0.025)

    hw = outer_w / 2
    hh = outer_h / 2
    hd = depth / 2
    wt = wall_t

    objects = []
    wood_mat = mat_wood(rng.randint(0, len(WOOD_STYLES) - 1))

    # Задняя стенка
    back = create_box("BoxBack", hw, wt / 10, hh,
                       cy=wt / 2 - wall_t*0.6, cz=0)
    _assign_mat(back, wood_mat)
    objects.append(back)

    # Верх
    top = create_box("BoxTop", hw, hd, wt / 2,
                      cy=hd, cz=hh - wt / 2)
    _assign_mat(top, wood_mat)
    objects.append(top)

    # Низ
    bottom = create_box("BoxBottom", hw, hd, wt / 2,
                          cy=hd, cz=-hh + wt / 2)
    _assign_mat(bottom, wood_mat)
    objects.append(bottom)

    # Левая стенка
    left = create_box("BoxLeft", wt / 2, hd, hh - wt,
                       cx=-hw + wt / 2, cy=hd, cz=0)
    _assign_mat(left, wood_mat)
    objects.append(left)

    # Правая стенка
    right = create_box("BoxRight", wt / 2, hd, hh - wt,
                         cx=hw - wt / 2, cy=hd, cz=0)
    _assign_mat(right, wood_mat)
    objects.append(right)

    # Поверхность: верх нижней доски, ширина между стенками, высота до верхней доски
    surface_z = -hh + wt
    usable_w = outer_w - 2 * wt
    max_h = outer_h - 2 * wt
    objects[0]['shelf_surfaces'] = [(surface_z, usable_w, max_h, depth)]

    return objects


# ============================================================
# API
# ============================================================

def generate_shelf(seed, subtype='single'):
    rng = random.Random(seed)
    if subtype == 'single':
        return _make_single(rng)
    elif subtype == 'multi':
        return _make_multi(rng)
    elif subtype == 'bracket':
        return _make_bracket(rng)
    elif subtype == 'box':
        return _make_box(rng)
    else:
        return _make_single(rng)

"""Генерация столов разных типов."""

import random
import math

from helpers import (
    create_box, create_cylinder, create_disk, create_oval_top,
    create_turned_leg, create_glass_material,
    create_lathe_column, create_plate_base, create_tripod_base,
    COLUMN_PROFILES,
    mat_wood, mat_metal,
)

TABLE_TYPES = {
    'dining': {},
    'coffee': {},
    'desk': {},
    'nightstand': {},
    'round': {},
    'radial': {},
    'bar': {},
    'tea': {},
}


def _four_legs(name, hw, hd, leg_r, leg_h, inset, leg_type, rng, mat, oval=False):
    """Создаёт 4 ножки. Для oval=True — размещает под краем эллипса."""
    legs = []
    for i, (sx, sy) in enumerate([(-1,-1), (1,-1), (1,1), (-1,1)]):
        if oval:
            # Ножки под 45° на эллипсе, смещённые внутрь на inset
            # Точка на эллипсе: (hw*cos45, hd*sin45), сдвиг внутрь на inset * (cos45, sin45)
            cos45 = math.cos(math.pi / 4)
            sin45 = math.sin(math.pi / 4)
            lx = sx * (hw * cos45 - inset)
            ly = sy * (hd * sin45 - inset)
        else:
            lx = sx * (hw - inset)
            ly = sy * (hd - inset)
        if leg_type == 'turned':
            leg = create_turned_leg(f"{name}_Leg{i}", leg_r, leg_h)
        elif leg_type == 'cylinder':
            leg = create_cylinder(f"{name}_Leg{i}", leg_r, leg_h)
        else:  # square
            leg = create_box(f"{name}_Leg{i}", leg_r, leg_r, leg_h / 2, cz=leg_h / 2)
        leg.location = (lx, ly, 0)
        leg.data.materials.append(mat)
        legs.append(leg)
    return legs


def _central_pedestal(name, base_r, column_r, column_h, rng, mat):
    """Центральная опора: колонна + крестовина."""
    objects = []

    # Колонна
    col = create_cylinder(f"{name}_Column", column_r, column_h)
    col.data.materials.append(mat)
    objects.append(col)

    # Крестовина (4 луча)
    arm_len = base_r * 0.8
    arm_w = column_r * 1.5
    arm_h = 0.025
    for i in range(4):
        angle = i * math.pi / 2
        ax = arm_len / 2 * math.cos(angle)
        ay = arm_len / 2 * math.sin(angle)
        arm = create_box(f"{name}_Arm{i}", arm_len / 2, arm_w / 2, arm_h / 2)
        arm.location = (ax,ay,arm_h / 2)
        arm.rotation_euler = (0, 0, angle)
        arm.data.materials.append(mat)
        objects.append(arm)

    return objects


# ============================================================
# Обеденный
# ============================================================

def _make_dining(rng):
    width = rng.uniform(1.2, 1.8)
    depth = rng.uniform(0.8, 1.0)
    height = 0.75
    top_thick = rng.uniform(0.03, 0.05)

    shape = rng.choice(['rect', 'oval'])
    leg_type = rng.choice(['cylinder', 'turned', 'square'])
    wood = mat_wood(rng)
    leg_mat = wood if rng.random() < 0.7 else mat_metal(rng)

    objects = []
    hw, hd = width / 2, depth / 2
    leg_h = height - top_thick
    leg_r = rng.uniform(0.02, 0.035)
    inset = rng.uniform(0.04, 0.08)

    # Столешница
    if shape == 'rect':
        top = create_box("DiningTop", hw, hd, top_thick / 2, cz=height - top_thick / 2)
    else:
        top = create_oval_top("DiningTop", hw, hd, top_thick, z_offset=height - top_thick)

    top.data.materials.append(wood)
    objects.append(top)

    # Ножки
    objects.extend(_four_legs("Dining", hw, hd, leg_r, leg_h, inset, leg_type, rng, leg_mat,
                               oval=(shape == 'oval')))

    objects[0]['surface_z'] = height
    objects[0]['table_size'] = (width, depth)
    return objects


# ============================================================
# Журнальный
# ============================================================

def _make_coffee(rng):
    width = rng.uniform(0.8, 1.2)
    depth = rng.uniform(0.5, 0.7)
    height = rng.uniform(0.35, 0.45)
    top_thick = rng.uniform(0.02, 0.04)

    shape = rng.choice(['rect', 'round', 'oval'])
    use_glass = rng.random() < 0.3
    leg_type = rng.choice(['cylinder', 'square'])
    wood = mat_wood(rng)
    leg_mat = mat_metal(rng) if use_glass else wood

    objects = []
    hw, hd = width / 2, depth / 2
    leg_h = height - top_thick
    leg_r = rng.uniform(0.015, 0.025)
    inset = rng.uniform(0.03, 0.06)

    if shape == 'rect':
        top = create_box("CoffeeTop", hw, hd, top_thick / 2, cz=height - top_thick / 2)
    elif shape == 'round':
        r = min(hw, hd)
        top = create_disk("CoffeeTop", r, top_thick, z_offset=height - top_thick)
    else:
        top = create_oval_top("CoffeeTop", hw, hd, top_thick, z_offset=height - top_thick)

    if use_glass:
        top.data.materials.append(create_glass_material())
    else:
        top.data.materials.append(wood)
    objects.append(top)

    if shape == 'round' and rng.random() < 0.4:
        # Центральная опора для круглого
        r = min(hw, hd)
        objects.extend(_central_pedestal("Coffee", r, 0.03, leg_h, rng, leg_mat))
    else:
        is_oval = shape in ('round', 'oval')
        if shape == 'round':
            hw = hd = min(hw, hd) * 0.7
        objects.extend(_four_legs("Coffee", hw, hd, leg_r, leg_h, inset, leg_type, rng, leg_mat,
                                   oval=is_oval))

    objects[0]['surface_z'] = height
    objects[0]['table_size'] = (width, depth)
    return objects


# ============================================================
# Письменный
# ============================================================

def _make_desk(rng):
    width = rng.uniform(1.2, 1.6)
    depth = rng.uniform(0.6, 0.8)
    height = 0.75
    top_thick = rng.uniform(0.03, 0.04)

    support = rng.choice(['legs', 'panels'])
    wood = mat_wood(rng)

    objects = []
    hw, hd = width / 2, depth / 2
    leg_h = height - top_thick

    # Столешница
    top = create_box("DeskTop", hw, hd, top_thick / 2, cz=height - top_thick / 2)
    top.data.materials.append(wood)
    objects.append(top)

    if support == 'legs':
        leg_r = rng.uniform(0.02, 0.03)
        leg_mat = wood if rng.random() < 0.5 else mat_metal(rng)
        objects.extend(_four_legs("Desk", hw, hd, leg_r, leg_h, 0.05, 'square', rng, leg_mat))
    else:
        # Боковые панели-тумбы
        panel_thick = rng.uniform(0.02, 0.03)
        for sx in (-1, 1):
            px = sx * (hw - panel_thick / 2 - 0.01)
            panel = create_box(f"DeskPanel_{sx}", panel_thick / 2, hd * 0.9 + panel_thick/2, leg_h / 2,
                                cx=px, cz=leg_h / 2,cy = -panel_thick/2)
            panel.data.materials.append(wood)
            objects.append(panel)

        # Задняя стенка (опциональная, внизу)
        if rng.random() < 0.5:
            back = create_box("DeskBack", hw - panel_thick - 0.01, panel_thick / 2, leg_h * 0.3,
                               cy=-hd + panel_thick, cz=leg_h * 0.7)
            back.data.materials.append(wood)
            objects.append(back)

    objects[0]['surface_z'] = height
    objects[0]['table_size'] = (width, depth)
    return objects


# ============================================================
# Тумбочка / прикроватный
# ============================================================

def _make_nightstand(rng):
    size = rng.uniform(0.4, 0.5)
    height = rng.uniform(0.5, 0.6)
    top_thick = rng.uniform(0.025, 0.035)

    shape = rng.choice(['square', 'round'])
    wood = mat_wood(rng)

    objects = []
    leg_h = height - top_thick

    if shape == 'square':
        hs = size / 2
        top = create_box("NightTop", hs, hs, top_thick / 2, cz=height - top_thick / 2)
        top.data.materials.append(wood)
        objects.append(top)

        leg_r = rng.uniform(0.015, 0.025)
        leg_type = rng.choice(['cylinder', 'turned', 'square'])
        objects.extend(_four_legs("Night", hs, hs, leg_r, leg_h, 0.03, leg_type, rng, wood))

        # Нижняя полка (опционально)
        if rng.random() < 0.5:
            shelf_z = leg_h * rng.uniform(0.15, 0.3)
            shelf = create_box("NightShelf", hs * 0.85, hs * 0.85, 0.01,
                                cz=shelf_z)
            shelf.data.materials.append(wood)
            objects.append(shelf)
    else:
        r = size / 2
        top = create_disk("NightTop", r, top_thick, z_offset=height - top_thick)
        top.data.materials.append(wood)
        objects.append(top)

        # Центральная ножка
        col_r = r * rng.uniform(0.15, 0.25)
        col = create_cylinder("NightCol", col_r, leg_h)
        col.data.materials.append(wood)
        objects.append(col)

        # База
        base = create_disk("NightBase", r * 0.7, 0.015)
        base.data.materials.append(wood)
        objects.append(base)

    objects[0]['surface_z'] = height
    objects[0]['table_size'] = (size, size)
    return objects


# ============================================================
# Круглый
# ============================================================

def _make_round(rng):
    radius = rng.uniform(0.4, 0.6)
    height = 0.75
    top_thick = rng.uniform(0.03, 0.045)

    support = rng.choice(['pedestal', 'legs'])
    wood = mat_wood(rng)

    objects = []
    leg_h = height - top_thick

    top = create_disk("RoundTop", radius, top_thick, z_offset=height - top_thick)
    top.data.materials.append(wood)
    objects.append(top)

    if support == 'pedestal':
        col_r = radius * rng.uniform(0.1, 0.18)
        objects.extend(_central_pedestal("Round", radius, col_r, leg_h, rng, wood))
    else:
        leg_r = rng.uniform(0.02, 0.03)
        n_legs = rng.choice([3, 4])
        # For round tables, place legs at an appropriate distance from the center
        # to ensure they're within the table top
        leg_distance = radius * rng.uniform(0.4, 0.6)  # Place legs at 40-60% of radius
        for i in range(n_legs):
            angle = 2 * math.pi * i / n_legs
            #lx = leg_distance * math.cos(angle)
            #ly = leg_distance * math.sin(angle)
            lx = (radius - 0.06) * math.cos(angle)
            ly = (radius - 0.06) * math.sin(angle)
            leg_type = rng.choice(['cylinder', 'turned'])
            if leg_type == 'turned':
                leg = create_turned_leg(f"RoundLeg{i}", leg_r, leg_h)
            else:
                leg = create_cylinder(f"RoundLeg{i}", leg_r, leg_h)
            leg.location = (lx, ly, 0)
            leg.data.materials.append(wood)
            objects.append(leg)

    objects[0]['surface_z'] = height
    objects[0]['table_size'] = (radius * 2, radius * 2)
    return objects

def _make_radial(rng):
    """Круглый стол с фигурной центральной ножкой и разными основаниями."""
    radius = rng.uniform(0.4, 0.6)
    height = 0.75
    top_thick = rng.uniform(0.03, 0.045)
    wood = mat_wood(rng)

    objects = []
    leg_h = height - top_thick

    # Столешница
    top = create_disk("RadialTop", radius, top_thick, z_offset=height - top_thick)
    top.data.materials.append(wood)
    objects.append(top)

    # Фигурная центральная колонна
    col_r = radius * rng.uniform(0.08, 0.15)
    profile_type = rng.choice(COLUMN_PROFILES)
    base_type = rng.choice(['plate', 'tripod', 'cross'])

    if base_type == 'plate':
        base_h = rng.uniform(0.015, 0.025)
        base = create_plate_base("RadialBase", radius * rng.uniform(0.55, 0.7), base_h)
        base.data.materials.append(wood)
        objects.append(base)
        col_z = base_h
    elif base_type == 'tripod':
        tripod_leg_len = radius * rng.uniform(0.5, 0.7)
        tripod_leg_r = col_r * rng.uniform(0.4, 0.6)
        tripod_parts = create_tripod_base("RadialTripod", tripod_leg_len,
                                            tripod_leg_r, col_r * 1.2, rng)
        for part in tripod_parts:
            part.data.materials.append(wood)
            objects.append(part)
        col_z = col_r * 2  # над втулкой
    else:  # cross — крестовина (уже есть _central_pedestal)
        col_z = 0
        cross_r = radius * rng.uniform(0.5, 0.65)
        arm_w = col_r * 1.5
        arm_h = 0.025
        for i in range(4):
            angle = math.pi / 4 + i * math.pi / 2
            arm = create_box(f"RadialArm{i}", cross_r / 2, arm_w / 2, arm_h / 2)
            arm.location = (cross_r / 2 * math.cos(angle),
                             cross_r / 2 * math.sin(angle),
                             arm_h / 2)
            arm.rotation_euler = (0, 0, angle)
            arm.data.materials.append(wood)
            objects.append(arm)

    # Колонна
    col_h = leg_h - col_z
    column = create_lathe_column("RadialColumn", col_r, col_h, profile_type, z_offset=col_z)
    column.data.materials.append(wood)
    objects.append(column)

    objects[0]['surface_z'] = height
    objects[0]['table_size'] = (radius * 2, radius * 2)
    return objects



# ============================================================
# Барный
# ============================================================

def _make_bar(rng):
    width = rng.uniform(0.8, 1.2)
    depth = rng.uniform(0.6, 0.8)
    height = rng.uniform(0.9, 1.05)
    top_thick = rng.uniform(0.02, 0.04)

    shape = rng.choice(['rect', 'round'])
    use_glass = rng.random() < 0.3
    wood = mat_wood(rng)
    metal = mat_metal(rng)

    objects = []
    hw, hd = width / 2, depth / 2
    leg_h = height - top_thick
    leg_r = rng.uniform(0.015, 0.025)
    inset = rng.uniform(0.03, 0.06)

    # Столешница
    if shape == 'rect':
        top = create_box("BarTop", hw, hd, top_thick / 2, cz=height - top_thick / 2)
    else:  # round
        r = min(hw, hd)
        top = create_disk("BarTop", r, top_thick, z_offset=height - top_thick)

    if use_glass:
        top.data.materials.append(create_glass_material())
    else:
        top.data.materials.append(wood)
    objects.append(top)

    # Ножки - для барных столов обычно 4 ножки, но с низкой высотой
    if shape == 'round':
        # Для круглых барных столов - центральная опора или 4 ножки вокруг
        if rng.random() < 0.5:
            # Центральная опора для круглого барного стола
            col_r = min(hw, hd) * rng.uniform(0.15, 0.25)
            objects.extend(_central_pedestal("Bar", min(hw, hd), col_r, leg_h, rng, metal))
        else:
            # 4 ножки вокруг - исправлено: размещаем внутри радиуса столешницы
            r = min(hw, hd)
            # Рассчитываем расстояние от центра, чтобы ножки были внутри столешницы
            leg_distance = r * rng.uniform(0.4, 0.6)
            for i, (sx, sy) in enumerate([(-1,-1), (1,-1), (1,1), (-1,1)]):
                # Используем правильную формулу для размещения на окружности внутри столешницы
                lx = sx * leg_distance
                ly = sy * leg_distance
                leg = create_cylinder(f"BarLeg{i}", leg_r, leg_h)
                leg.location = (lx, ly, 0)
                leg.data.materials.append(metal)
                objects.append(leg)
    else:
        # Прямоугольные барные столы
        objects.extend(_four_legs("Bar", hw, hd, leg_r, leg_h, inset, 'cylinder', rng, metal,
                                   oval=False))

    objects[0]['surface_z'] = height
    objects[0]['table_size'] = (width, depth)
    return objects


# ============================================================
# Чайный
# ============================================================

def _make_tea(rng):
    width = rng.uniform(0.4, 0.6)
    depth = rng.uniform(0.4, 0.6)
    height = rng.uniform(0.3, 0.45)
    top_thick = rng.uniform(0.02, 0.03)

    shape = rng.choice(['square', 'round'])
    wood = mat_wood(rng)

    objects = []
    hw, hd = width / 2, depth / 2
    leg_h = height - top_thick
    leg_r = rng.uniform(0.01, 0.015)
    inset = rng.uniform(0.02, 0.03)

    # Столешница
    if shape == 'square':
        top = create_box("TeaTop", hw, hd, top_thick / 2, cz=height - top_thick / 2)
    else:  # round
        r = min(hw, hd)
        top = create_disk("TeaTop", r, top_thick, z_offset=height - top_thick)

    top.data.materials.append(wood)
    objects.append(top)

    # Ножки - чайные столы обычно имеют 4 ножки в углах
    if shape == 'round':
        # Для круглых чайных столов, используем центральную опору или 4 ножки
        if rng.random() < 0.5:
            # Центральная опора для круглого чайного стола
            col_r = min(hw, hd) * rng.uniform(0.15, 0.25)
            objects.extend(_central_pedestal("Tea", min(hw, hd), col_r, leg_h, rng, wood))
        else:
            # 4 ножки вокруг - правильно размещаем внутри радиуса
            r = min(hw, hd)
            leg_distance = r * rng.uniform(0.4, 0.6)
            for i, (sx, sy) in enumerate([(-1,-1), (1,-1), (1,1), (-1,1)]):
                lx = sx * leg_distance
                ly = sy * leg_distance
                leg = create_cylinder(f"TeaLeg{i}", leg_r, leg_h)
                leg.location = (lx, ly, 0)
                leg.data.materials.append(wood)
                objects.append(leg)
    else:
        # Прямоугольные (квадратные) чайные столы
        objects.extend(_four_legs("Tea", hw, hd, leg_r, leg_h, inset, 'cylinder', rng, wood,
                                   oval=False))

    objects[0]['surface_z'] = height
    objects[0]['table_size'] = (width, depth)
    return objects




# ============================================================
# API
# ============================================================

def generate_table(seed, subtype='dining'):
    rng = random.Random(seed)
    if subtype == 'dining':
        return _make_dining(rng)
    elif subtype == 'coffee':
        return _make_coffee(rng)
    elif subtype == 'desk':
        return _make_desk(rng)
    elif subtype == 'nightstand':
        return _make_nightstand(rng)
    elif subtype == 'round':
        return _make_round(rng)
    elif subtype == 'radial':
        return _make_radial(rng)
    elif subtype == 'bar':
        return _make_bar(rng)
    elif subtype == 'tea':
        return _make_tea(rng)
    else:
        return _make_dining(rng)

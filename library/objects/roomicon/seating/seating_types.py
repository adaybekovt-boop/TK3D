"""Генерация кроватей и диванов."""

import bpy
import bmesh
import random
import math

from helpers import (
    create_box, create_cylinder, make_mattress,
    mat_wood, mat_metal, mat_fabric, mat_leather, mat_mattress, mat_cushion,
)

SEATING_TYPES = {
    'panel_bed': {},
    'single_bed': {},
    'double_bed': {},
    'bunk_bed': {},
    'sofa': {},
    'daybed': {},
}

# ============================================================
# Панельная кровать
# ============================================================

def _make_panel_bed(rng):
    width = 0.9
    length = 2.0
    frame_thick = 0.04
    mattress_h = rng.uniform(0.15, 0.2)


    height = rng.uniform(0.9,1.1)

    base_thick = rng.uniform(0.05,0.1)
    base_z = height * rng.uniform(0.5,0.6)

    hw, hl = width / 2, length / 2
    wood = mat_wood(rng)
    mattress_mat = mat_mattress(rng)

    objects = []

    # Каркас
    frame = create_box("BedFrame", hw - frame_thick, hl, base_thick)
    frame.location = (0, 0, base_z - base_thick - mattress_h)
    frame.data.materials.append(wood)
    objects.append(frame)

    # Матрас
    mat_top = make_mattress("Mattress", hw - 0.02, hl - 0.02 - frame_thick, mattress_h / 2)
    mat_top.location = (0, 0, base_z -  mattress_h/2 )
    mat_top.data.materials.append(mattress_mat)
    objects.append(mat_top)

    # Две рамы-спинки по бокам (вместо одной сплошной спинки)
    # Рамы начинаются от пола и образуют раму над кроватью
    rail_width = 0.04  # ширина бруска
    num_rails = rng.randint(3, 5)  # количество реек между основанием и верхним бруском

    
    # Межосевое расстояние для реек
    rail_spacing = width / (num_rails + 4)
    
    for sx in (-1, 1):  # две рамы: левая и правая
        # Вертикальные стойки рамы (начинаются от пола)
        for sy, label in [(-1, 'Left'), (1, 'Right')]:
            post = create_cylinder(f"HeadboardPost_{label}_{sx}", rail_width / 2, height)
            post.location = (sx * (hw - 0.03), sy * (hl - 0.03), 0)
            post.data.materials.append(wood)
            objects.append(post)
        
        # Верхний горизонтальный брус рамы (сверху)
        upper_rail = create_box(f"HeadboardUpperRail_{sx}", hw -0.03, 0.02, frame_thick/2)
        upper_rail.location = (0, sx * (hl - 0.03), height-frame_thick/2)
        upper_rail.data.materials.append(wood)
        objects.append(upper_rail)
        
        # Рейки между верхним бруском и основанием кровати
        for ri in range(num_rails):


            r_h = (height - (base_z - mattress_h))

            rail = create_cylinder(f"HeadboardRail_{sx}_{ri}", rail_width / 5,  (r_h - frame_thick))

            rail.location = ( rail_spacing * (ri - (num_rails-1)/2), sx * (hl - 0.03), height  - r_h )
            rail.data.materials.append(wood)
            objects.append(rail)

    objects[0]['mattress_z'] = base_z
    return objects


# ============================================================
# Односпальная кровать
# ============================================================

def _make_single_bed(rng):
    width = 0.9
    length = 2.0
    frame_h = rng.uniform(0.3, 0.38)
    frame_thick = 0.04
    mattress_h = rng.uniform(0.15, 0.2)
    headboard_h = rng.uniform(0.4, 0.55)
    headboard_thick = rng.uniform(0.04, 0.06)
    has_legs = rng.random() < 0.6
    leg_h = rng.uniform(0.08, 0.15) if has_legs else 0

    hw, hl = width / 2, length / 2
    wood = mat_wood(rng)
    mattress_mat = mat_mattress(rng)

    objects = []

    # Каркас
    base_z = leg_h
    frame = create_box("BedFrame", hw, hl, frame_thick / 2)
    frame.location = (0, 0, base_z + frame_thick / 2)
    frame.data.materials.append(wood)
    objects.append(frame)

    # Ножки
    if has_legs:
        leg_r = 0.025
        for sx, sy in [(-1,-1), (1,-1), (1,1), (-1,1)]:
            leg = create_cylinder(f"BedLeg_{sx}_{sy}", leg_r, leg_h)
            leg.location = (sx * (hw - 0.04), sy * (hl - 0.04), 0)
            leg.data.materials.append(wood)
            objects.append(leg)

    # Матрас
    mat_top = make_mattress("Mattress", hw - 0.02, hl - 0.02, mattress_h / 2)
    mat_top.location = (0, 0, base_z + frame_thick + mattress_h / 2)
    mat_top.data.materials.append(mattress_mat)
    objects.append(mat_top)

    # Изголовье (у -Y, спинкой к стене)
    head = create_box("Headboard", hw, headboard_thick / 2, headboard_h / 2)
    head.location = (0, -hl + headboard_thick / 2, base_z + frame_thick + headboard_h / 2)
    head.data.materials.append(wood)
    objects.append(head)

    objects[0]['mattress_z'] = base_z + frame_thick + mattress_h
    return objects


# ============================================================
# Двуспальная кровать
# ============================================================

def _make_double_bed(rng):
    width = rng.uniform(1.4, 1.8)
    length = 2.0
    frame_h = rng.uniform(0.3, 0.38)
    frame_thick = 0.05
    mattress_h = rng.uniform(0.18, 0.22)
    headboard_h = rng.uniform(0.5, 0.75)
    headboard_thick = rng.uniform(0.05, 0.08)
    has_legs = rng.random() < 0.5
    leg_h = rng.uniform(0.1, 0.15) if has_legs else 0

    hw, hl = width / 2, length / 2
    wood = mat_wood(rng)
    mattress_mat = mat_mattress(rng)
    upholstery = rng.choice(['wood', 'fabric'])

    objects = []

    base_z = leg_h

    # Каркас
    frame = create_box("BedFrame", hw, hl, frame_thick / 2)
    frame.location = (0, 0, base_z + frame_thick / 2)
    frame.data.materials.append(wood)
    objects.append(frame)

    # Ножки
    if has_legs:
        leg_r = 0.03
        for sx, sy in [(-1,-1), (1,-1), (1,1), (-1,1)]:
            leg = create_cylinder(f"BedLeg_{sx}_{sy}", leg_r, leg_h)
            leg.location = (sx * (hw - 0.05), sy * (hl - 0.05), 0)
            leg.data.materials.append(wood)
            objects.append(leg)

    # Матрас
    mat_top = make_mattress("Mattress", hw - 0.02, hl - 0.02, mattress_h / 2)
    mat_top.location = (0, 0, base_z + frame_thick + mattress_h / 2)
    mat_top.data.materials.append(mattress_mat)
    objects.append(mat_top)

    # Подушки (2 штуки)
    pillow_w = (width - 0.1) / 2 - 0.02
    pillow_d = 0.2
    pillow_h = 0.08
    pillow_z = base_z + frame_thick + mattress_h + pillow_h / 2
    for sx in (-1, 1):
        #pillow = create_box(f"Pillow_{sx}", pillow_w / 2, pillow_d / 2, pillow_h / 2)
        pillow = make_mattress(f"Pillow_{sx}", pillow_w / 2, pillow_d / 2, pillow_h / 2)
        pillow.location = (sx * (pillow_w / 2 + 0.02), -hl + 0.25, pillow_z)
        pillow.data.materials.append(mattress_mat)
        objects.append(pillow)

    # Изголовье
    if upholstery == 'fabric':
        head_mat = mat_fabric(rng)
    else:
        head_mat = wood
    head = create_box("Headboard", hw, headboard_thick / 2, headboard_h / 2)
    head.location = (0, -hl + headboard_thick / 2, base_z + frame_thick + headboard_h / 2)
    head.data.materials.append(head_mat)
    objects.append(head)

    return objects


# ============================================================
# Двухъярусная кровать
# ============================================================

def _make_bunk_bed(rng):
    width = 0.9
    length = 2.0
    frame_thick = 0.04
    mattress_h = 0.12
    lower_h = 0.35
    upper_h = rng.uniform(1.35, 1.5)
    total_h = upper_h + frame_thick + mattress_h + 0.1
    post_r = rng.uniform(0.025, 0.035)

    hw, hl = width / 2, length / 2
    material_type = rng.choice(['wood', 'metal'])
    if material_type == 'wood':
        frame_mat = mat_wood(rng)
    else:
        frame_mat = mat_metal(rng)
    mattress_mat = mat_mattress(rng)

    objects = []

    # 4 стойки
    for sx, sy in [(-1,-1), (1,-1), (1,1), (-1,1)]:
        post = create_cylinder(f"BunkPost_{sx}_{sy}", post_r, total_h)
        post.location = (sx * (hw - post_r), sy * (hl - post_r), 0)
        post.data.materials.append(frame_mat)
        objects.append(post)

    # Нижний ярус
    for label, z_base in [("Lower", lower_h), ("Upper", upper_h)]:
        # Рама
        frame = create_box(f"Bunk{label}Frame", hw - post_r, hl - post_r, frame_thick / 2)
        frame.location = (0, 0, z_base + frame_thick / 2)
        frame.data.materials.append(frame_mat)
        objects.append(frame)

        # Матрас
        mat_obj = make_mattress(f"Bunk{label}Mattress", hw - post_r - 0.01,
                                 hl - post_r - 0.01, mattress_h / 2)
        mat_obj.location = (0, 0, z_base + frame_thick + mattress_h / 2)
        mat_obj.data.materials.append(mattress_mat)
        objects.append(mat_obj)

    # Лестница (на правой стороне, +X)
    ladder_x = hw + post_r + 0.02
    rung_count = rng.randint(4, 6)
    rung_spacing = (upper_h - lower_h) / (rung_count + 1)
    rung_r = 0.012
    for ri in range(rung_count):
        rung_z = lower_h + rung_spacing * (ri + 1)
        rung = create_cylinder(f"BunkRung_{ri}", rung_r, 0.3)
        rung.location = (ladder_x, 0.15, rung_z)
        rung.rotation_euler = (math.pi / 2, 0, 0)
        rung.data.materials.append(frame_mat)
        objects.append(rung)

    # Стойки лестницы
    ladder_h = upper_h + frame_thick + mattress_h - lower_h
    for sy in (-1, 1):
        ls = create_cylinder(f"BunkLadderPost_{sy}", rung_r, ladder_h)
        ls.location = (ladder_x, sy * 0.13, lower_h)
        ls.data.materials.append(frame_mat)
        objects.append(ls)

    # Ограждение верхнего яруса (-Y сторона)
    guard_z = upper_h + frame_thick + mattress_h
    guard = create_box("BunkGuard", hw - post_r, 0.01, 0.08)
    guard.location = (0, -hl + post_r, guard_z + 0.08)
    guard.data.materials.append(frame_mat)
    objects.append(guard)

    return objects


# ============================================================
# Прямой диван
# ============================================================

def _make_sofa(rng):
    width = rng.uniform(1.8, 2.4)
    depth = rng.uniform(0.85, 0.95)
    seat_h = 0.42
    seat_thick = rng.uniform(0.1, 0.14)
    back_h = rng.uniform(0.42, 0.52)
    back_thick = rng.uniform(0.12, 0.16)
    arm_w = rng.uniform(0.08, 0.14)
    arm_h = rng.uniform(0.18, 0.25)
    base_h = seat_h - seat_thick

    n_cushions = rng.randint(2, 3)

    hw, hd = width / 2, depth / 2
    use_leather = rng.random() < 0.25
    if use_leather:
        upholstery = mat_leather(rng)
    else:
        upholstery = mat_fabric(rng)
    cushion_mat = mat_cushion(upholstery, rng)
    leg_mat = mat_wood(rng) if rng.random() < 0.5 else mat_metal(rng)

    objects = []

    # Основание
    base = make_mattress("SofaBase", hw - arm_w, hd, base_h / 2,0.02)
    base.location = (0, 0, base_h / 2)
    base.data.materials.append(upholstery)
    objects.append(base)

    # Ножки (маленькие, опционально)
    if rng.random() < 0.6:
        leg_r = 0.02
        leg_h_val = 0.04
        # Смещаем основание вверх
        base.location = (0, 0, base_h / 2 + leg_h_val)
        for sx, sy in [(-1,-1), (1,-1), (1,1), (-1,1)]:
            leg = create_cylinder(f"SofaLeg_{sx}_{sy}", leg_r, leg_h_val)
            leg.location = (sx * (hw - 0.06), sy * (hd - 0.06), 0)
            leg.data.materials.append(leg_mat)
            objects.append(leg)
        base_top_z = base_h + leg_h_val
    else:
        base_top_z = base_h

    # Подушки сиденья
    cushion_w = (width - arm_w * 2 - 0.02 * (n_cushions - 1)) / n_cushions
    for ci in range(n_cushions):
        cx = -hw + arm_w + cushion_w / 2 + ci * (cushion_w)
        cushion = make_mattress(f"SofaCushion_{ci}",
                              cushion_w / 2 , hd * 0.75, seat_thick / 2,0.03)
        cushion.location = (cx, hd * 0.1, base_top_z + seat_thick / 2)
        cushion.data.materials.append(cushion_mat)
        objects.append(cushion)

    # Спинка
    back = make_mattress("SofaBack", hw - arm_w, back_thick / 2, back_h / 2,0.02)
    back.location = (0, -hd + back_thick / 2, base_top_z +  back_h / 2 - 0.02)
    back.data.materials.append(upholstery)
    objects.append(back)

    # Подлокотники
    arm_top_z = base_top_z + seat_thick + arm_h
    for sx in (-1, 1):
        arm = make_mattress(f"SofaArm_{sx}", arm_w / 2, hd, arm_top_z / 2,0.01)
        arm.location = (sx * (hw - arm_w / 2), 0, arm_top_z / 2)
        arm.data.materials.append(upholstery)
        objects.append(arm)

    return objects



# ============================================================
# Кушетка
# ============================================================

def _make_daybed(rng):
    width = rng.uniform(1.8, 2.0)
    depth = rng.uniform(0.7, 0.85)
    seat_h = rng.uniform(0.35, 0.42)
    seat_thick = rng.uniform(0.1, 0.14)
    base_h = seat_h - seat_thick
    has_arm = rng.random() < 0.6
    arm_w = 0.08
    arm_h = rng.uniform(0.12, 0.2)

    hw, hd = width / 2, depth / 2
    upholstery = mat_fabric(rng)
    leg_mat = mat_wood(rng) if rng.random() < 0.6 else mat_metal(rng)

    objects = []


    # Ножки
    leg_r = 0.02
    leg_h_val = 0.05
    #base.location = (0, 0, base_h / 2 + leg_h_val)
    for sx, sy in [(-1,-1), (1,-1), (1,1), (-1,1)]:
        leg = create_cylinder(f"DaybedLeg_{sx}_{sy}", leg_r, leg_h_val*2)
        leg.location = (sx * (hw - 0.05), sy * (hd - 0.05), 0)
        leg.data.materials.append(leg_mat)
        objects.append(leg)

    base_top_z = base_h + leg_h_val


    if has_arm:
        shift = arm_w/2
        side = rng.choice([-1, 1])
    else:
        shift = 0
        side = 0


    # Основание
    base = make_mattress("DaybedBase", hw - shift, hd, base_h / 2)
    base.location = (-side*arm_w/2, 0, base_h / 2 + leg_h_val)
    base.data.materials.append(upholstery)
    objects.append(base)



    # Подушка сиденья (одна большая)
    cushion = make_mattress("DaybedCushion", hw - 0.03 - shift, hd - 0.03, seat_thick / 2)
    cushion.location = (-side*0.02, 0, base_top_z + seat_thick / 2)
    cushion.data.materials.append(mat_cushion(upholstery, rng))
    objects.append(cushion)

    # Подлокотник (один, с одной стороны)
    if has_arm:
        arm = make_mattress("DaybedArm", arm_w / 2, hd,
                           (base_top_z + seat_thick + arm_h) / 2,0.02)
        arm.location = (side * (hw - arm_w / 2), 0,
                          (base_top_z + seat_thick + arm_h) / 2)
        arm.data.materials.append(upholstery)
        objects.append(arm)

    return objects


# ============================================================
# API
# ============================================================

def generate_seating(seed, subtype='sofa'):
    rng = random.Random(seed)
    if subtype == 'single_bed':
        return _make_single_bed(rng)
    elif subtype == 'panel_bed':
        return _make_panel_bed(rng)
    elif subtype == 'double_bed':
        return _make_double_bed(rng)
    elif subtype == 'bunk_bed':
        return _make_bunk_bed(rng)
    elif subtype == 'sofa':
        return _make_sofa(rng)
    elif subtype == 'daybed':
        return _make_daybed(rng)
    else:
        return _make_sofa(rng)

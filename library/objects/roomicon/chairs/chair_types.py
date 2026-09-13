"""Генерация стульев разных типов."""

import bpy
import bmesh
import random
import math

from helpers import (
    create_box, create_prism, create_cylinder, create_disk,
    mat_wood, mat_metal, mat_fabric,
)

CHAIR_TYPES = {
    'dining': {},
    'normal': {},
    'office': {},
    'armchair': {},
    'stool': {},
    'bench': {},
}

def _smooth_cushions(obj,bevel_width=0.02,bevel_segments=3):
    bevel = obj.modifiers.new('Bevel','BEVEL')
    bevel.width = bevel_width
    bevel.segments = bevel_segments
    for p in obj.data.polygons: p.use_smooth = True



def _four_legs(name, hw, hd, leg_r, leg_h, inset, rng, mat, tapered=False, oval=False,w_diff=0):
    """4 ножки. oval=True — размещает под краем эллипса. tapered — наклон наружу."""
    legs = []
    for i, (sx, sy) in enumerate([(-1,-1), (1,-1), (1,1), (-1,1)]):
        x_diff = 0
        if sy < 0 and w_diff > 0:
            x_diff = hw*w_diff


        if oval:
            cos45 = math.cos(math.pi / 4)
            sin45 = math.sin(math.pi / 4)
            top_x = sx * (hw * cos45 - inset)
            top_y = sy * (hd * sin45 - inset)
        else:
            top_x = sx * (hw - inset - x_diff)
            top_y = sy * (hd - inset)

        if tapered:
            # Ножка наклонена наружу
            spread = leg_r * 2
            bot_x = top_x + sx * spread
            bot_y = top_y + sy * spread
            cx = (top_x + bot_x) / 2
            cy = (top_y + bot_y) / 2
            leg = create_box(f"{name}_Leg{i}", leg_r, leg_r, leg_h / 2)
            leg.location = (cx, cy, leg_h / 2)
            angle_x = math.atan2(spread, leg_h) * sy
            angle_y = -math.atan2(spread, leg_h) * sx
            leg.rotation_euler = (angle_x, angle_y, 0)
        else:
            leg = create_cylinder(f"{name}_Leg{i}", leg_r, leg_h)
            leg.location = (top_x, top_y, 0)

        leg.data.materials.append(mat)
        legs.append(leg)
    return legs


# ============================================================
# Обеденный
# ============================================================

def _make_dining(rng):
    seat_w = rng.uniform(0.40, 0.48)
    seat_d = rng.uniform(0.40, 0.45)
    seat_h = 0.46
    seat_thick = rng.uniform(0.025, 0.04)

    back_h = rng.uniform(0.38, 0.48)
    back_thick = seat_thick 
    leg_r = rng.uniform(0.015, 0.025)

    hw, hd = seat_w / 2, seat_d / 2
    wood = mat_wood(rng)

    objects = []

    # Сиденье
    seat = create_box("DiningSeat", hw, hd, seat_thick / 2,
                       cz=seat_h)
    seat.data.materials.append(wood)
    objects.append(seat)

    # Ножки
    inset = 0.02
    objects.extend(_four_legs("Dining", hw, hd, leg_r, seat_h - seat_thick / 2,
                               inset, rng, wood, tapered=rng.random() < 0.3))

    # Спинка
    back_style = rng.choice(['solid', 'slats', 'cross'])
    back_y = -hd + back_thick / 2

    if back_style == 'solid':
        back = create_box("DiningBack", hw * 0.9, back_thick / 2, back_h / 2,
                            cy=back_y, cz=seat_h + seat_thick / 2 + back_h / 2)
        back.data.materials.append(wood)
        objects.append(back)
    elif back_style == 'slats':
        n_slats = rng.randint(3, 5)
        slat_w = back_thick
        spacing = (seat_w * 0.8) / (n_slats + 1)
        for si in range(n_slats):
            sx = -hw * 0.8 + spacing * (si + 1)
            slat = create_box(f"DiningSlat{si}", slat_w / 2, back_thick / 2, back_h/2,
                                cx=sx, cy=back_y, cz=seat_h + seat_thick/2 + back_h / 2  )
            slat.data.materials.append(wood)
            objects.append(slat)
        # Верхняя перекладина
        reil_h = rng.uniform(0.02,0.03)
        rail = create_box("DiningRail", hw * 0.9, back_thick / 2, reil_h,
                            cy=back_y, cz=seat_h + seat_thick/2 + back_h + reil_h)
        rail.data.materials.append(wood)
        objects.append(rail)
    else:  # cross
        # X-образная спинка
        for dx in (-1, 1):
            cross = create_box(f"DiningCross{dx}", 0.015, back_thick / 2, back_h / 2 ,
                                cx=dx * hw * 0.3, cy=back_y,
                                cz=seat_h + seat_thick / 2 + back_h / 2)
            cross.rotation_euler = (0, 0, dx * 0.3)
            cross.data.materials.append(wood)
            objects.append(cross)
        # Верхняя/нижняя перекладины
        for pz_frac in (0.1, 0.9):
            rail = create_box(f"DiningRailX", hw * 0.85, back_thick / 2, 0.015,
                                cy=back_y, cz=seat_h + seat_thick / 2 + back_h * pz_frac)
            rail.data.materials.append(wood)
            objects.append(rail)

    return objects


def _make_normal(rng):

    slat_angle = rng.uniform(0.01,0.2)
    slat_angle2 = rng.uniform(0.04,0.2)
    w_diff = rng.uniform(0.01,0.1)
    seat_w = rng.uniform(0.40, 0.48)
    seat_d = rng.uniform(0.40, 0.45) * (1 - w_diff/2)
    seat_h = 0.46
    seat_thick = rng.uniform(0.025, 0.04)
    back_h = rng.uniform(0.38, 0.48)
    back_thick = rng.uniform(0.02, 0.03)
    leg_r = rng.uniform(0.015, 0.025)

    hw, hd = seat_w / 2, seat_d / 2
    wood = mat_wood(rng)

    objects = []

    # Сиденье

    seat = create_prism("DiningSeat", hw, hd, seat_thick / 2,diff=w_diff)
    seat.location = (0,0,seat_h)
    seat.data.materials.append(wood)
    _smooth_cushions(seat)
    objects.append(seat)

    # Ножки
    inset = 0.05
    objects.extend(_four_legs("Dining", hw, hd, leg_r, seat_h - seat_thick / 2,
                               inset, rng, wood, tapered=rng.random() < 0.3,w_diff=w_diff))

    # Спинка
    back_y = -hd + back_thick / 2

    slat_w = 0.025
    sx = hw * (1 - w_diff) * 0.6
    slat = create_box(f"DiningSlat1", slat_w / 2, back_thick / 3, back_h / 2)
    slat.location = (sx*0.8 + seat_h*math.sin(slat_angle2),back_y + back_thick/2 - back_h*math.sin(slat_angle)/2, seat_h + seat_thick / 2 + back_h / 2 - 0.01)
    slat.data.materials.append(wood)
    slat.rotation_euler = (slat_angle,slat_angle2,0)
    objects.append(slat)

    sx = -hw * (1 - w_diff) * 0.6
    slat = create_box(f"DiningSlat2", slat_w / 2, back_thick / 3, back_h / 2)
    slat.location = (sx*0.8 - seat_h*math.sin(slat_angle2),back_y + back_thick/2 - back_h*math.sin(slat_angle)/2, seat_h + seat_thick / 2 + back_h / 2 - 0.01)
    slat.data.materials.append(wood)
    slat.rotation_euler = (slat_angle,-slat_angle2,0)
    objects.append(slat)

    rail_shift = back_thick/2 - back_h*math.sin(slat_angle)/2
    # Верхняя перекладина
    rail = create_box("DiningRail", hw*0.9 + seat_h*math.sin(slat_angle2)/2, back_thick , rng.uniform(0.04,0.07))
    rail.location = (0,back_y + rail_shift - seat_h*math.sin(slat_angle)/2, seat_h + seat_thick / 2 + back_h)
    rail.rotation_euler = (slat_angle,0,0)
    rail.data.materials.append(wood)
    _smooth_cushions(rail)
    objects.append(rail)

    return objects


# ============================================================
# Офисный
# ============================================================

def _make_office(rng):
    seat_r = rng.uniform(0.2, 0.24)
    seat_h = rng.uniform(0.45, 0.55)
    seat_thick = 0.05
    back_h = rng.uniform(0.35, 0.45)
    back_w = seat_r * rng.uniform(0.85, 1.0)

    metal = mat_metal(rng)
    fabric = mat_fabric(rng)

    objects = []

    # Крестовина (5 лучей)
    base_r = rng.uniform(0.28, 0.34)
    arm_thickness = 0.01
    arm_height = 0.018
    wheel_r = 0.015
    wheel_h = 0.018
    arm_z = wheel_h + arm_height / 2

    for i in range(5):
        angle = 2 * math.pi * i / 5
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Луч: бокс вдоль X (half_len), ставим location на середину и поворачиваем
        half_len = base_r / 2
        arm = create_box(f"OfficeArm{i}",
                          half_len, arm_thickness, arm_height / 2)
        arm.location = (half_len * cos_a, half_len * sin_a, arm_z)
        arm.rotation_euler = (0, 0, angle)
        arm.data.materials.append(metal)
        objects.append(arm)

        # Колёсико
        wheel = create_cylinder(f"OfficeWheel{i}", wheel_r, wheel_h, z_offset=-wheel_h / 2)
        wheel.location = (base_r * cos_a, base_r * sin_a, wheel_r)
        # Поворот на 90° чтобы колёсико стояло на ребре, ось вращения перпендикулярна лучу
        wheel.rotation_euler = (math.pi / 2, 0, math.atan2(sin_a, cos_a))
        wheel.data.materials.append(metal)
        objects.append(wheel)

    # Центральная колонна
    col_r = rng.uniform(0.02, 0.028)
    col_base_z = wheel_h + arm_height
    col_h = seat_h - seat_thick - col_base_z
    col = create_cylinder("OfficeColumn", col_r, col_h, z_offset=col_base_z)
    col.data.materials.append(metal)
    objects.append(col)

    # Сиденье
    seat = create_disk("OfficeSeat", seat_r, seat_thick, z_offset=seat_h - seat_thick)
    seat.data.materials.append(fabric)
    objects.append(seat)

    # Спинка: овал на прямоугольном держателе
    back_angle = rng.uniform(0.08, 0.18)
    support_w = 0.025
    support_d = 0.012
    support_h_val = back_h * 0.5
    oval_thick = 0.03
    back_panel_y = -seat_r + 0.01   # спинка: у заднего края сиденья
    support_y = -seat_r             # нижняя часть держателя на краю сиденья

    # Empty-родитель для спинки+держателя (точка крепления — задний край сиденья)
    back_pivot = bpy.data.objects.new("OfficeBackPivot", None)
    back_pivot.empty_display_size = 0.01
    back_pivot.location = (0, support_y + support_w/2, seat_h)
    back_pivot.rotation_euler = (back_angle, 0, 0)
    objects.append(back_pivot)

    # Держатель (прямоугольное сечение, позади спинки)
    support = create_box("OfficeBackSupport",
                          support_w / 2, support_d / 2, support_h_val / 2)
    support.location = (0, 0, support_h_val / 2)
    support.parent = back_pivot
    support.data.materials.append(metal)
    objects.append(support)

    # Овальная спинка — строим в плоскости XZ (вертикально)
    oval_hw = back_w
    oval_hh = back_h * 0.45
    segments = 24

    bm_back = bmesh.new()
    # Две грани овала: front (Y+) и back (Y-)
    for dy in (-oval_thick / 2, oval_thick / 2):
        ring = []
        for si in range(segments):
            a = 2 * math.pi * si / segments
            x = oval_hw * math.cos(a)
            z = oval_hh * math.sin(a)
            ring.append(bm_back.verts.new((x, dy, z)))
        if dy < 0:
            bm_back.faces.new(ring[::-1])
        else:
            bm_back.faces.new(ring)

    # Боковые грани между передним и задним кольцом
    bm_back.verts.ensure_lookup_table()
    for si in range(segments):
        sj = (si + 1) % segments
        bm_back.faces.new([
            bm_back.verts[si],
            bm_back.verts[sj],
            bm_back.verts[segments + sj],
            bm_back.verts[segments + si],
        ])

    mesh_back = bpy.data.meshes.new("OfficeBackOval")
    bm_back.to_mesh(mesh_back)
    bm_back.free()
    for p in mesh_back.polygons:
        p.use_smooth = True
    mesh_back.update()

    back_obj = bpy.data.objects.new("OfficeBackOval", mesh_back)
    back_center_z = support_h_val + oval_hh * 0.3
    back_obj.location = (0, support_w, back_center_z)
    back_obj.parent = back_pivot
    back_obj.data.materials.append(fabric)
    objects.append(back_obj)

    return objects


# ============================================================
# Кресло
# ============================================================

def _make_armchair(rng):
    seat_w = rng.uniform(0.55, 0.7)
    seat_d = rng.uniform(0.5, 0.6)
    seat_h = rng.uniform(0.4, 0.45)
    seat_thick = rng.uniform(0.18, 0.32)
    back_h = rng.uniform(0.45, 0.6)
    arm_h = rng.uniform(0.2, 0.28)
    arm_w = rng.uniform(0.06, 0.1)
    leg_h = seat_h - seat_thick / 2

    hw, hd = seat_w / 2, seat_d / 2
    fabric = mat_fabric(rng)
    wood = mat_wood(rng)
    leg_r = rng.uniform(0.02, 0.03)

    objects = []

    # Сиденье (мягкое)
    seat = create_box("ArmchairSeat", hw, hd, seat_thick / 2, cz=seat_h)
    seat.data.materials.append(fabric)
    _smooth_cushions(seat)
    objects.append(seat)

    # Ножки
    style = rng.choice(['legs', 'box'])
    if style == 'legs':
        for i, (sx, sy) in enumerate([(-1,-1), (1,-1), (1,1), (-1,1)]):
            leg = create_cylinder(f"ArmLeg{i}", leg_r, leg_h)
            leg.location = (sx * (hw - 0.03), sy * (hd - 0.03), 0)
            leg.data.materials.append(wood)
            objects.append(leg)
    else:
        # Сплошные боковины
        for sx in (-1, 1):
            panel = create_box(f"ArmPanel{sx}", 0.025, hd, leg_h / 2,
                                cx=sx * hw, cz=leg_h / 2)
            panel.data.materials.append(wood)
            _smooth_cushions(panel)
            objects.append(panel)

    # Спинка (наклонная, мягкая)
    back_angle = rng.uniform(0.08, 0.18)
    back = create_box("ArmchairBack", hw, 0.04, back_h / 2,
                        cy=-hd + 0.03,
                        cz=seat_h + seat_thick / 2 + back_h / 2)
    back.rotation_euler = (back_angle, 0, 0)
    back.data.materials.append(fabric)
    _smooth_cushions(back)
    objects.append(back)

    # Подлокотники
    arm_z = seat_h + seat_thick / 2 + arm_h / 2
    for sx in (-1, 1):
        arm = create_box(f"ArmchairArm{sx}", arm_w / 2, hd * 0.8, arm_h / 2,
                           cx=sx * (hw - arm_w / 2), cz=arm_z)
        arm.data.materials.append(fabric)
        _smooth_cushions(arm)
        objects.append(arm)

    return objects


# ============================================================
# Табурет
# ============================================================

def _make_stool(rng):
    seat_r = rng.uniform(0.14, 0.18)
    seat_h = 0.46
    seat_thick = rng.uniform(0.025, 0.04)
    leg_r = rng.uniform(0.012, 0.02)

    shape = rng.choice(['round', 'square'])
    n_legs = rng.choice([3, 4])
    wood = mat_wood(rng)

    objects = []

    if shape == 'round':
        seat = create_disk("StoolSeat", seat_r, seat_thick,
                            z_offset=seat_h - seat_thick)
    else:
        seat = create_box("StoolSeat", seat_r, seat_r, seat_thick / 2,
                            cz=seat_h)
    seat.data.materials.append(wood)
    objects.append(seat)

    leg_h = seat_h - seat_thick / 2
    for i in range(n_legs):
        angle = 2 * math.pi * i / n_legs + math.pi / n_legs
        lx = (seat_r - 0.03) * math.cos(angle)
        ly = (seat_r - 0.03) * math.sin(angle)
        leg = create_cylinder(f"StoolLeg{i}", leg_r, leg_h)
        leg.location = (lx, ly, 0)
        leg.data.materials.append(wood)
        objects.append(leg)

    # Перекладины между ножками (опционально)
    if rng.random() < 0.6:
        brace_h = leg_h * rng.uniform(0.25, 0.4)
        for i in range(n_legs):
            j = (i + 1) % n_legs
            a1 = 2 * math.pi * i / n_legs + math.pi / n_legs
            a2 = 2 * math.pi * j / n_legs + math.pi / n_legs
            x1 = (seat_r - 0.03) * math.cos(a1)
            y1 = (seat_r - 0.03) * math.sin(a1)
            x2 = (seat_r - 0.03) * math.cos(a2)
            y2 = (seat_r - 0.03) * math.sin(a2)
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            dist = math.sqrt((x2-x1)**2 + (y2-y1)**2) / 2
            ang = math.atan2(y2-y1, x2-x1)
            brace = create_box(f"StoolBrace{i}", dist, 0.008, 0.008)
            brace.location = (cx, cy, brace_h)
            brace.rotation_euler = (0, 0, ang)
            brace.data.materials.append(wood)
            objects.append(brace)

    return objects


# ============================================================
# Скамья
# ============================================================

def _make_bench(rng):
    width = rng.uniform(1.0, 1.5)
    depth = rng.uniform(0.35, 0.45)
    seat_h = 0.46
    seat_thick = rng.uniform(0.03, 0.05)
    has_back = rng.random() < 0.4
    back_h = rng.uniform(0.3, 0.4) if has_back else 0

    hw, hd = width / 2, depth / 2
    leg_r = rng.uniform(0.02, 0.035)
    wood = mat_wood(rng)

    objects = []

    # Сиденье
    seat = create_box("BenchSeat", hw, hd, seat_thick / 2, cz=seat_h)
    seat.data.materials.append(wood)
    objects.append(seat)

    # Ножки (4 или 6)
    leg_h = seat_h - seat_thick / 2
    n_pairs = 2 if width < 1.2 else 3
    for pi in range(n_pairs):
        lx = -hw + 0.05 + (width - 0.1) * pi / max(n_pairs - 1, 1)
        for sy in (-1, 1):
            ly = sy * (hd - 0.03)
            leg = create_box(f"BenchLeg_{pi}_{sy}", leg_r, leg_r, leg_h / 2,
                              cx=lx, cy=ly, cz=leg_h / 2)
            leg.data.materials.append(wood)
            objects.append(leg)

    # Спинка
    if has_back:
        back = create_box("BenchBack", hw * 0.95, 0.025, back_h / 2,
                            cy=-hd + 0.02, cz=seat_h + seat_thick / 2 + back_h / 2)
        back.data.materials.append(wood)
        objects.append(back)

    return objects


# ============================================================
# API
# ============================================================

def generate_chair(seed, subtype='dining'):
    rng = random.Random(seed)
    if subtype == 'dining':
        return _make_dining(rng)
    elif subtype == 'normal':
        return _make_normal(rng)
    elif subtype == 'office':
        return _make_office(rng)
    elif subtype == 'armchair':
        return _make_armchair(rng)
    elif subtype == 'stool':
        return _make_stool(rng)
    elif subtype == 'bench':
        return _make_bench(rng)
    else:
        return _make_dining(rng)

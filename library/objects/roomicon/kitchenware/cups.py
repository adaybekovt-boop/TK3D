"""Процедурная генерация чашек и кружек (spin + ручка)."""

import bpy
import bmesh
import math
import random

from plates import _interpolate_profile, create_ceramic_material
from vases import _create_spin_object

SPIN_SEGMENTS = 48
PROFILE_SEGMENTS = 16
handle_profile_segments = 8


# ============================================================
# Профили чашек
# ============================================================

def _coffee_cup_profile(rng, radius, height, thickness):
    """Кофейная чашка: слегка расширяющаяся кверху, тонкие стенки."""
    base_r = radius * rng.uniform(0.7, 0.82)
    top_r = radius
    bottom_thick = thickness * rng.uniform(1.8, 2.5)

    inner = [
        (0, bottom_thick),
        (base_r - thickness, bottom_thick),
        (base_r - thickness + (top_r - base_r) * 0.4, height * 0.4),
        (top_r - thickness, height * 0.9),
        (top_r - thickness, height),
    ]
    outer = [
        (0, 0),
        (base_r, 0),
        (base_r + (top_r - base_r) * 0.4, height * 0.4),
        (top_r, height * 0.9),
        (top_r, height),
    ]
    return inner, outer

def _tea_cup_profile(rng, radius, height, thickness):
    """Кофейная чашка: слегка расширяющаяся кверху, тонкие стенки."""
    base_r = radius * rng.uniform(0.3, 0.52)
    top_r = radius
    bottom_thick = thickness * rng.uniform(1.8, 2.5)

    base_h = height/6

    inner = [
        (0, base_h),
        (base_r/2, base_h),
        (base_r, base_h + bottom_thick),

        #(base_r - thickness, bottom_thick),
        #(base_r - thickness + (top_r - base_r) * 0.4, height * 0.4),
        (top_r - thickness, height * 0.9),
        (top_r - thickness, height),
    ]
    outer = [
        (0, 0),
        (base_r/2, 0),
        (base_r, 0),
        (base_r, base_h),
        (base_r * 1.1, base_h),
        (radius * 0.7, height * 0.3),
        (radius * 0.9, height * 0.6),
        #(base_r + (top_r - base_r) * 0.4, height * 0.4),
        (top_r, height * 0.9),
        (top_r, height),
    ]
    return inner, outer


def _mug_profile(rng, radius, height, thickness):
    """Кружка: цилиндрическая, толстые стенки."""
    base_r = radius * rng.uniform(0.9, 0.98)
    top_r = radius
    bottom_thick = thickness * rng.uniform(2.5, 3.5)

    inner = [
        (0, bottom_thick),
        (base_r - thickness, bottom_thick),
        (top_r - thickness, height),
    ]
    outer = [
        (0, 0),
        (base_r, 0),
        (top_r, height),
    ]
    return inner, outer


# ============================================================
# Ручка (трубка вдоль дуги)
# ============================================================

HANDLE_PROFILE_SEGMENTS = 8  # сечение трубки


def _catmull_rom_interp(points, segments_per_span=8):
    """Catmull-Rom интерполяция списка (y, z) точек."""
    result = []
    n = len(points)
    for i in range(n - 1):
        p0 = points[max(i - 1, 0)]
        p1 = points[i]
        p2 = points[i + 1]
        p3 = points[min(i + 2, n - 1)]
        for j in range(segments_per_span):
            t = j / segments_per_span
            t2 = t * t
            t3 = t2 * t
            y = 0.5 * ((2*p1[0]) + (-p0[0]+p2[0])*t + (2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*t2 + (-p0[0]+3*p1[0]-3*p2[0]+p3[0])*t3)
            z = 0.5 * ((2*p1[1]) + (-p0[1]+p2[1])*t + (2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*t2 + (-p0[1]+3*p1[1]-3*p2[1]+p3[1])*t3)
            result.append((y, z))
    result.append(points[-1])
    return result

def _create_profile_handle(bm, path, width, thickness, n_sides=4):
    """Строит ручку как трубку с полигональным сечением вдоль пути.

    Args:
        bm: bmesh для добавления геометрии
        path: список точек [(y, z), ...] — профиль ручки в плоскости YZ
        width: ширина сечения (по X)
        thickness: толщина сечения (перпендикулярно пути)
        n_sides: количество сторон сечения (4=прямоугольник, 6=шестиугольник)
    """
    hw = width / 2
    ht = thickness / 2

    path = _catmull_rom_interp(path,segments_per_span=2)
    # Профиль сечения (в локальных координатах: X — ширина, перпенд — толщина)
    profile = []
    for i in range(n_sides):
        angle = 2 * math.pi * i / n_sides + math.pi / n_sides  # поворот чтобы грань была плоской снизу
        px = hw * math.cos(angle)
        pt = ht * math.sin(angle)
        profile.append((px, pt))

    rings = []

    for idx in range(len(path)):
        py, pz = path[idx]

        # Направление пути (tangent) для ориентации сечения
        if idx < len(path) - 1:
            dy = path[idx + 1][0] - py
            dz = path[idx + 1][1] - pz
        else:
            dy = py - path[idx - 1][0]
            dz = pz - path[idx - 1][1]

        seg_len = math.sqrt(dy * dy + dz * dz)
        if seg_len < 1e-8:
            dy, dz = 0, 1
        else:
            dy /= seg_len
            dz /= seg_len

        # Нормаль к пути (перпендикуляр в плоскости YZ)
        ny, nz = -dz, dy

        # Строим кольцо вершин
        ring = []
        for px, pt in profile:
            vx = px  # ширина по X
            vy = py + ny * pt
            vz = pz + nz * pt
            ring.append(bm.verts.new((vx, vy, vz)))
        rings.append(ring)

    # Грани между кольцами
    for i in range(len(rings) - 1):
        for j in range(n_sides):
            j_next = (j + 1) % n_sides
            bm.faces.new([
                rings[i][j], rings[i][j_next],
                rings[i + 1][j_next], rings[i + 1][j],
            ])

    # Торцевые крышки
    if len(rings) > 1:
        bm.faces.new(rings[0][::-1])
        bm.faces.new(rings[-1])

def _create_handle_tea(bm, cup_radius, cup_height, thickness, rng, outer=False):
    """Угловатая ручка из профиля с точками изгиба."""
    handle_w = thickness * rng.uniform(2.5, 4.8)
    handle_t = thickness * rng.uniform(1.4, 2.6)

    # Точки крепления к чашке
    attach_top_z = cup_height * rng.uniform(0.78, 0.88)
    attach_bot_z = cup_height * rng.uniform(0.2, 0.35)

    # Выступ ручки от чашки
    protrusion = rng.uniform(0.015, 0.025)

    # Нижний крепёж чуть ближе к чашке
    bot_protrusion = protrusion * rng.uniform(0.4, 0.6)

    # Профиль ручки (y, z) — от верхнего крепления к нижнему
    mid_z = (attach_top_z + attach_bot_z) / 2
    TEA_HANDLE_PROFILES = [
        (
            (cup_radius * 0.9, attach_top_z),                          # крепление сверху
            (cup_radius + protrusion * 0.6, attach_top_z * 1.07),  # изгиб наружу
            (cup_radius + protrusion * 0.87, attach_top_z * 0.98),  
            (cup_radius + protrusion , attach_top_z * 0.80),  
            (cup_radius + protrusion * 0.8 , attach_top_z * 0.60),  
            (cup_radius + protrusion * 0.4, attach_top_z * 0.5),  # изгиб к чашке
            (outer[5][0]*0.9, outer[5][1])                          # крепление снизу
        ),
        (
            (cup_radius * 0.95, attach_top_z),                          # крепление сверху
            (cup_radius + protrusion * 0.95, attach_top_z ),  # изгиб наружу
            (cup_radius + protrusion , attach_top_z * 0.90),
            #(cup_radius + protrusion * 0.87, attach_top_z * 0.98),  
            #(cup_radius + protrusion , attach_top_z * 0.80),  
            #(cup_radius + protrusion * 0.8 , attach_top_z * 0.60),  
            (cup_radius + protrusion * 0.2, attach_top_z * 0.5),  # изгиб к чашке
            (outer[5][0]*0.9, outer[5][1])                          # крепление снизу
        ),
        (
            (cup_radius * 0.95, attach_top_z),                          # крепление сверху
            (cup_radius + protrusion * 0.95, attach_top_z ),  # изгиб наружу
            (cup_radius + protrusion , attach_top_z * 0.80),
            (cup_radius + protrusion , attach_top_z * 0.55),
            (cup_radius + protrusion * 0.7 , attach_top_z * 0.40),
            #(cup_radius + protrusion * 0.2, attach_top_z * 0.5),  # изгиб к чашке
            (outer[5][0]*0.9, outer[5][1])                          # крепление снизу
        ),
        (
            (cup_radius * 0.95, attach_top_z),                          # крепление сверху
            (cup_radius + protrusion * 0.95, attach_top_z * 0.9),  # изгиб наружу
            (cup_radius + protrusion , attach_top_z * 0.55),
            (cup_radius + protrusion * 0.5 , attach_top_z * 0.40),
            #(cup_radius + protrusion * 0.2, attach_top_z * 0.5),  # изгиб к чашке
            (outer[5][0]*0.9, outer[5][1])                          # крепление снизу
        )
    ]



    path = rng.choice(TEA_HANDLE_PROFILES)

    n_sides = rng.choice([7, 9])
    _create_profile_handle(bm, path, handle_w, handle_t, n_sides=n_sides)

def _create_handle(bm, cup_radius, cup_height, thickness, rng,outer=False):
    """
    создаёт ручку как гладкую трубку (circle profile вдоль catmull-rom дуги).
    ручка в плоскости yz, крепится к чаше при y=cup_radius.
    """
    tube_radius = thickness * rng.uniform(0.8, 1.2)

    attach_top = cup_height * rng.uniform(0.78, 0.9)
    attach_bottom = cup_height * rng.uniform(0.18, 0.32)
    protrusion = cup_radius * rng.uniform(0.4, 0.6)

    # точки привязки — на поверхности чаши (y = cup_radius)
    if outer:
        bottom = outer[1][0] * 1.04
    else:
        bottom = cup_radius - thickness * 0.5
    arc_points = [
        (cup_radius - thickness * 0.5, attach_top),
        (cup_radius + protrusion * 0.6, attach_top - (attach_top - attach_bottom) * 0.15),
        (cup_radius + protrusion, (attach_top + attach_bottom) / 2),
        (cup_radius + protrusion * 0.6, attach_bottom + (attach_top - attach_bottom) * 0.15),
        (bottom, attach_bottom),
    ]

    path = _catmull_rom_interp(arc_points, segments_per_span=6)

    # строим трубку: на каждой точке пути — кольцо вершин
    rings = []
    n_prof = handle_profile_segments

    for idx in range(len(path)):
        py, pz = path[idx]

        # направление пути (tangent) для ориентации сечения
        if idx < len(path) - 1:
            dy = path[idx + 1][0] - py
            dz = path[idx + 1][1] - pz
        else:
            dy = py - path[idx - 1][0]
            dz = pz - path[idx - 1][1]

        length = math.sqrt(dy * dy + dz * dz)
        if length < 1e-8:
            dy, dz = 0, 1
        else:
            dy /= length
            dz /= length

        # нормаль и бинормаль (tangent в плоскости yz, нормаль в x и перпендикуляр в yz)
        # tangent = (0, dy, dz), normal = (1, 0, 0), binormal = (0, -dz, dy)
        ring = []
        for j in range(n_prof):
            angle = 2 * math.pi * j / n_prof
            # смещение по нормали и бинормали
            nx = tube_radius * math.cos(angle)
            nb = tube_radius * math.sin(angle)
            vx = nx
            vy = py + nb * (-dz)
            vz = pz + nb * dy
            ring.append(bm.verts.new((vx, vy, vz)))
        rings.append(ring)

    # соединяем кольца гранями
    for i in range(len(rings) - 1):
        for j in range(n_prof):
            j_next = (j + 1) % n_prof
            v0 = rings[i][j]
            v1 = rings[i][j_next]
            v2 = rings[i + 1][j_next]
            v3 = rings[i + 1][j]
            try:
                bm.faces.new([v0, v1, v2, v3])
            except valueerror:
                pass

    # закрываем торцы
    try:
        bm.faces.new(rings[0][::-1])
    except valueerror:
        pass
    try:
        bm.faces.new(rings[-1])
    except valueerror:
        pass


def create_cup_with_handle(name, profile_inner, profile_outer, cup_radius, cup_height, thickness, rng,cup_type):
    """Создаёт чашку (spin) + ручку."""
    bm = bmesh.new()

    # Чаша — spin
    inner = _interpolate_profile(profile_inner, PROFILE_SEGMENTS)
    outer = _interpolate_profile(profile_outer, PROFILE_SEGMENTS)
    outer_rev = list(reversed(outer))
    profile = inner + outer_rev

    profile_verts = []
    for r, z in profile:
        profile_verts.append(bm.verts.new((max(0, r), 0, z)))

    for i in range(len(profile_verts) - 1):
        bm.edges.new((profile_verts[i], profile_verts[i + 1]))
    bm.edges.new((profile_verts[-1], profile_verts[0]))

    bmesh.ops.spin(
        bm,
        geom=bm.edges[:] + bm.verts[:],
        cent=(0, 0, 0),
        axis=(0, 0, 1),
        angle=math.pi * 2,
        steps=SPIN_SEGMENTS,
        use_duplicate=False,
    )

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)

    # Ручка
    if cup_type=='tea':
        _create_handle_tea(bm, cup_radius, cup_height, thickness, rng,outer=profile_outer)
    else:
        _create_handle(bm, cup_radius, cup_height, thickness, rng,outer=profile_outer)

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    for poly in mesh.polygons:
        poly.use_smooth = True
    mesh.update()

    return bpy.data.objects.new(name, mesh)


# ============================================================
# Цвета
# ============================================================

CUP_COLORS = [
    ("White", (0.95, 0.93, 0.9, 1.0), 0.25),
    ("Cream", (0.93, 0.88, 0.78, 1.0), 0.3),
    ("NavyBlue", (0.1, 0.15, 0.3, 1.0), 0.2),
    ("Red", (0.6, 0.12, 0.1, 1.0), 0.25),
    ("ForestGreen", (0.15, 0.3, 0.15, 1.0), 0.25),
    ("Gray", (0.5, 0.5, 0.5, 1.0), 0.2),
]


# ============================================================
# Публичный API
# ============================================================

CUP_TYPES = {
    'coffee': {
        'profile_fn': _coffee_cup_profile,
        'radius': (0.035, 0.042),
        'height': (0.06, 0.075),
        'thickness': (0.0025, 0.004),
    },
    'tea': {
        'profile_fn': _tea_cup_profile,
        'radius': (0.045, 0.062),
        'height': (0.05, 0.085),
        'thickness': (0.0025, 0.004),
    },
    'mug': {
        'profile_fn': _mug_profile,
        'radius': (0.038, 0.045),
        'height': (0.085, 0.10),
        'thickness': (0.004, 0.006),
    },
}


def _create_saucer(name, radius, rng):
    """Блюдце — плоская тарелка через spin."""
    bm = bmesh.new()

    # Профиль блюдца (сечение): плоское дно, слегка приподнятый край
    h = 0.012  # высота края
    t = 0.003  # толщина
    inner = [
        (0, t),
        (radius * 0.15, t),
        (radius * 0.6, t * 1.2),
        (radius * 0.85, t + h * 0.3),
        (radius * 0.97, t + h),
        (radius, t + h),
    ]
    outer = [
        (0, 0),
        (radius * 0.15, 0),
        (radius * 0.6, 0),
        (radius * 0.85, h * 0.2),
        (radius, h),
    ]

    profile_inner = _interpolate_profile(inner, PROFILE_SEGMENTS)
    profile_outer = _interpolate_profile(outer, PROFILE_SEGMENTS)
    profile = profile_inner + list(reversed(profile_outer))

    profile_verts = [bm.verts.new((max(0, r), 0, z)) for r, z in profile]
    for i in range(len(profile_verts) - 1):
        bm.edges.new((profile_verts[i], profile_verts[i + 1]))
    bm.edges.new((profile_verts[-1], profile_verts[0]))

    bmesh.ops.spin(bm, geom=bm.edges[:] + bm.verts[:],
                   cent=(0, 0, 0), axis=(0, 0, 1),
                   angle=math.pi * 2, steps=SPIN_SEGMENTS, use_duplicate=False)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.update()
    return bpy.data.objects.new(name, mesh)


def generate_cup(seed, cup_type='coffee', color_idx=None):
    """Генерирует чашку/кружку с ручкой. Tea — с блюдцем (50%)."""
    rng = random.Random(seed)
    spec = CUP_TYPES[cup_type]

    radius = rng.uniform(*spec['radius'])
    height = rng.uniform(*spec['height'])
    thickness = rng.uniform(*spec['thickness'])

    inner, outer = spec['profile_fn'](rng, radius, height, thickness)
    name = f"Cup_{cup_type}_{seed}"
    obj = create_cup_with_handle(name, inner, outer, radius, height, thickness, rng, cup_type)

    if color_idx is None:
        color_idx = rng.randint(0, len(CUP_COLORS) - 1)
    color_name, color, roughness = CUP_COLORS[color_idx]
    mat = create_ceramic_material(f"M_Cup_{color_name}", color, roughness)
    obj.data.materials.append(mat)

    objects = [obj]

    # Блюдце для чайной чашки (50% шанс)
    if cup_type == 'tea' and rng.random() < 0.5:
        saucer_r = radius * rng.uniform(1.1, 1.3)
        saucer = _create_saucer(f"Saucer_{seed}", saucer_r, rng)
        saucer.data.materials.append(mat)  # тот же материал что и чашка
        # Чашку поднимаем на высоту блюдца
        saucer_h = 0.003  # высота края + толщина
        obj.location.z += saucer_h
        objects.append(saucer)

    return objects

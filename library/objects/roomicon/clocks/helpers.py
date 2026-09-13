"""Общие утилиты для генерации часов: циферблат, стрелки, материалы."""

import bpy
import bmesh
import math

from common.shared_geometry import create_box, create_cylinder
from common.shared_materials import get_or_create_mat, setup_principled


# ============================================================
# Геометрия
# ============================================================

def create_clock_face(name, radius, tick_depth, rng):
    """
    Создаёт циферблат: фоновый диск + 12 засечек.
    Всё в плоскости XZ, лицевая сторона +Y.
    Возвращает список объектов.
    """
    objects = []

    # Фоновый диск
    face_disk = create_cylinder(f"{name}_Face", radius * 0.95, 0.003, z_offset=0)
    face_disk.rotation_euler = (math.pi / 2, 0, 0)  # лежит в XZ
    objects.append(face_disk)

    # Засечки
    for i in range(12):
        angle = math.pi / 2 - (2 * math.pi * i / 12)  # 12 = верх
        is_major = (i % 3 == 0)

        tick_len = radius * (0.12 if is_major else 0.07)
        tick_w = radius * (0.02 if is_major else 0.012)
        tick_r = radius * 0.82  # расстояние от центра

        tx = tick_r * math.cos(angle)
        tz = tick_r * math.sin(angle)

        tick = create_box(f"{name}_Tick{i}",
                          tick_w / 2, tick_depth / 2, tick_len / 2,
                          cx=tx, cy=0, cz=tz)
        tick.rotation_euler = (0, angle - math.pi / 2, 0)  # ??? нет, нужен другой подход

        # Проще: засечка как вытянутый бокс, повёрнутый к центру
        # Пересоздадим правильно
        bpy.data.objects.remove(tick, do_unlink=True)

        bm = bmesh.new()
        # Засечка вдоль радиуса: от (tick_r - tick_len/2) до (tick_r + tick_len/2)
        r_inner = tick_r - tick_len / 2
        r_outer = tick_r + tick_len / 2

        for r in (r_inner, r_outer):
            for dw in (-tick_w / 2, tick_w / 2):
                for dd in (-tick_depth / 2, tick_depth / 2):
                    x = r * math.cos(angle) + dw * (-math.sin(angle))
                    z = r * math.sin(angle) + dw * math.cos(angle)
                    bm.verts.new((x, dd, z))

        vs = bm.verts
        vs.ensure_lookup_table()
        faces_idx = [
            (0, 1, 3, 2), (4, 6, 7, 5),
            (0, 4, 5, 1), (2, 3, 7, 6),
            (0, 2, 6, 4), (1, 5, 7, 3),
        ]
        for f in faces_idx:
            bm.faces.new([vs[j] for j in f])

        mesh = bpy.data.meshes.new(f"{name}_Tick{i}")
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
        tick = bpy.data.objects.new(f"{name}_Tick{i}", mesh)
        objects.append(tick)

    return objects


def create_hands(name, radius, depth, hour, minute):
    """
    Создаёт стрелки часов в плоскости XZ, лицевая +Y.
    hour: 0-11 (позиция часовой), minute: 0-59.
    """
    objects = []
    y_off = depth * 0.6  # чуть перед циферблатом

    # Часовая
    hour_angle = math.pi / 2 - (2 * math.pi * (hour + minute / 60) / 12)
    hour_len = radius * 0.45
    hour_w = radius * 0.035

    h_obj = _make_hand(f"{name}_Hour", hour_len, hour_w, 0.004, hour_angle, y_off)
    objects.append(h_obj)

    # Минутная
    min_angle = math.pi / 2 - (2 * math.pi * minute / 60)
    min_len = radius * 0.65
    min_w = radius * 0.02

    m_obj = _make_hand(f"{name}_Minute", min_len, min_w, 0.003, min_angle, y_off + 0.001)
    objects.append(m_obj)

    # Центральная ось
    hub = create_cylinder(f"{name}_Hub", radius * 0.025, 0.006, z_offset=0)
    hub.location = (0, y_off + 0.002, 0)
    hub.rotation_euler = (math.pi / 2, 0, 0)
    objects.append(hub)

    return objects


def _make_hand(name, length, width, thickness, angle, y_offset):
    """Стрелка: вытянутый бокс от центра наружу по angle."""
    bm = bmesh.new()

    # От центра (маленький хвостик) до кончика
    tail = length * 0.15
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    # 4 точки вдоль стрелки: хвост, центр, середина, кончик
    points_along = [-tail, 0, length * 0.6, length]
    widths = [width * 0.8, width, width * 0.7, width * 0.15]  # сужается к кончику

    rings = []
    for dist, w in zip(points_along, widths):
        px = dist * cos_a
        pz = dist * sin_a
        hw = w / 2
        ht = thickness / 2
        # Перпендикуляр к стрелке
        nx = -sin_a
        nz = cos_a

        ring = []
        for dw in (-hw, hw):
            for dd in (-ht, ht):
                ring.append(bm.verts.new((px + dw * nx, y_offset + dd, pz + dw * nz)))
        rings.append(ring)

    # Соединяем секции
    for i in range(len(rings) - 1):
        r0, r1 = rings[i], rings[i + 1]
        # 4 вершины в каждом кольце: 0=(-w,-t), 1=(+w,-t), 2=(-w,+t), 3=(+w,+t)
        faces_idx = [
            (0, 1, 1, 0),  # будем делать вручную
        ]
        # верх
        bm.faces.new([r0[2], r0[3], r1[3], r1[2]])
        # низ
        bm.faces.new([r0[0], r1[0], r1[1], r0[1]])
        # бок 1
        bm.faces.new([r0[0], r0[2], r1[2], r1[0]])
        # бок 2
        bm.faces.new([r0[1], r1[1], r1[3], r0[3]])

    # Торцы
    bm.faces.new([rings[0][0], rings[0][1], rings[0][3], rings[0][2]])
    bm.faces.new([rings[-1][0], rings[-1][2], rings[-1][3], rings[-1][1]])

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return bpy.data.objects.new(name, mesh)


def create_glass_cover(name, radius, depth):
    """Стеклянный диск перед циферблатом."""
    glass = create_cylinder(name, radius * 0.96, 0.002, z_offset=0)
    glass.rotation_euler = (math.pi / 2, 0, 0)
    glass.location = (0, depth * 0.8, 0)
    return glass


# ============================================================
# Материалы
# ============================================================

def mat_clock_body(style='metal', color=None):
    """Корпус часов."""
    if style == 'metal':
        c = color or (0.6, 0.6, 0.62, 1.0)
        mat = get_or_create_mat(f"M_ClockBody_{style}")
        return setup_principled(mat, c, roughness=0.3, metallic=1.0, specular=0.8)
    elif style == 'wood':
        c = color or (0.4, 0.25, 0.12, 1.0)
        mat = get_or_create_mat(f"M_ClockBody_{style}")
        return setup_principled(mat, c, roughness=0.5, metallic=0.0, specular=0.3)
    else:  # plastic
        c = color or (0.15, 0.15, 0.15, 1.0)
        mat = get_or_create_mat(f"M_ClockBody_{style}")
        return setup_principled(mat, c, roughness=0.4, metallic=0.0, specular=0.4)


def mat_clock_face(color=None):
    """Циферблат."""
    c = color or (0.95, 0.93, 0.9, 1.0)
    mat = get_or_create_mat("M_ClockFace")
    return setup_principled(mat, c, roughness=0.8, specular=0.1)


def mat_clock_hands(color=None):
    """Стрелки и засечки."""
    c = color or (0.08, 0.08, 0.08, 1.0)
    mat = get_or_create_mat("M_ClockHands")
    return setup_principled(mat, c, roughness=0.4, metallic=0.5, specular=0.5)


def mat_clock_glass():
    """Стекло циферблата."""
    mat = get_or_create_mat("M_ClockGlass")
    mat.blend_method = 'HASHED'
    tree = mat.node_tree
    for n in list(tree.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            tree.nodes.remove(n)
    output = [n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    output.location = (500, 0)
    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (200, 0)
    bsdf.inputs['Base Color'].default_value = (0.97, 0.98, 1.0, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.05
    bsdf.inputs['IOR'].default_value = 1.5
    bsdf.inputs['Transmission Weight'].default_value = 0.9
    bsdf.inputs['Alpha'].default_value = 0.2
    bsdf.inputs['Specular IOR Level'].default_value = 0.5
    tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat


# Варианты стилей
BODY_STYLES = [
    ('metal', (0.6, 0.6, 0.62, 1.0)),
    ('metal', (0.7, 0.55, 0.25, 1.0)),   # латунь
    ('metal', (0.08, 0.08, 0.08, 1.0)),   # чёрный металл
    ('wood', (0.4, 0.25, 0.12, 1.0)),     # тёмное дерево
    ('wood', (0.55, 0.38, 0.2, 1.0)),     # светлое дерево
    ('plastic', (0.15, 0.15, 0.15, 1.0)), # чёрный пластик
    ('plastic', (0.9, 0.9, 0.88, 1.0)),   # белый пластик
]

FACE_COLORS = [
    (0.95, 0.93, 0.9, 1.0),   # белый
    (0.9, 0.87, 0.78, 1.0),   # кремовый
    (0.1, 0.1, 0.1, 1.0),     # чёрный
]

HANDS_COLORS = [
    (0.08, 0.08, 0.08, 1.0),  # чёрный
    (0.7, 0.55, 0.25, 1.0),   # золотой
    (0.7, 0.7, 0.72, 1.0),    # серебряный
]

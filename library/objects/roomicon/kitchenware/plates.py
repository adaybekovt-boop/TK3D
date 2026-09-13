"""Процедурная генерация тарелок через тело вращения (bmesh spin)."""

import bpy
import bmesh
import math
import random


# ============================================================
# Профили сечений
# ============================================================

def _interpolate_profile(points, segments=32):
    """
    Интерполирует профиль через контрольные точки (Catmull-Rom).
    points: [(r, z), ...] — радиус и высота
    Возвращает список (r, z) с плавными переходами.
    """
    result = []
    n = len(points)

    for i in range(n - 1):
        p0 = points[max(i - 1, 0)]
        p1 = points[i]
        p2 = points[i + 1]
        p3 = points[min(i + 2, n - 1)]

        for j in range(segments):
            t = j / segments
            t2 = t * t
            t3 = t2 * t

            # Catmull-Rom
            r = 0.5 * (
                (2 * p1[0]) +
                (-p0[0] + p2[0]) * t +
                (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
            )
            z = 0.5 * (
                (2 * p1[1]) +
                (-p0[1] + p2[1]) * t +
                (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
            )
            result.append((max(0, r), z))

    result.append(points[-1])
    return result


def _dinner_plate_profile(rng, radius, rim_height, thickness):
    """Профиль обеденной тарелки: плоское дно + пологий подъём + бортик."""
    # Контрольные точки (r, z) — от центра к краю, внутренняя поверхность
    inner_bottom_r = radius * rng.uniform(0.15, 0.25)
    curve_start_r = radius * rng.uniform(0.55, 0.7)
    rim_start_r = radius * rng.uniform(0.82, 0.88)
    rim_width = rng.uniform(0.001,0.003)

    inner = [
        (0, thickness),                          # центр дна (внутри)
        (inner_bottom_r, thickness),             # плоское дно
        (curve_start_r, thickness * 1.3),        # начало подъёма
        (rim_start_r, rim_height * 0.6),         # переход к бортику
        (radius * 0.95, rim_height * 0.85),      # бортик
        (radius - rim_width, rim_height),                     # верхний край
        (radius , rim_height - 0.001),
    ]

    outer = [
        (0, 0),                                   # центр дна (снаружи)
        (inner_bottom_r, 0),                      # плоское дно
        (curve_start_r, thickness * 0.2),         # лёгкий подъём
        (rim_start_r, rim_height * 0.3),          # под бортиком
        (radius * 0.95, rim_height * 0.7),        # бортик снаружи
        (radius, rim_height - 0.001),                      # верхний край (совпадает)
    ]

    return inner, outer


def _soup_plate_profile(rng, radius, rim_height, thickness):
    """Профиль глубокой тарелки: вогнутое дно + крутой подъём + широкий бортик."""
    inner_bottom_r = radius * rng.uniform(0.12, 0.2)
    well_depth = rim_height * rng.uniform(0.5, 0.7)
    rim_start_r = radius * rng.uniform(0.6, 0.7)
    rim_width = rng.uniform(0.003,0.006)

    inner = [
        (0, thickness + well_depth * 0.1),
        (inner_bottom_r, thickness),              # дно впадины
        (rim_start_r * 0.5, thickness * 0.8),     # глубокая часть
        (rim_start_r, rim_height * 0.5),           # подъём
        (radius * 0.85, rim_height * 0.85),        # плоский бортик
        (radius - rim_width, rim_height),
        (radius, rim_height),
    ]

    outer = [
        (0, well_depth * 0.15),
        (inner_bottom_r, 0),
        (rim_start_r * 0.5, 0),
        (rim_start_r, rim_height * 0.2),
        (radius * 0.85, rim_height * 0.7),
        (radius, rim_height - 0.003),
        (radius, rim_height),
    ]

    return inner, outer


def _dessert_plate_profile(rng, radius, rim_height, thickness):
    """Профиль десертной тарелки: почти плоская с невысоким бортиком."""
    inner_bottom_r = radius * rng.uniform(0.2, 0.3)
    rim_start_r = radius * rng.uniform(0.78, 0.85)
    rim_width = rng.uniform(0.001,0.003)

    inner = [
        (0, thickness),
        (inner_bottom_r, thickness),
        (rim_start_r, thickness * 1.1),
        (radius * 0.93, rim_height * 0.7),
        (radius-rim_width, rim_height),
        (radius, rim_height),
    ]

    outer = [
        (0, 0),
        (inner_bottom_r, 0),
        (rim_start_r, thickness * 0.15),
        (radius * 0.93, rim_height * 0.4),
        (radius, rim_height),
    ]

    return inner, outer


# ============================================================
# Генерация меша
# ============================================================

SPIN_SEGMENTS = 48  # количество сегментов вращения
PROFILE_SEGMENTS = 16  # интерполяция на участок профиля


def create_plate_mesh(name, profile_inner, profile_outer, spin_segments=SPIN_SEGMENTS):
    """
    Создаёт тело вращения из внутреннего и внешнего профилей.
    Профили: списки (r, z), от центра к краю.
    """
    bm = bmesh.new()

    # Интерполируем профили
    inner = _interpolate_profile(profile_inner, PROFILE_SEGMENTS)
    outer = _interpolate_profile(profile_outer, PROFILE_SEGMENTS)

    # Строим полный профиль: outer (снизу, от края к центру) + inner (сверху, от центра к краю)
    # Разворачиваем outer чтобы шёл от края к центру
    outer_rev = list(reversed(outer))

    # Объединяем: inner (центр→край) + outer_rev (край→центр)
    # Это замкнутый профиль сечения
    profile = inner + outer_rev

    # Создаём вершины профиля в плоскости XZ (Y=0)
    profile_verts = []
    for r, z in profile:
        v = bm.verts.new((r, 0, z))
        profile_verts.append(v)

    # Создаём рёбра профиля
    for i in range(len(profile_verts) - 1):
        bm.edges.new((profile_verts[i], profile_verts[i + 1]))
    # Замыкаем
    bm.edges.new((profile_verts[-1], profile_verts[0]))

    # Spin (тело вращения)
    spin_result = bmesh.ops.spin(
        bm,
        geom=bm.edges[:] + bm.verts[:],
        cent=(0, 0, 0),
        axis=(0, 0, 1),
        angle=math.pi * 2,
        steps=spin_segments,
        use_duplicate=False,
    )

    # Удаляем дублирующиеся вершины на шве
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)

    # Пересчитываем нормали
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    # Smooth shading
    for poly in mesh.polygons:
        poly.use_smooth = True
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    return obj


# ============================================================
# Материалы
# ============================================================

def create_ceramic_material(name, color=(0.95, 0.93, 0.9, 1.0), roughness=0.25):
    """Керамика / фарфор."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree

    for n in list(tree.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            tree.nodes.remove(n)

    output = [n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    output.location = (600, 0)

    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (200, 0)
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Specular IOR Level'].default_value = 0.6
    bsdf.inputs['Coat Weight'].default_value = 0.3
    bsdf.inputs['Coat Roughness'].default_value = 0.1

    tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat


# ============================================================
# Публичный API
# ============================================================

PLATE_TYPES = {
    'dinner': {
        'profile_fn': _dinner_plate_profile,
        'radius': (0.12, 0.135),
        'rim_height': (0.02, 0.03),
        'thickness': (0.004, 0.006),
    },
    'soup': {
        'profile_fn': _soup_plate_profile,
        'radius': (0.11, 0.125),
        'rim_height': (0.035, 0.05),
        'thickness': (0.004, 0.006),
    },
    'dessert': {
        'profile_fn': _dessert_plate_profile,
        'radius': (0.09, 0.10),
        'rim_height': (0.015, 0.022),
        'thickness': (0.003, 0.005),
    },
}

# Цвета керамики
CERAMIC_COLORS = [
    ("White", (0.95, 0.93, 0.9, 1.0), 0.25),
    ("Cream", (0.93, 0.88, 0.78, 1.0), 0.3),
    ("LightBlue", (0.82, 0.87, 0.92, 1.0), 0.25),
    ("LightGray", (0.85, 0.85, 0.85, 1.0), 0.2),
    ("Terracotta", (0.75, 0.45, 0.3, 1.0), 0.45),
]


def generate_plate(seed, plate_type='dinner', color_idx=None):
    """
    Генерирует одну тарелку.
    Возвращает (obj, material_name).
    """
    rng = random.Random(seed)
    spec = PLATE_TYPES[plate_type]

    radius = rng.uniform(*spec['radius'])
    rim_height = rng.uniform(*spec['rim_height'])
    thickness = rng.uniform(*spec['thickness'])

    profile_fn = spec['profile_fn']
    inner, outer = profile_fn(rng, radius, rim_height, thickness)

    name = f"Plate_{plate_type}_{seed}"
    obj = create_plate_mesh(name, inner, outer)

    # Материал
    if color_idx is None:
        color_idx = rng.randint(0, len(CERAMIC_COLORS) - 1)
    color_name, color, roughness = CERAMIC_COLORS[color_idx]
    mat = create_ceramic_material(f"M_Ceramic_{color_name}", color, roughness)
    obj.data.materials.append(mat)

    return obj

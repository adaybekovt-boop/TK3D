"""Утилиты для генерации столов: боксы, цилиндры, spin, материалы."""

import bpy
import bmesh
import math

from common.shared_geometry import create_box, create_cylinder
from common.shared_materials import get_or_create_mat, setup_principled


# ============================================================
# Геометрия
# ============================================================


def create_disk(name, radius, thickness, z_offset=0, segments=32):
    """Диск (столешница круглая)."""
    return create_cylinder(name, radius, thickness, z_offset, segments)


def create_oval_top(name, rx, ry, thickness, z_offset=0, segments=32):
    """Овальная столешница."""
    bm = bmesh.new()
    bottom, top = [], []
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = rx * math.cos(angle)
        y = ry * math.sin(angle)
        bottom.append(bm.verts.new((x, y, z_offset)))
        top.append(bm.verts.new((x, y, z_offset + thickness)))
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new([bottom[i], bottom[j], top[j], top[i]])
    bm.faces.new(bottom[::-1])
    bm.faces.new(top)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.update()
    return bpy.data.objects.new(name, mesh)


def create_turned_leg(name, radius, height, z_offset=0, segments=16, profile_segments=8):
    """Точёная ножка (spin-профиль)."""
    bm = bmesh.new()
    r = radius
    h = height

    # Профиль сечения: утолщение внизу и вверху, сужение посередине
    profile = [
        (r * 1.2, z_offset),
        (r * 1.3, z_offset + h * 0.05),
        (r * 0.8, z_offset + h * 0.15),
        (r * 0.6, z_offset + h * 0.3),
        (r * 0.55, z_offset + h * 0.5),
        (r * 0.6, z_offset + h * 0.7),
        (r * 0.8, z_offset + h * 0.85),
        (r * 1.1, z_offset + h * 0.95),
        (r * 1.2, z_offset + h),
    ]

    verts = [bm.verts.new((pr, 0, pz)) for pr, pz in profile]
    for i in range(len(verts) - 1):
        bm.edges.new((verts[i], verts[i + 1]))

    bmesh.ops.spin(bm, geom=bm.edges[:] + bm.verts[:],
                   cent=(0, 0, 0), axis=(0, 0, 1),
                   angle=math.pi * 2, steps=segments, use_duplicate=False)
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


def create_lathe_column(name, radius, height, profile_type='classic', z_offset=0, segments=20):
    """
    Фигурная колонна (тело вращения) с разными профилями.
    profile_type: 'classic', 'baluster', 'vase', 'tapered', 'fluted'
    """
    bm = bmesh.new()
    r = radius
    h = height

    if profile_type == 'classic':
        # Классический: утолщения вверху и внизу, тонкая середина
        profile = [
            (r * 1.1, z_offset),
            (r * 1.0, z_offset + h * 0.04),
            (r * 0.7, z_offset + h * 0.12),
            (r * 0.5, z_offset + h * 0.35),
            (r * 0.45, z_offset + h * 0.5),
            (r * 0.5, z_offset + h * 0.65),
            (r * 0.7, z_offset + h * 0.88),
            (r * 1.4, z_offset + h * 0.96),
            (r * 1.3, z_offset + h),
        ]
    elif profile_type == 'baluster':
        # Балясина: грушевидное утолщение внизу
        profile = [
            (r * 1.2, z_offset),
            (r * 1.3, z_offset + h * 0.03),
            (r * 1.5, z_offset + h * 0.15),
            (r * 1.6, z_offset + h * 0.25),
            (r * 1.3, z_offset + h * 0.35),
            (r * 0.6, z_offset + h * 0.5),
            (r * 0.5, z_offset + h * 0.7),
            (r * 0.6, z_offset + h * 0.9),
            (r * 1.0, z_offset + h * 0.97),
            (r * 1.0, z_offset + h),
        ]
    elif profile_type == 'vase':
        # Вазообразный: широкая середина, узкие концы
        profile = [
            (r * 0.8, z_offset),
            (r * 0.9, z_offset + h * 0.05),
            (r * 1.2, z_offset + h * 0.2),
            (r * 1.5, z_offset + h * 0.4),
            (r * 1.5, z_offset + h * 0.55),
            (r * 1.2, z_offset + h * 0.7),
            (r * 0.8, z_offset + h * 0.85),
            (r * 0.7, z_offset + h * 0.95),
            (r * 0.8, z_offset + h),
        ]
    elif profile_type == 'tapered':
        # Конусный: широкий внизу, узкий вверху
        profile = [
            (r * 1.5, z_offset),
            (r * 1.5, z_offset + h * 0.03),
            (r * 1.2, z_offset + h * 0.15),
            (r * 0.9, z_offset + h * 0.4),
            (r * 0.7, z_offset + h * 0.65),
            (r * 0.55, z_offset + h * 0.85),
            (r * 0.5, z_offset + h * 0.95),
            (r * 0.6, z_offset + h),
        ]
    else:  # fluted — с каннелюрами (имитация через волнистый профиль)
        profile = [
            (r * 1.1, z_offset),
            (r * 1.2, z_offset + h * 0.04),
            (r * 0.8, z_offset + h * 0.1),
            (r * 0.7, z_offset + h * 0.2),
            (r * 0.75, z_offset + h * 0.3),
            (r * 0.65, z_offset + h * 0.4),
            (r * 0.7, z_offset + h * 0.5),
            (r * 0.65, z_offset + h * 0.6),
            (r * 0.7, z_offset + h * 0.7),
            (r * 0.75, z_offset + h * 0.8),
            (r * 0.8, z_offset + h * 0.9),
            (r * 1.2, z_offset + h * 0.96),
            (r * 1.1, z_offset + h),
        ]

    verts = [bm.verts.new((pr, 0, pz)) for pr, pz in profile]
    for i in range(len(verts) - 1):
        bm.edges.new((verts[i], verts[i + 1]))

    bmesh.ops.spin(bm, geom=bm.edges[:] + bm.verts[:],
                   cent=(0, 0, 0), axis=(0, 0, 1),
                   angle=math.pi * 2, steps=segments, use_duplicate=False)
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


COLUMN_PROFILES = ['classic', 'baluster', 'vase', 'tapered', 'fluted']


def create_plate_base(name, radius, thickness=0.015, segments=32):
    """Основание-тарелка (диск с бортиком)."""
    bm = bmesh.new()
    r = radius
    t = thickness
    # Профиль: плоское дно + плавный подъём к краю
    profile = [
        (0.001, 0),
        (r * 0.3, t * 0.3),
        (r * 0.7, t * 0.5),
        (r * 0.9, t * 0.8),
        (r, t),
        (r, t + 0.005),
        (r * 0.95, t + 0.005),
    ]

    verts = [bm.verts.new((pr, 0, pz)) for pr, pz in profile]
    for i in range(len(verts) - 1):
        bm.edges.new((verts[i], verts[i + 1]))

    bmesh.ops.spin(bm, geom=bm.edges[:] + bm.verts[:],
                   cent=(0, 0, 0), axis=(0, 0, 1),
                   angle=math.pi * 2, steps=segments, use_duplicate=False)
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


def create_tripod_base(name, leg_length, leg_r, center_r, rng, segments=12):
    """Трёхножник: 3 горизонтальные опоры от центра."""
    objects = []

    # Центральная втулка
    hub = create_cylinder(f"{name}_Hub", center_r, center_r * 2, z_offset=0, segments=segments)
    objects.append(hub)

    # 3 луча
    tilt = rng.uniform(0.05, 0.15)  # лёгкий наклон вниз
    for i in range(3):
        angle = 2 * math.pi * i / 3 + rng.uniform(-0.1, 0.1)

        leg = create_box(f"{name}_Leg{i}", leg_r/2, leg_r, leg_length/2)
        #leg = create_cylinder(f"{name}_Leg{i}", leg_r, leg_length, segments=segments)
        # Позиция: от центра наружу
        leg.location = ((leg_length + center_r) / 2 * math.cos(angle),
                         (leg_length  + center_r)/ 2 * math.sin(angle),
                         math.sin(tilt)*leg_length/2 + leg_r)
        # Горизонтально + лёгкий наклон
        
        leg.rotation_euler = (math.pi/2+tilt, 0, angle + math.pi / 2)
        objects.append(leg)

    return objects


# ============================================================
# Материалы
# ============================================================

def create_glass_material(name="M_GlassTop"):
    mat = get_or_create_mat(name)
    mat.blend_method = 'HASHED'
    tree = mat.node_tree
    for n in list(tree.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            tree.nodes.remove(n)
    output = [n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.95, 0.97, 1.0, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.02
    bsdf.inputs['IOR'].default_value = 1.5
    bsdf.inputs['Transmission Weight'].default_value = 0.9
    bsdf.inputs['Alpha'].default_value = 0.25
    tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat


WOOD_STYLES = [
    ("LightOak", (0.55, 0.4, 0.22, 1.0), 0.5),
    ("Birch", (0.7, 0.6, 0.45, 1.0), 0.45),
    ("DarkWalnut", (0.25, 0.15, 0.08, 1.0), 0.45),
    ("Wenge", (0.15, 0.1, 0.06, 1.0), 0.4),
    ("WhitePaint", (0.92, 0.91, 0.88, 1.0), 0.35),
    ("Pine", (0.65, 0.5, 0.3, 1.0), 0.5),
]

METAL_STYLES = [
    ("BlackMetal", (0.08, 0.08, 0.08, 1.0), 0.4),
    ("Chrome", (0.7, 0.7, 0.72, 1.0), 0.15),
    ("Brass", (0.7, 0.55, 0.25, 1.0), 0.3),
]


def mat_wood(rng):
    name, color, roughness = rng.choice(WOOD_STYLES)
    mat = get_or_create_mat(f"M_Table_{name}")
    return setup_principled(mat, color, roughness=roughness, specular=0.3)


def mat_metal(rng):
    name, color, roughness = rng.choice(METAL_STYLES)
    mat = get_or_create_mat(f"M_TableLeg_{name}")
    return setup_principled(mat, color, roughness=roughness, metallic=1.0, specular=0.8)

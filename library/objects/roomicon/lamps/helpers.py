"""Общие утилиты для генерации ламп: spin, материалы."""

import bpy
import bmesh
import math
import os
import sys

# Ensure common is importable
_generators_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if _generators_dir not in sys.path:
    sys.path.insert(0, _generators_dir)

from common.shared_materials import get_or_create_mat, clear_and_get_output


# ============================================================
# Spin (тело вращения)
# ============================================================

SPIN_SEGMENTS = 32


def catmull_rom(points, segments_per_span=8):
    """Catmull-Rom интерполяция списка (r, z) точек."""
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
            r = 0.5 * ((2*p1[0]) + (-p0[0]+p2[0])*t + (2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*t2 + (-p0[0]+3*p1[0]-3*p2[0]+p3[0])*t3)
            z = 0.5 * ((2*p1[1]) + (-p0[1]+p2[1])*t + (2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*t2 + (-p0[1]+3*p1[1]-3*p2[1]+p3[1])*t3)
            result.append((max(0, r), z))
    result.append(points[-1])
    return result


def create_spin_solid(name, profile_inner, profile_outer, spin_segments=SPIN_SEGMENTS):
    """Тело вращения из внутреннего и внешнего профиля (замкнутое сечение)."""
    bm = bmesh.new()

    inner = catmull_rom(profile_inner)
    outer = catmull_rom(profile_outer)
    profile = inner + list(reversed(outer))

    verts = [bm.verts.new((max(0, r), 0, z)) for r, z in profile]
    for i in range(len(verts) - 1):
        bm.edges.new((verts[i], verts[i + 1]))
    bm.edges.new((verts[-1], verts[0]))

    bmesh.ops.spin(bm, geom=bm.edges[:] + bm.verts[:],
                   cent=(0, 0, 0), axis=(0, 0, 1),
                   angle=math.pi * 2, steps=spin_segments, use_duplicate=False)
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


def create_spin_surface(name, profile, spin_segments=SPIN_SEGMENTS):
    """Тело вращения из одного профиля (открытая поверхность, для тонких абажуров)."""
    bm = bmesh.new()

    pts = catmull_rom(profile)
    verts = [bm.verts.new((max(0.0001, r), 0, z)) for r, z in pts]
    for i in range(len(verts) - 1):
        bm.edges.new((verts[i], verts[i + 1]))

    bmesh.ops.spin(bm, geom=bm.edges[:] + bm.verts[:],
                   cent=(0, 0, 0), axis=(0, 0, 1),
                   angle=math.pi * 2, steps=spin_segments, use_duplicate=False)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.update()

    obj = bpy.data.objects.new(name, mesh)
    # Solidify для толщины
    mod = obj.modifiers.new("Solidify", 'SOLIDIFY')
    mod.thickness = 0.002
    mod.offset = -1
    return obj


def create_cylinder(name, radius, height, z_offset=0, segments=SPIN_SEGMENTS):
    """Простой цилиндр (ножка, шнур)."""
    bm = bmesh.new()
    bottom = []
    top = []
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        bottom.append(bm.verts.new((x, y, z_offset)))
        top.append(bm.verts.new((x, y, z_offset + height)))

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


# ============================================================
# Лампочка
# ============================================================

_BULB_ENERGY = {
    'LampBulb': 50,       # tabletop classic
    'NightBulb': 20,      # tabletop nightlight
    'FloorBulb': 100,     # floor lamp
    'ArcBulb': 100,       # arc lamp
    'SconceBulb': 30,     # wall sconce
    'PendantBulb': 80,    # ceiling pendant
    'FlushBulb': 60,      # ceiling flush
}


def create_bulb(name, radius, rng, location=(0, 0, 0)):
    """Лампочка — вытянутая сфера с emission материалом + Point light.

    Args:
        name: имя объекта
        radius: базовый радиус
        rng: Random для вариативности
        location: позиция (x, y, z)

    Returns:
        (bulb_mesh, point_light) — оба объекта для включения в иерархию ассета.
    """
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=radius)
    stretch = rng.uniform(1.0, 2.0)
    for v in bm.verts:
        v.co.z *= stretch
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.update()
    bulb = bpy.data.objects.new(name, mesh)
    bulb.location = location

    # Тёплый белый emission
    mat = get_or_create_mat("M_LampBulb")
    tree = mat.node_tree
    output = clear_and_get_output(tree)
    output.location = (500, 0)
    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (200, 0)
    bsdf.inputs['Base Color'].default_value = (1.0, 0.95, 0.85, 1.0)
    bsdf.inputs['Emission Color'].default_value = (1.0, 0.95, 0.85, 1.0)
    bsdf.inputs['Emission Strength'].default_value = 3.0
    tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    bulb.data.materials.append(mat)

    # Point light at same position
    energy = _BULB_ENERGY.get(name, 50)
    light_data = bpy.data.lights.new(name + "_Light", 'POINT')
    light_data.energy = energy
    light_data.color = (1.0, 0.85, 0.66)  # ~3000K warm
    light_data.shadow_soft_size = radius * 2
    light_obj = bpy.data.objects.new(name + "_Light", light_data)
    light_obj.location = location
    light_obj['roomicon_lamp'] = True
    light_obj['base_energy'] = energy
    light_obj.hide_viewport = True
    light_obj.hide_render = True

    return bulb, light_obj


# ============================================================
# Материалы
# ============================================================

def create_metal_material(name="M_LampMetal", color=(0.6, 0.6, 0.6, 1.0), roughness=0.3):
    """Металл для ножек, креплений."""
    mat = get_or_create_mat(name)
    tree = mat.node_tree
    output = clear_and_get_output(tree)
    output.location = (500, 0)

    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (200, 0)
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Specular IOR Level'].default_value = 0.8

    tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat


def create_shade_material(name="M_LampShade", color=(0.95, 0.9, 0.82, 1.0)):
    """Ткань абажура — полупрозрачная, тёплая."""
    mat = get_or_create_mat(name)
    tree = mat.node_tree
    output = clear_and_get_output(tree)
    output.location = (500, 0)

    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (200, 0)
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = 0.8
    bsdf.inputs['Specular IOR Level'].default_value = 0.05
    bsdf.inputs['Transmission Weight'].default_value = 0.3
    bsdf.inputs['Alpha'].default_value = 0.9

    tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat


def create_glass_shade_material(name="M_GlassShade", color=(0.95, 0.97, 1.0, 1.0), roughness=0.1):
    """Стеклянный плафон."""
    mat = get_or_create_mat(name)
    mat.blend_method = 'HASHED'
    tree = mat.node_tree
    output = clear_and_get_output(tree)
    output.location = (500, 0)

    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (200, 0)
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['IOR'].default_value = 1.45
    bsdf.inputs['Transmission Weight'].default_value = 0.85
    bsdf.inputs['Alpha'].default_value = 0.35

    tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat


# Цвета металла
METAL_COLORS = [
    ("Brass", (0.7, 0.55, 0.25, 1.0), 0.3),
    ("Chrome", (0.7, 0.7, 0.72, 1.0), 0.15),
    ("BlackMetal", (0.08, 0.08, 0.08, 1.0), 0.4),
    ("Copper", (0.72, 0.45, 0.3, 1.0), 0.3),
    ("NickelMatte", (0.55, 0.55, 0.55, 1.0), 0.5),
]

# Цвета абажуров
SHADE_COLORS = [
    ("Cream", (0.95, 0.9, 0.82, 1.0)),
    ("White", (0.95, 0.95, 0.93, 1.0)),
    ("Beige", (0.85, 0.78, 0.65, 1.0)),
    ("Gray", (0.7, 0.7, 0.7, 1.0)),
    ("DarkGreen", (0.2, 0.35, 0.2, 1.0)),
]

GLASS_COLORS = [
    ("Clear", (0.95, 0.97, 1.0, 1.0), 0.05),
    ("Frosted", (0.9, 0.92, 0.95, 1.0), 0.5),
    ("Amber", (1.0, 0.85, 0.6, 1.0), 0.15),
    ("Opal", (0.95, 0.93, 0.9, 1.0), 0.6),
]

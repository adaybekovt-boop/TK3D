"""Утилиты для генерации штор."""

import bpy
import bmesh
import math

from common.shared_materials import get_or_create_mat


def create_curtain_mesh(name, width, height, folds=8, fold_depth=0.03, subdivisions_x=40, subdivisions_z=20,rng=False,noise_x=0.01,noise_y=0.02):
    """
    Создаёт штору как деформированную сетку (plane с синусоидальными складками).
    Плоскость в XZ, нормаль +Y, складки по X.
    """
    bm = bmesh.new()

    hw = width / 2

    # Сетка вершин
    verts_grid = []
    for iz in range(subdivisions_z + 1):
        row = []
        z = height * iz / subdivisions_z
        for ix in range(subdivisions_x + 1):
            x = -hw + width * ix / subdivisions_x
            if rng:
                x += rng.uniform(-noise_x,noise_x)

            # Синусоидальная деформация по Y (складки)
            fold_phase = (ix / subdivisions_x) * folds * 2 * math.pi
            # Складки сильнее в середине по высоте, слабее у карниза и подола
            height_factor = math.sin(math.pi * iz / subdivisions_z) * 0.7 + 0.3
            y = math.sin(fold_phase) * fold_depth * height_factor
            if rng:
                y += rng.uniform(-noise_y,noise_y)

            row.append(bm.verts.new((x, y, z)))
        verts_grid.append(row)

    # Грани
    for iz in range(subdivisions_z):
        for ix in range(subdivisions_x):
            v0 = verts_grid[iz][ix]
            v1 = verts_grid[iz][ix + 1]
            v2 = verts_grid[iz + 1][ix + 1]
            v3 = verts_grid[iz + 1][ix]
            bm.faces.new([v0, v1, v2, v3])

    # UV
    uv_layer = bm.loops.layers.uv.new("UVMap")
    for face in bm.faces:
        for loop in face.loops:
            co = loop.vert.co
            loop[uv_layer].uv = ((co.x + hw) / width, co.z / height)

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.update()
    return bpy.data.objects.new(name, mesh)


def create_rod(name, width, radius=0.008, segments=12):
    """Карниз (горизонтальный цилиндр вдоль X)."""
    bm = bmesh.new()
    hw = width / 2
    left, right = [], []
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        dy = radius * math.cos(angle)
        dz = radius * math.sin(angle)
        left.append(bm.verts.new((-hw - 0.03, dy, dz)))
        right.append(bm.verts.new((hw + 0.03, dy, dz)))

    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new([left[i], left[j], right[j], right[i]])
    bm.faces.new(left[::-1])
    bm.faces.new(right)

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.update()
    return bpy.data.objects.new(name, mesh)


# ============================================================
# Материалы
# ============================================================

CURTAIN_COLORS = [
    ("Cream", (0.9, 0.85, 0.75, 1.0)),
    ("DarkRed", (0.4, 0.1, 0.08, 1.0)),
    ("NavyBlue", (0.1, 0.12, 0.25, 1.0)),
    ("ForestGreen", (0.12, 0.25, 0.12, 1.0)),
    ("Gray", (0.45, 0.45, 0.45, 1.0)),
    ("Gold", (0.65, 0.5, 0.2, 1.0)),
    ("Burgundy", (0.35, 0.08, 0.1, 1.0)),
    ("Taupe", (0.5, 0.43, 0.35, 1.0)),
    ("Charcoal", (0.18, 0.18, 0.18, 1.0)),
    ("Sage", (0.5, 0.55, 0.4, 1.0)),
]

METAL_COLORS = [
    ("Brass", (0.7, 0.55, 0.25, 1.0)),
    ("BlackMetal", (0.08, 0.08, 0.08, 1.0)),
    ("Chrome", (0.7, 0.7, 0.72, 1.0)),
]


def mat_curtain(rng):
    """Плотная ткань для портьер."""
    name, color = rng.choice(CURTAIN_COLORS)
    mat = get_or_create_mat(f"M_Curtain_{name}")
    tree = mat.node_tree

    for n in list(tree.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            tree.nodes.remove(n)
    output = [n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    output.location = (600, 0)

    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (300, 0)
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = 0.8
    bsdf.inputs['Specular IOR Level'].default_value = 0.08
    bsdf.inputs['Sheen Weight'].default_value = 0.4

    # Лёгкий bump
    noise = tree.nodes.new('ShaderNodeTexNoise')
    noise.location = (-100, -200)
    noise.inputs['Scale'].default_value = 40.0
    noise.inputs['Detail'].default_value = 4.0

    bump = tree.nodes.new('ShaderNodeBump')
    bump.location = (100, -200)
    bump.inputs['Strength'].default_value = 0.02

    tc = tree.nodes.new('ShaderNodeTexCoord')
    tc.location = (-300, -200)

    tree.links.new(tc.outputs['Object'], noise.inputs['Vector'])
    tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    tree.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat


def mat_sheer():
    """Полупрозрачная тюль."""
    mat = get_or_create_mat("M_Sheer")
    mat.blend_method = 'HASHED'
    tree = mat.node_tree

    for n in list(tree.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            tree.nodes.remove(n)
    output = [n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    output.location = (600, 0)

    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (300, 0)
    bsdf.inputs['Base Color'].default_value = (0.95, 0.93, 0.9, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.7
    bsdf.inputs['Specular IOR Level'].default_value = 0.05
    bsdf.inputs['Transmission Weight'].default_value = 0.6
    bsdf.inputs['Alpha'].default_value = 0.4

    tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat


def mat_rod(rng):
    """Металл карниза."""
    name, color = rng.choice(METAL_COLORS)
    mat = get_or_create_mat(f"M_Rod_{name}")
    tree = mat.node_tree

    for n in list(tree.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            tree.nodes.remove(n)
    output = [n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    output.location = (500, 0)

    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (200, 0)
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.3
    bsdf.inputs['Specular IOR Level'].default_value = 0.8

    tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

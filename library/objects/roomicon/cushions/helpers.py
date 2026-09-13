"""Утилиты для генерации подушек."""

import bpy
import bmesh
import math

from common.shared_geometry import create_box, create_cylinder
from common.shared_materials import get_or_create_mat


def make_soft(obj, disp_strength=0.003, noise_scale=8.0):
    """Добавляет Subdivision + Displacement (Noise) для мягкости."""
    sub = obj.modifiers.new("Subdivision", 'SUBSURF')
    sub.levels = 2
    sub.render_levels = 2

    tex = bpy.data.textures.new(f"{obj.name}_Disp", type='CLOUDS')
    tex.noise_scale = noise_scale
    tex.noise_depth = 2

    disp = obj.modifiers.new("Displacement", 'DISPLACE')
    disp.texture = tex
    disp.strength = disp_strength
    disp.mid_level = 0.5


def create_cushion_rect(name, width, depth, thickness, segs_x=12, segs_y=12, rng=None):
    """Прямоугольная подушка с параболическим профилем.

    Центр — максимальная толщина, края — сходят к нулю.
    Лежит на Z=0, верхняя точка на Z=thickness.
    """
    bm = bmesh.new()
    hw, hd, ht = width / 2, depth / 2, thickness / 2

    verts_grid = []
    for iy in range(segs_y + 1):
        row = []
        fy = iy / segs_y  # 0..1
        y = -hd + depth * fy
        # Нормализованное расстояние от центра по Y (0=центр, 1=край)
        dy = abs(fy - 0.5) * 2

        for ix in range(segs_x + 1):
            fx = ix / segs_x
            x = -hw + width * fx
            dx = abs(fx - 0.5) * 2

            # Расстояние от центра (макс = 1 в углах)
            dist = min(1.0, max(dx, dy))
            # Параболический профиль: 1 в центре, 0 на краях
            profile = 1.0 - dist * dist

            z_top = ht + ht * profile
            z_bot = ht - ht * profile

            if rng:
                noise = thickness * 0.06
                z_top += rng.uniform(-noise, noise)
                z_bot += rng.uniform(-noise, noise)

            row.append((
                bm.verts.new((x, y, z_top)),
                bm.verts.new((x, y, z_bot)),
            ))
        verts_grid.append(row)

    # Верхние грани
    for iy in range(segs_y):
        for ix in range(segs_x):
            bm.faces.new([
                verts_grid[iy][ix][0],
                verts_grid[iy][ix + 1][0],
                verts_grid[iy + 1][ix + 1][0],
                verts_grid[iy + 1][ix][0],
            ])
    # Нижние грани
    for iy in range(segs_y):
        for ix in range(segs_x):
            bm.faces.new([
                verts_grid[iy][ix][1],
                verts_grid[iy + 1][ix][1],
                verts_grid[iy + 1][ix + 1][1],
                verts_grid[iy][ix + 1][1],
            ])
    # Боковые грани (замыкаем верх и низ по периметру)
    for ix in range(segs_x):
        # Передний край (iy=0)
        bm.faces.new([
            verts_grid[0][ix][0], verts_grid[0][ix][1],
            verts_grid[0][ix + 1][1], verts_grid[0][ix + 1][0],
        ])
        # Задний край (iy=segs_y)
        bm.faces.new([
            verts_grid[segs_y][ix][0], verts_grid[segs_y][ix + 1][0],
            verts_grid[segs_y][ix + 1][1], verts_grid[segs_y][ix][1],
        ])
    for iy in range(segs_y):
        # Левый край (ix=0)
        bm.faces.new([
            verts_grid[iy][0][0], verts_grid[iy + 1][0][0],
            verts_grid[iy + 1][0][1], verts_grid[iy][0][1],
        ])
        # Правый край (ix=segs_x)
        bm.faces.new([
            verts_grid[iy][segs_x][0], verts_grid[iy][segs_x][1],
            verts_grid[iy + 1][segs_x][1], verts_grid[iy + 1][segs_x][0],
        ])

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

FABRIC_COLORS = [
    ("Cream", (0.9, 0.85, 0.75, 1.0)),
    ("White", (0.93, 0.93, 0.91, 1.0)),
    ("DarkBlue", (0.12, 0.18, 0.32, 1.0)),
    ("Burgundy", (0.45, 0.1, 0.1, 1.0)),
    ("Olive", (0.3, 0.35, 0.2, 1.0)),
    ("Gray", (0.5, 0.5, 0.5, 1.0)),
    ("Mustard", (0.7, 0.55, 0.15, 1.0)),
    ("Teal", (0.15, 0.4, 0.4, 1.0)),
    ("Blush", (0.8, 0.6, 0.6, 1.0)),
    ("Charcoal", (0.2, 0.2, 0.2, 1.0)),
    ("Terracotta", (0.65, 0.35, 0.2, 1.0)),
    ("Sage", (0.55, 0.6, 0.45, 1.0)),
]


def mat_fabric(rng):
    name, color = rng.choice(FABRIC_COLORS)
    mat = get_or_create_mat(f"M_Cushion_{name}")
    tree = mat.node_tree

    for n in list(tree.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            tree.nodes.remove(n)
    output = [n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    output.location = (600, 0)

    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (300, 0)
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = 0.85
    bsdf.inputs['Specular IOR Level'].default_value = 0.05
    bsdf.inputs['Sheen Weight'].default_value = 0.5
    bsdf.inputs['Sheen Roughness'].default_value = 0.4

    # Noise bump для текстуры ткани
    noise = tree.nodes.new('ShaderNodeTexNoise')
    noise.location = (-100, -200)
    noise.inputs['Scale'].default_value = 60.0
    noise.inputs['Detail'].default_value = 6.0

    bump = tree.nodes.new('ShaderNodeBump')
    bump.location = (100, -200)
    bump.inputs['Strength'].default_value = 0.04
    bump.inputs['Distance'].default_value = 0.002

    tc = tree.nodes.new('ShaderNodeTexCoord')
    tc.location = (-300, -200)

    tree.links.new(tc.outputs['Object'], noise.inputs['Vector'])
    tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    tree.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

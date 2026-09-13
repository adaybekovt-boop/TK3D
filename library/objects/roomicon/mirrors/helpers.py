"""Утилиты для генерации зеркал."""

import bpy
import bmesh
import math

from common.shared_geometry import create_box
from common.shared_materials import get_or_create_mat, setup_principled


def create_rect_plane(name, hw, hh):
    """Прямоугольная плоскость в XZ, лицевая +Y. Origin — центр."""
    bm = bmesh.new()
    v0 = bm.verts.new((-hw, 0, -hh))
    v1 = bm.verts.new((hw, 0, -hh))
    v2 = bm.verts.new((hw, 0, hh))
    v3 = bm.verts.new((-hw, 0, hh))
    bm.faces.new([v0, v1, v2, v3])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return bpy.data.objects.new(name, mesh)


def create_circle_plane(name, radius, segments=48):
    """Круглая плоскость в XZ, лицевая +Y."""
    bm = bmesh.new()
    center = bm.verts.new((0, 0, 0))
    ring = []
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        ring.append(bm.verts.new((radius * math.cos(angle), 0, radius * math.sin(angle))))
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new([center, ring[i], ring[j]])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return bpy.data.objects.new(name, mesh)


def create_oval_plane(name, rx, rz, segments=48):
    """Овальная плоскость в XZ, лицевая +Y."""
    bm = bmesh.new()
    center = bm.verts.new((0, 0, 0))
    ring = []
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        ring.append(bm.verts.new((rx * math.cos(angle), 0, rz * math.sin(angle))))
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new([center, ring[i], ring[j]])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return bpy.data.objects.new(name, mesh)


def create_arch_plane(name, hw, hh, arch_r=None, segments=24):
    """Прямоугольник с арочным верхом в XZ, лицевая +Y."""
    if arch_r is None:
        arch_r = hw  # полукруглая арка

    bm = bmesh.new()
    center = bm.verts.new((0, 0, 0))

    # Нижняя часть — прямоугольник до начала арки
    rect_top_z = hh - arch_r
    verts_outline = []

    # Низ-лево → низ-право
    verts_outline.append(bm.verts.new((-hw, 0, -hh)))
    verts_outline.append(bm.verts.new((hw, 0, -hh)))

    # Право вверх до начала арки
    verts_outline.append(bm.verts.new((hw, 0, rect_top_z)))

    # Арка (от правого края к левому)
    for i in range(1, segments):
        angle = math.pi * i / segments  # от 0 до pi
        x = arch_r * math.cos(angle)  # от +hw к -hw
        z = rect_top_z + arch_r * math.sin(angle)
        verts_outline.append(bm.verts.new((x, 0, z)))

    # Лево вниз
    verts_outline.append(bm.verts.new((-hw, 0, rect_top_z)))

    # Грани — fan от центра
    for i in range(len(verts_outline)):
        j = (i + 1) % len(verts_outline)
        bm.faces.new([center, verts_outline[i], verts_outline[j]])

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return bpy.data.objects.new(name, mesh)


def create_circle_frame(name, radius, frame_w, frame_d, segments=48):
    """Круглая рамка (кольцо) в XZ."""
    bm = bmesh.new()
    inner_r = radius
    outer_r = radius + frame_w
    hd = frame_d / 2

    for i in range(segments):
        angle = 2 * math.pi * i / segments
        next_angle = 2 * math.pi * ((i + 1) % segments) / segments

        # 4 вершины секции: inner/outer × front/back
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        cos_n, sin_n = math.cos(next_angle), math.sin(next_angle)

        v_if = bm.verts.new((inner_r * cos_a, hd, inner_r * sin_a))
        v_ib = bm.verts.new((inner_r * cos_a, -hd, inner_r * sin_a))
        v_of = bm.verts.new((outer_r * cos_a, hd, outer_r * sin_a))
        v_ob = bm.verts.new((outer_r * cos_a, -hd, outer_r * sin_a))

        v_if2 = bm.verts.new((inner_r * cos_n, hd, inner_r * sin_n))
        v_ib2 = bm.verts.new((inner_r * cos_n, -hd, inner_r * sin_n))
        v_of2 = bm.verts.new((outer_r * cos_n, hd, outer_r * sin_n))
        v_ob2 = bm.verts.new((outer_r * cos_n, -hd, outer_r * sin_n))

        # Front
        bm.faces.new([v_if, v_of, v_of2, v_if2])
        # Back
        bm.faces.new([v_ib, v_ib2, v_ob2, v_ob])
        # Outer
        bm.faces.new([v_of, v_ob, v_ob2, v_of2])
        # Inner
        bm.faces.new([v_if, v_if2, v_ib2, v_ib])

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return bpy.data.objects.new(name, mesh)


# ============================================================
# Материалы
# ============================================================


def mat_mirror():
    """Зеркальная поверхность."""
    mat = get_or_create_mat("M_Mirror")
    return setup_principled(mat, (0.95, 0.95, 0.95, 1.0),
                              roughness=0.02, metallic=1.0, specular=1.0)


FRAME_STYLES = [
    ("DarkWood", (0.2, 0.12, 0.06, 1.0), 0.45, 0.0),
    ("LightWood", (0.55, 0.4, 0.22, 1.0), 0.5, 0.0),
    ("WhitePaint", (0.92, 0.91, 0.88, 1.0), 0.35, 0.0),
    ("BlackPaint", (0.08, 0.08, 0.08, 1.0), 0.3, 0.0),
    ("Gold", (0.7, 0.55, 0.2, 1.0), 0.25, 0.8),
    ("Chrome", (0.7, 0.7, 0.72, 1.0), 0.15, 1.0),
    ("BlackMetal", (0.05, 0.05, 0.05, 1.0), 0.35, 1.0),
]


def mat_frame(rng):
    name, color, roughness, metallic = rng.choice(FRAME_STYLES)
    mat = get_or_create_mat(f"M_MirrorFrame_{name}")
    return setup_principled(mat, color, roughness=roughness, metallic=metallic,
                              specular=0.5 if metallic > 0 else 0.3)

"""Утилиты для генерации ковров."""

import bpy
import bmesh
import math

from common.shared_geometry import create_box
from common.shared_materials import get_or_create_mat


def _get_or_create_mat(name):
    """Backward-compatible wrapper around common get_or_create_mat."""
    return get_or_create_mat(name)


def create_rect_rug(name, width, depth):
    """Прямоугольный ковёр в плоскости XY (лежит на полу, Z=0), с UV."""
    bm = bmesh.new()

    hw, hd = width / 2, depth / 2
    v0 = bm.verts.new((-hw, -hd, 0))
    v1 = bm.verts.new((hw, -hd, 0))
    v2 = bm.verts.new((hw, hd, 0))
    v3 = bm.verts.new((-hw, hd, 0))
    face = bm.faces.new([v0, v1, v2, v3])

    # UV
    uv_layer = bm.loops.layers.uv.new("UVMap")
    for loop in face.loops:
        uv = loop[uv_layer]
        co = loop.vert.co
        uv.uv = ((co.x + hw) / width, (co.y + hd) / depth)

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return bpy.data.objects.new(name, mesh)


def create_circle_rug(name, radius, segments=48):
    """Круглый ковёр в плоскости XY (Z=0), с UV."""
    bm = bmesh.new()

    center = bm.verts.new((0, 0, 0))
    ring = []
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        ring.append(bm.verts.new((x, y, 0)))

    uv_layer = bm.loops.layers.uv.new("UVMap")

    for i in range(segments):
        j = (i + 1) % segments
        face = bm.faces.new([center, ring[i], ring[j]])
        # UV: маппим на круг [0,1]×[0,1]
        for loop in face.loops:
            co = loop.vert.co
            uv = loop[uv_layer]
            uv.uv = (co.x / (radius * 2) + 0.5, co.y / (radius * 2) + 0.5)

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return bpy.data.objects.new(name, mesh)


def create_oval_rug(name, rx, ry, segments=48):
    """Овальный ковёр в плоскости XY (Z=0), с UV."""
    bm = bmesh.new()

    center = bm.verts.new((0, 0, 0))
    ring = []
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = rx * math.cos(angle)
        y = ry * math.sin(angle)
        ring.append(bm.verts.new((x, y, 0)))

    uv_layer = bm.loops.layers.uv.new("UVMap")

    for i in range(segments):
        j = (i + 1) % segments
        face = bm.faces.new([center, ring[i], ring[j]])
        for loop in face.loops:
            co = loop.vert.co
            uv = loop[uv_layer]
            uv.uv = (co.x / (rx * 2) + 0.5, co.y / (ry * 2) + 0.5)

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return bpy.data.objects.new(name, mesh)


# ============================================================
# Цвета ковров
# ============================================================

RUG_COLORS = [
    (0.5, 0.15, 0.12, 1.0),   # бордовый
    (0.12, 0.2, 0.35, 1.0),   # тёмно-синий
    (0.15, 0.3, 0.15, 1.0),   # тёмно-зелёный
    (0.6, 0.5, 0.35, 1.0),    # бежевый
    (0.35, 0.2, 0.1, 1.0),    # коричневый
    (0.55, 0.25, 0.15, 1.0),  # терракота
    (0.4, 0.35, 0.45, 1.0),   # серо-фиолетовый
    (0.7, 0.65, 0.5, 1.0),    # песочный
]

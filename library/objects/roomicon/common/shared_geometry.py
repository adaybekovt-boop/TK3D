"""Shared geometry primitives for generators."""

import bpy
import bmesh
import math


def create_box(name, sx, sy, sz, cx=0, cy=0, cz=0):
    """Create a box mesh object. sx/sy/sz are half-extents."""
    bm = bmesh.new()
    verts = []
    for dx in (-sx, sx):
        for dy in (-sy, sy):
            for dz in (-sz, sz):
                verts.append(bm.verts.new((cx + dx, cy + dy, cz + dz)))
    faces = [
        (0, 1, 3, 2), (4, 6, 7, 5),
        (0, 4, 5, 1), (2, 3, 7, 6),
        (0, 2, 6, 4), (1, 5, 7, 3),
    ]
    for f in faces:
        bm.faces.new([verts[i] for i in f])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return bpy.data.objects.new(name, mesh)


def create_cylinder(name, radius, height, z_offset=0, segments=24, smooth=True):
    """Create a cylinder mesh object."""
    bm = bmesh.new()
    bottom, top = [], []
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
    if smooth:
        for p in mesh.polygons:
            p.use_smooth = True
    mesh.update()
    return bpy.data.objects.new(name, mesh)

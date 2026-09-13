"""Helpers for plush toy generation."""

import bpy
import bmesh
import math


def create_sphere(name, radius, cx=0, cy=0, cz=0, segments=16, rings=12):
    """UV sphere mesh object."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius)
    for v in bm.verts:
        v.co.x += cx
        v.co.y += cy
        v.co.z += cz
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.update()
    return bpy.data.objects.new(name, mesh)


def create_ellipsoid(name, rx, ry, rz, cx=0, cy=0, cz=0, segments=16, rings=12):
    """Ellipsoid = stretched sphere."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=1.0)
    for v in bm.verts:
        v.co.x = v.co.x * rx + cx
        v.co.y = v.co.y * ry + cy
        v.co.z = v.co.z * rz + cz
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.update()
    return bpy.data.objects.new(name, mesh)


def create_droopy_ear(name, rx, ry, rz, cx=0, cy=0, cz=0,
                      droop_amount=0.5, droop_start=0.3, segments=12, rings=10):
    """Ellipsoid ear with upper part drooping forward (-Y).
    droop_start: fraction of height (0..1) where drooping begins.
    droop_amount: how far the tip droops (multiplier of rz).
    """
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=1.0)
    # Scale to ellipsoid, then droop upper vertices
    for v in bm.verts:
        lz = v.co.z  # -1..1 in unit sphere
        v.co.x = v.co.x * rx
        v.co.y = v.co.y * ry
        v.co.z = v.co.z * rz
        # Droop: vertices above droop_start get bent forward and down
        if lz > droop_start:
            t = (lz - droop_start) / (1.0 - droop_start)  # 0..1
            v.co.y -= t * t * droop_amount * rz  # forward droop
            v.co.z -= t * t * droop_amount * rz * 0.8  # sag down
        v.co.z += rz
        v.co.x += cx
        v.co.y += cy
        v.co.z += cz
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.update()
    return bpy.data.objects.new(name, mesh)


def create_cone(name, radius, height, cx=0, cy=0, cz=0, segments=12):
    """Simple cone."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True,
                          segments=segments, radius1=radius, radius2=0, depth=height)
    for v in bm.verts:
        v.co.x += cx
        v.co.y += cy
        v.co.z += cz + height / 2
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    mesh.update()
    return bpy.data.objects.new(name, mesh)


def add_subdivision(obj, levels=2):
    """Add Subdivision Surface modifier."""
    mod = obj.modifiers.new("Subsurf", 'SUBSURF')
    mod.levels = levels
    mod.render_levels = levels


def mat_plush(name, color, roughness=0.9):
    """Fabric-like material for plush toys."""
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
    bsdf.location = (300, 0)
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Specular IOR Level'].default_value = 0.1
    # Slight fuzz via sheen
    bsdf.inputs['Sheen Weight'].default_value = 0.3
    bsdf.inputs['Sheen Roughness'].default_value = 0.8

    # Noise bump for fabric texture
    tc = tree.nodes.new('ShaderNodeTexCoord')
    tc.location = (-200, -200)
    noise = tree.nodes.new('ShaderNodeTexNoise')
    noise.location = (0, -200)
    noise.inputs['Scale'].default_value = 80.0
    noise.inputs['Detail'].default_value = 4.0
    bump = tree.nodes.new('ShaderNodeBump')
    bump.location = (150, -200)
    bump.inputs['Strength'].default_value = 0.03

    tree.links.new(tc.outputs['Object'], noise.inputs['Vector'])
    tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    tree.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    return mat


def mat_eye(name='M_PlushEye'):
    """Glossy dark eye material."""
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    for n in list(tree.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            tree.nodes.remove(n)
    output = [n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.02, 0.02, 0.02, 1)
    bsdf.inputs['Roughness'].default_value = 0.15
    bsdf.inputs['Specular IOR Level'].default_value = 0.8
    tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat


# Color palettes for plush toys
PLUSH_COLORS = {
    'dark_brown':  (0.18, 0.10, 0.05, 1),
    'chocolate':   (0.25, 0.14, 0.07, 1),
    'brown':       (0.35, 0.22, 0.12, 1),
    'light_brown': (0.55, 0.40, 0.25, 1),
    'cream':       (0.85, 0.78, 0.65, 1),
    'white':       (0.92, 0.90, 0.88, 1),
    'grey':        (0.55, 0.55, 0.55, 1),
    'pink':        (0.85, 0.55, 0.60, 1),
    'yellow':      (0.90, 0.80, 0.30, 1),
    'blue':        (0.40, 0.55, 0.75, 1),
    'orange':      (0.85, 0.55, 0.20, 1),
}

BELLY_COLORS = {
    'dark_brown':  (0.35, 0.25, 0.16, 1),
    'chocolate':   (0.42, 0.30, 0.18, 1),
    'brown':       (0.55, 0.42, 0.30, 1),
    'light_brown': (0.75, 0.65, 0.50, 1),
    'cream':       (0.92, 0.88, 0.78, 1),
    'white':       (0.95, 0.94, 0.93, 1),
    'grey':        (0.75, 0.75, 0.75, 1),
    'pink':        (0.92, 0.78, 0.80, 1),
    'yellow':      (0.95, 0.92, 0.65, 1),
    'blue':        (0.65, 0.75, 0.85, 1),
    'orange':      (0.95, 0.78, 0.50, 1),
}

# Подмножества цветов по типу игрушки
BEAR_COLORS = ['dark_brown', 'chocolate', 'brown', 'light_brown', 'cream', 'white', 'grey']

"""Утилиты для генерации фоторамок."""

import bpy
import bmesh
import math
import os
import sys

_generators_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if _generators_dir not in sys.path:
    sys.path.insert(0, _generators_dir)

from common.shared_geometry import create_box
from common.shared_materials import get_or_create_mat, clear_and_get_output, setup_principled


IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}


def list_images(pool_dir):
    if not os.path.isdir(pool_dir):
        return []
    result = []
    for f in os.listdir(pool_dir):
        ext = os.path.splitext(f)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            result.append(os.path.join(pool_dir, f))
    return sorted(result)


def get_image_aspect(image_path):
    img = bpy.data.images.load(image_path, check_existing=True)
    w, h = img.size
    if h == 0:
        return w, h, 1.0
    return w, h, w / h


# ============================================================
# Геометрия
# ============================================================

def create_canvas(name, width, height):
    """Плоскость с UV в плоскости XZ, лицом в +Y."""
    bm = bmesh.new()
    hw, hh = width / 2, height / 2
    v0 = bm.verts.new((-hw, 0, -hh))
    v1 = bm.verts.new((hw, 0, -hh))
    v2 = bm.verts.new((hw, 0, hh))
    v3 = bm.verts.new((-hw, 0, hh))
    face = bm.faces.new([v0, v1, v2, v3])

    uv_layer = bm.loops.layers.uv.new("UVMap")
    for loop in face.loops:
        uv = loop[uv_layer]
        co = loop.vert.co
        uv.uv = ((co.x + hw) / width, (co.z + hh) / height)

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return bpy.data.objects.new(name, mesh)


# ============================================================
# Рамки
# ============================================================

def frame_simple(name, canvas_w, canvas_h, rng, frame_w=None):
    """Простая прямоугольная рамка из 4 боксов."""
    if frame_w is None:
        frame_w = rng.uniform(0.008, 0.015)
    frame_d = rng.uniform(0.005, 0.01)

    hw, hh = canvas_w / 2, canvas_h / 2
    hfw = frame_w / 2
    hfd = frame_d / 2

    objects = []
    objects.append(create_box(f"{name}_Top", hw + frame_w, hfd, hfw,
                              cy=hfd, cz=hh + hfw))
    objects.append(create_box(f"{name}_Bottom", hw + frame_w, hfd, hfw,
                              cy=hfd, cz=-hh - hfw))
    objects.append(create_box(f"{name}_Left", hfw, hfd, hh,
                              cx=-hw - hfw, cy=hfd))
    objects.append(create_box(f"{name}_Right", hfw, hfd, hh,
                              cx=hw + hfw, cy=hfd))
    return objects


def frame_bevel(name, canvas_w, canvas_h, rng, frame_w=None):
    """Багетная рамка с Bevel."""
    if frame_w is None:
        frame_w = rng.uniform(0.01, 0.02)
    frame_d = rng.uniform(0.008, 0.015)
    bevel_width = rng.uniform(0.003, 0.006)

    hw, hh = canvas_w / 2, canvas_h / 2
    hfw = frame_w / 2
    hfd = frame_d / 2

    parts = [
        (f"{name}_Top", hw + frame_w, hfd, hfw, 0, hfd, hh + hfw),
        (f"{name}_Bottom", hw + frame_w, hfd, hfw, 0, hfd, -hh - hfw),
        (f"{name}_Left", hfw, hfd, hh + frame_w, -hw - hfw, hfd, 0),
        (f"{name}_Right", hfw, hfd, hh + frame_w, hw + hfw, hfd, 0),
    ]
    objects = []
    for pname, sx, sy, sz, cx, cy, cz in parts:
        obj = create_box(pname, sx, sy, sz, cx, cy, cz)
        mod = obj.modifiers.new("Bevel", 'BEVEL')
        mod.width = bevel_width
        mod.segments = 2
        mod.limit_method = 'ANGLE'
        mod.angle_limit = math.radians(60)
        objects.append(obj)
    return objects


# ============================================================
# Подставка
# ============================================================

def create_stand(name, top_y, top_z, rng):
    """Ножка-подставка: от точки крепления (top_y, top_z) вниз до пола (Z=0).

    Строится в мировых координатах, без вращения.
    """
    bm = bmesh.new()
    t = 0.002  # толщина
    stand_w = rng.uniform(0.01, 0.018)
    hw = stand_w / 2

    # Низ подставки на полу, чуть дальше назад для устойчивости
    bot_y = top_y * 1.4

    # Передняя грань (ближе к рамке)
    v0 = bm.verts.new((-hw, top_y, top_z))
    v1 = bm.verts.new((hw, top_y, top_z))
    v2 = bm.verts.new((hw, bot_y, 0))
    v3 = bm.verts.new((-hw, bot_y, 0))
    bm.faces.new([v0, v1, v2, v3])

    # Задняя грань (толщина)
    v4 = bm.verts.new((-hw, top_y - t, top_z))
    v5 = bm.verts.new((hw, top_y - t, top_z))
    v6 = bm.verts.new((hw, bot_y - t, 0))
    v7 = bm.verts.new((-hw, bot_y - t, 0))
    bm.faces.new([v7, v6, v5, v4])

    # Боковые грани
    bm.faces.new([v0, v3, v7, v4])
    bm.faces.new([v1, v5, v6, v2])
    bm.faces.new([v0, v4, v5, v1])
    bm.faces.new([v3, v2, v6, v7])

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return bpy.data.objects.new(name, mesh)


# ============================================================
# Материалы
# ============================================================

FRAME_STYLES = [
    ("DarkWood", (0.2, 0.12, 0.06, 1.0), 0.45, 0.0),
    ("LightWood", (0.55, 0.4, 0.22, 1.0), 0.5, 0.0),
    ("WhitePaint", (0.92, 0.91, 0.88, 1.0), 0.4, 0.0),
    ("BlackPaint", (0.08, 0.08, 0.08, 1.0), 0.3, 0.0),
    ("Silver", (0.7, 0.7, 0.72, 1.0), 0.2, 0.8),
    ("Gold", (0.7, 0.55, 0.2, 1.0), 0.25, 0.8),
    ("Walnut", (0.3, 0.18, 0.08, 1.0), 0.5, 0.0),
]


def mat_frame(rng):
    name, color, roughness, metallic = rng.choice(FRAME_STYLES)
    mat = get_or_create_mat(f"M_PhotoFrame_{name}")
    return setup_principled(mat, color, roughness=roughness, metallic=metallic, specular=0.4)


def mat_canvas(image_path):
    """Материал с Image Texture."""
    img = bpy.data.images.load(image_path, check_existing=True)
    mat_name = f"M_Photo_{os.path.basename(image_path)}"
    mat = get_or_create_mat(mat_name)
    tree = mat.node_tree
    output = clear_and_get_output(tree)
    output.location = (600, 0)

    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (300, 0)
    bsdf.inputs['Roughness'].default_value = 0.3
    bsdf.inputs['Specular IOR Level'].default_value = 0.2

    tex = tree.nodes.new('ShaderNodeTexImage')
    tex.location = (0, 0)
    tex.image = img

    tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat


def mat_backing():
    mat = get_or_create_mat("M_PhotoBacking")
    return setup_principled(mat, (0.25, 0.2, 0.15, 1.0), roughness=0.9, specular=0.02)

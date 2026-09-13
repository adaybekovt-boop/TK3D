"""Генерация картин из изображений + рамки."""

import bpy
import bmesh
import os
import math
import random

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}


def list_images(pool_dir):
    """Возвращает список путей к изображениям в пуле."""
    if not os.path.isdir(pool_dir):
        return []
    result = []
    for f in os.listdir(pool_dir):
        ext = os.path.splitext(f)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            result.append(os.path.join(pool_dir, f))
    return sorted(result)


def get_image_aspect(image_path):
    """Загружает изображение в Blender и возвращает (width, height, aspect_ratio)."""
    img = bpy.data.images.load(image_path, check_existing=True)
    w, h = img.size
    if h == 0:
        return w, h, 1.0
    return w, h, w / h


# ============================================================
# Геометрия
# ============================================================

def _create_canvas(name, width, height):
    """Плоскость с UV для текстуры. Лицевая сторона +Y. Origin — центр задней стороны."""
    bm = bmesh.new()

    hw, hh = width / 2, height / 2
    # 4 вершины в плоскости XZ, Y=0
    v0 = bm.verts.new((-hw, 0, -hh))
    v1 = bm.verts.new((hw, 0, -hh))
    v2 = bm.verts.new((hw, 0, hh))
    v3 = bm.verts.new((-hw, 0, hh))
    face = bm.faces.new([v0, v1, v2, v3])

    # UV
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


def _create_box(name, sx, sy, sz, cx=0, cy=0, cz=0):
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


# ============================================================
# Рамки
# ============================================================

def _frame_simple(name, canvas_w, canvas_h, rng):
    """Прямоугольная рамка из 4 боксов."""
    frame_w = rng.uniform(0.02, 0.04)
    frame_d = rng.uniform(0.015, 0.025)

    hw, hh = canvas_w / 2, canvas_h / 2
    hfw = frame_w / 2
    hfd = frame_d / 2

    objects = []

    # Верх
    objects.append(_create_box(f"{name}_Top",
                                hw + frame_w, hfd, hfw,
                                cy=hfd, cz=hh + hfw))
    # Низ
    objects.append(_create_box(f"{name}_Bottom",
                                hw + frame_w, hfd, hfw,
                                cy=hfd, cz=-hh - hfw))
    # Лево
    objects.append(_create_box(f"{name}_Left",
                                hfw, hfd, hh,
                                cx=-hw - hfw, cy=hfd))
    # Право
    objects.append(_create_box(f"{name}_Right",
                                hfw, hfd, hh,
                                cx=hw + hfw, cy=hfd))
    return objects


def _frame_bevel(name, canvas_w, canvas_h, rng):
    """Багетная рамка: прямоугольное сечение + Bevel modifier."""
    frame_w = rng.uniform(0.03, 0.06)
    frame_d = rng.uniform(0.02, 0.035)
    bevel_width = rng.uniform(0.008, 0.015)

    hw, hh = canvas_w / 2, canvas_h / 2
    hfw = frame_w / 2
    hfd = frame_d / 2

    objects = []

    parts = [
        (f"{name}_Top", hw + frame_w, hfd, hfw, 0, hfd, hh + hfw),
        (f"{name}_Bottom", hw + frame_w, hfd, hfw, 0, hfd, -hh - hfw),
        (f"{name}_Left", hfw, hfd, hh + frame_w, -hw - hfw, hfd, 0),
        (f"{name}_Right", hfw, hfd, hh + frame_w, hw + hfw, hfd, 0),
    ]

    for pname, sx, sy, sz, cx, cy, cz in parts:
        obj = _create_box(pname, sx, sy, sz, cx, cy, cz)
        # Bevel для фигурного профиля
        mod = obj.modifiers.new("Bevel", 'BEVEL')
        mod.width = bevel_width
        mod.segments = 3
        mod.limit_method = 'ANGLE'
        mod.angle_limit = math.radians(60)
        objects.append(obj)

    return objects


# ============================================================
# Материалы
# ============================================================

def _get_or_create_mat(name):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    return mat


def create_canvas_material(image_path):
    """Материал холста с Image Texture."""
    img = bpy.data.images.load(image_path, check_existing=True)
    mat_name = f"M_Canvas_{os.path.basename(image_path)}"
    mat = _get_or_create_mat(mat_name)
    tree = mat.node_tree

    for n in list(tree.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            tree.nodes.remove(n)
    output = [n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    output.location = (600, 0)

    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (300, 0)
    bsdf.inputs['Roughness'].default_value = 0.7
    bsdf.inputs['Specular IOR Level'].default_value = 0.1

    tex = tree.nodes.new('ShaderNodeTexImage')
    tex.location = (0, 0)
    tex.image = img

    tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat


def create_procedural_canvas_material(rng):
    """Процедурная 'абстрактная картина' — используется когда нет изображений."""
    style = rng.choice(['gradient', 'blocks', 'noise'])

    # Палитра мягких тонов
    palettes = [
        [(0.85, 0.75, 0.65, 1), (0.45, 0.35, 0.55, 1)],  # бежево-фиолетовый
        [(0.3, 0.5, 0.6, 1), (0.8, 0.7, 0.5, 1)],        # сине-золотой
        [(0.7, 0.3, 0.25, 1), (0.9, 0.85, 0.7, 1)],       # терракот-кремовый
        [(0.25, 0.35, 0.3, 1), (0.75, 0.8, 0.7, 1)],      # тёмно-зелёный / светлый
        [(0.2, 0.25, 0.4, 1), (0.85, 0.6, 0.4, 1)],       # индиго-оранж
    ]
    colors = rng.choice(palettes)

    mat_name = f"M_AbstractCanvas_{rng.randint(0, 99999)}"
    mat = _get_or_create_mat(mat_name)
    tree = mat.node_tree
    for n in list(tree.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            tree.nodes.remove(n)
    output = [n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    output.location = (800, 0)

    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (500, 0)
    bsdf.inputs['Roughness'].default_value = 0.8
    bsdf.inputs['Specular IOR Level'].default_value = 0.05

    tc = tree.nodes.new('ShaderNodeTexCoord')
    tc.location = (-400, 0)

    if style == 'gradient':
        sep = tree.nodes.new('ShaderNodeSeparateXYZ')
        sep.location = (-200, 0)
        tree.links.new(tc.outputs['UV'], sep.inputs['Vector'])

        ramp = tree.nodes.new('ShaderNodeValToRGB')
        ramp.location = (100, 0)
        ramp.color_ramp.elements[0].color = colors[0]
        ramp.color_ramp.elements[0].position = 0.2
        ramp.color_ramp.elements[1].color = colors[1]
        ramp.color_ramp.elements[1].position = 0.8

        axis = rng.choice(['X', 'Y'])
        tree.links.new(sep.outputs[axis], ramp.inputs['Fac'])
        tree.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])

    elif style == 'blocks':
        sep = tree.nodes.new('ShaderNodeSeparateXYZ')
        sep.location = (-200, 0)
        tree.links.new(tc.outputs['UV'], sep.inputs['Vector'])

        ramp = tree.nodes.new('ShaderNodeValToRGB')
        ramp.location = (100, 0)
        ramp.color_ramp.interpolation = 'CONSTANT'
        ramp.color_ramp.elements[0].color = colors[0]
        ramp.color_ramp.elements[0].position = 0.0
        el = ramp.color_ramp.elements.new(0.4)
        el.color = colors[1]
        el2 = ramp.color_ramp.elements.new(0.7)
        c2 = tuple((colors[0][i] + colors[1][i]) / 2 for i in range(3)) + (1,)
        el2.color = c2
        ramp.color_ramp.elements[1].position = 1.0

        tree.links.new(sep.outputs['Y'], ramp.inputs['Fac'])
        tree.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])

    else:  # noise
        noise = tree.nodes.new('ShaderNodeTexNoise')
        noise.location = (-100, 0)
        noise.inputs['Scale'].default_value = rng.uniform(2.0, 6.0)
        noise.inputs['Detail'].default_value = rng.uniform(3.0, 8.0)
        tree.links.new(tc.outputs['UV'], noise.inputs['Vector'])

        ramp = tree.nodes.new('ShaderNodeValToRGB')
        ramp.location = (200, 0)
        ramp.color_ramp.elements[0].color = colors[0]
        ramp.color_ramp.elements[1].color = colors[1]
        tree.links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
        tree.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])

    tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat


FRAME_STYLES = [
    ("DarkWood", (0.2, 0.12, 0.06, 1.0), 0.45, 0.0),
    ("LightWood", (0.55, 0.4, 0.22, 1.0), 0.5, 0.0),
    ("WhitePaint", (0.92, 0.91, 0.88, 1.0), 0.4, 0.0),
    ("BlackPaint", (0.08, 0.08, 0.08, 1.0), 0.3, 0.0),
    ("Gold", (0.7, 0.55, 0.2, 1.0), 0.25, 0.8),
]


def create_frame_material(rng):
    """Случайный материал рамки."""
    name, color, roughness, metallic = rng.choice(FRAME_STYLES)
    mat = _get_or_create_mat(f"M_Frame_{name}")
    tree = mat.node_tree
    for n in list(tree.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            tree.nodes.remove(n)
    output = [n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    output.location = (500, 0)
    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (200, 0)
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Specular IOR Level'].default_value = 0.4
    tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat


# ============================================================
# API
# ============================================================

PAINTING_TYPES = {
    'none': {},
    'simple': {},
    'bevel': {},
}


def generate_painting(seed, image_path=None, frame_type='simple', max_width=None):
    """
    Генерирует картину. Если image_path=None — процедурная абстракция.
    Возвращает список объектов.
    """
    rng = random.Random(seed)

    if max_width is None:
        max_width = rng.uniform(0.3, 0.8)

    # Определяем размеры
    if image_path and os.path.isfile(image_path):
        img_w, img_h, aspect = get_image_aspect(image_path)
    else:
        aspect = rng.choice([1.0, 1.33, 1.5, 0.75, 0.67])
        image_path = None

    canvas_w = max_width
    canvas_h = canvas_w / aspect if aspect > 0 else canvas_w

    # Ограничиваем высоту
    if canvas_h > 1.0:
        canvas_h = 1.0
        canvas_w = canvas_h * aspect

    objects = []

    # Холст
    canvas = _create_canvas("Canvas", canvas_w, canvas_h)
    if image_path:
        canvas_mat = create_canvas_material(image_path)
    else:
        canvas_mat = create_procedural_canvas_material(rng)
    canvas.data.materials.append(canvas_mat)
    objects.append(canvas)

    # Задник (тонкая панель за холстом)
    back = _create_box("PaintingBack",
                        canvas_w / 2 + 0.005, 0.004, canvas_h / 2 + 0.005,
                        cy=-0.004)
    back_mat = _get_or_create_mat("M_PaintingBack")
    tree = back_mat.node_tree
    for n in list(tree.nodes):
        if n.type != 'OUTPUT_MATERIAL':
            tree.nodes.remove(n)
    out = [n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.3, 0.3, 0.3, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.8
    tree.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    back.data.materials.append(back_mat)
    objects.append(back)

    # Рамка
    if frame_type == 'simple':
        frame_objs = _frame_simple("Frame", canvas_w, canvas_h, rng)
    elif frame_type == 'bevel':
        frame_objs = _frame_bevel("Frame", canvas_w, canvas_h, rng)
    else:
        frame_objs = []

    if frame_objs:
        frame_mat = create_frame_material(rng)
        for obj in frame_objs:
            obj.data.materials.append(frame_mat)
        objects.extend(frame_objs)

    return objects

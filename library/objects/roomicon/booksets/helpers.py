"""Утилиты для генерации книг."""

import bpy
import bmesh
import os
import sys

# Ensure common is importable
_generators_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if _generators_dir not in sys.path:
    sys.path.insert(0, _generators_dir)

from common.shared_geometry import create_box
from common.shared_materials import get_or_create_mat, setup_principled


def create_page_block(name, thickness, width, height, rng, segments=25,back_shift=0):
    """Цельный блок страниц с волнистыми торцами.

    Стоячая книга: толщина по X, ширина по Y, высота по Z.
    Корешок на -Y (плоский), видимые торцы: +Y (перед), +Z (верх), -Z (низ).
    Торцы переходят друг в друга на углах.

    Блок центрирован по origin.

    Args:
        thickness: толщина блока (X)
        width: ширина блока (Y)
        height: высота блока (Z)
        rng: Random
        segments: количество сегментов вдоль X для волн
    """
    bm = bmesh.new()

    ht = thickness / 2
    hw = width / 2
    hh = height / 2
    amp = thickness * 0.02  # амплитуда волн

    # Для каждого сечения по X генерируем волны на 3 видимых рёбрах
    n = segments + 1  # количество точек
    xs = [(-ht + thickness * i / segments) for i in range(n)]

    wave_front = []  # отклонение Y на переднем торце
    wave_top = []    # отклонение Z на верхнем торце
    wave_bot = []    # отклонение Z на нижнем торце

    for i in range(n):
        wave_front.append(amp * ((-1) ** i) * rng.uniform(0.3, 1.0))
        wave_top.append(amp * ((-1) ** i) * rng.uniform(0.3, 1.0))
        wave_bot.append(amp * ((-1) ** (i + 1)) * rng.uniform(0.3, 1.0))

    # 4 вершины на каждое сечение:
    #   v0: back-bottom  (-Y, -Z) — у корешка, внизу
    #   v1: front-bottom (+Y, -Z) — спереди, внизу
    #   v2: front-top    (+Y, +Z) — спереди, вверху
    #   v3: back-top     (-Y, +Z) — у корешка, вверху
    slices = []
    for i in range(n):
        x = xs[i]
        y_front = hw + wave_front[i]
        z_top = hh + wave_top[i]
        z_bot = -hh + wave_bot[i]
        y_back = -hw - back_shift # плоский, у корешка

        v0 = bm.verts.new((x, y_back, z_bot))
        v1 = bm.verts.new((x, y_front, z_bot))
        v2 = bm.verts.new((x, y_front, z_top))
        v3 = bm.verts.new((x, y_back, z_top))
        slices.append((v0, v1, v2, v3))

    # Грани между соседними сечениями
    for i in range(n - 1):
        a0, a1, a2, a3 = slices[i]
        b0, b1, b2, b3 = slices[i + 1]

        # Нижний торец (видимый, -Z)
        bm.faces.new([a0, a1, b1, b0])
        # Передний торец (видимый, +Y)
        bm.faces.new([a1, a2, b2, b1])
        # Верхний торец (видимый, +Z)
        bm.faces.new([a2, a3, b3, b2])
        # Задний (у корешка, плоский, -Y)
        bm.faces.new([a3, a0, b0, b3])

    # Торцевые крышки (левая и правая, примыкают к обложке)
    s = slices[0]
    bm.faces.new([s[0], s[3], s[2], s[1]])  # левый торец
    s = slices[-1]
    bm.faces.new([s[0], s[1], s[2], s[3]])  # правый торец

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return bpy.data.objects.new(name, mesh)



COVER_COLORS = [
    (0.5, 0.12, 0.1, 1.0),    # тёмно-красный
    (0.1, 0.15, 0.35, 1.0),   # тёмно-синий
    (0.12, 0.3, 0.15, 1.0),   # тёмно-зелёный
    (0.55, 0.35, 0.15, 1.0),  # коричневый
    (0.08, 0.08, 0.08, 1.0),  # чёрный
    (0.7, 0.6, 0.3, 1.0),     # горчичный
    (0.35, 0.15, 0.3, 1.0),   # фиолетовый
    (0.6, 0.25, 0.12, 1.0),   # оранжево-коричневый
    (0.2, 0.2, 0.2, 1.0),     # тёмно-серый
    (0.45, 0.1, 0.1, 1.0),    # бордовый
    (0.15, 0.25, 0.35, 1.0),  # синевато-серый
    (0.3, 0.35, 0.2, 1.0),    # оливковый
    (0.65, 0.5, 0.35, 1.0),   # бежево-коричневый
    (0.4, 0.2, 0.1, 1.0),     # тёплый коричневый
    (0.8, 0.75, 0.6, 1.0),    # светло-бежевый
]


def mat_cover(rng):
    color = rng.choice(COVER_COLORS)
    # Немного рандомизируем оттенок
    color = tuple(max(0, min(1, c + rng.uniform(-0.05, 0.05))) for c in color[:3]) + (1.0,)
    mat = get_or_create_mat(f"M_BookCover_{id(color)}")
    return setup_principled(mat, color, roughness=rng.uniform(0.55, 0.75), specular=0.2)


def mat_pages():
    mat = get_or_create_mat("M_BookPages")
    return setup_principled(mat, (0.9, 0.87, 0.8, 1.0), roughness=0.9, specular=0.05)

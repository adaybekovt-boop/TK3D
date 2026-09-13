"""
Генератор шкафов — headless скрипт.

Использование:
    blender --background --python tools/generators/wardrobes/generate.py -- [опции]

Опции:
    --type TYPE         single, double, with_drawers, mixed
    --count N           Количество (по умолчанию 10)
    --output DIR        Папка для результатов (по умолчанию output/wardrobes)
    --seed N            Начальный seed
    --resolution WxH    Разрешение рендера (по умолчанию 800x800)
    --save-blend        Сохранять .blend в assets/furniture/
"""

import bpy
import os
import sys

# Paths & module cache
script_dir = os.path.dirname(os.path.realpath(__file__))
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)
generators_dir = os.path.dirname(script_dir)
if generators_dir not in sys.path:
    sys.path.insert(0, generators_dir)
if script_dir in sys.path:
    sys.path.remove(script_dir)
sys.path.insert(0, script_dir)
for _m in list(sys.modules.keys()):
    if _m in ('helpers', 'wardrobe_types'):
        del sys.modules[_m]

from wardrobe_types import generate_wardrobe, WARDROBE_TYPES
from common.generate_base import parse_args, run_batch, link_objects
from common.preview_scene import setup_preview


def _generate_fn(item_seed, args, rng):
    active_types = list(WARDROBE_TYPES.keys()) if args.type == 'mixed' else [args.type]
    subtype = rng.choice(active_types)
    objects = generate_wardrobe(item_seed, subtype=subtype)
    basename = f"wardrobe_{subtype}_{item_seed}"
    variant = {'basename': basename, 'seed': item_seed, 'subtype': subtype}

    link_objects(objects)
    if args.save_blend:
        from common.generate_base import save_asset_blend
        filepath = os.path.join(project_dir, "assets", "furniture", f"{basename}.blend")
        save_asset_blend(objects, basename, filepath)

    return objects, variant


def main():
    args = parse_args(
        description="Wardrobe generator",
        type_choices=list(WARDROBE_TYPES.keys()) + ['mixed'],
    )

    run_batch(
        args, project_dir,
        category='wardrobes',
        generate_fn=_generate_fn,
        asset_subdir=None,
        gallery_title='Wardrobe Generator',
        gallery_info_fn=lambda v: f"Seed: {v['seed']} — {v['subtype']}",
        preview_fn=lambda objs: setup_preview(objs, style='product'),
    )


if __name__ == "__main__":
    main()

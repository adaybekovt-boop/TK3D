"""
Генератор часов — headless скрипт с рендером и галереей.

Использование:
    blender --background --python tools/generators/clocks/generate.py -- [опции]

Опции:
    --type TYPE         round, square, alarm, grandfather, mixed (по умолчанию mixed)
    --count N           Количество вариантов (по умолчанию 10)
    --output DIR        Папка для результатов (по умолчанию output/clocks)
    --seed N            Начальный seed (по умолчанию случайный)
    --resolution WxH    Разрешение рендера (по умолчанию 800x800)
    --save-blend        Сохранять .blend в assets/decor/<category>/
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
    if _m in ('helpers', 'clock_types'):
        del sys.modules[_m]

from clock_types import generate_clock, CLOCK_TYPES, ASSET_CATEGORIES
from common.generate_base import parse_args, run_batch, link_objects
from common.preview_scene import setup_preview


def _generate_fn(item_seed, args, rng):
    active_types = list(CLOCK_TYPES.keys()) if args.type == 'mixed' else [args.type]
    subtype = rng.choice(active_types)
    objects = generate_clock(item_seed, subtype=subtype)
    basename = f"clock_{subtype}_{item_seed}"

    link_objects(objects)
    if args.save_blend:
        from common.generate_base import save_asset_blend
        asset_cat = ASSET_CATEGORIES.get(subtype, 'wall')
        filepath = os.path.join(project_dir, "assets", "decor", asset_cat, f"{basename}.blend")
        save_asset_blend(objects, basename, filepath)

    return objects, {'basename': basename, 'seed': item_seed, 'subtype': subtype}


def main():
    args = parse_args(
        description="Clock generator",
        type_choices=['round', 'square', 'alarm', 'grandfather', 'mixed'],
        has_subtype=True,
    )

    run_batch(
        args, project_dir,
        category='clocks',
        generate_fn=_generate_fn,
        asset_subdir=None,  # handled in generate_fn per type
        gallery_title='Clock Generator',
        gallery_info_fn=lambda v: f"Seed: {v['seed']} — {v['subtype']}",
        preview_fn=lambda objs: setup_preview(objs, style='product'),
    )


if __name__ == "__main__":
    main()

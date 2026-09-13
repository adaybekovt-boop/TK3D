"""
Генератор ламп — headless скрипт с рендером и галереей.

Использование:
    blender --background --python tools/generators/lamps/generate.py -- [опции]

Опции:
    --type TYPE         tabletop, floor, wall, ceiling, mixed (по умолчанию mixed)
    --subtype SUBTYPE   classic, nightlight, floor_lamp, arc_lamp, sconce, pendant, flush, mixed
    --count N           Количество вариантов (по умолчанию 10)
    --output DIR        Папка для результатов (по умолчанию output/lamps)
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
    if _m in ('helpers', 'tabletop', 'floor_lamps', 'wall_lamps', 'ceiling_lamps'):
        del sys.modules[_m]

from tabletop import generate_tabletop_lamp, TABLETOP_TYPES
from floor_lamps import generate_floor_lamp, FLOOR_TYPES
from wall_lamps import generate_wall_lamp, WALL_TYPES
from ceiling_lamps import generate_ceiling_lamp, CEILING_TYPES
from common.generate_base import parse_args, run_batch, link_objects
from common.preview_scene import setup_preview

# Маппинг тип → генератор, подтипы, asset-категория
TYPE_MAP = {
    'tabletop': {
        'generator': generate_tabletop_lamp,
        'subtypes': TABLETOP_TYPES,
        'prefix': 'lamp_tabletop',
        'asset_dir': 'tabletop',
    },
    'floor': {
        'generator': generate_floor_lamp,
        'subtypes': FLOOR_TYPES,
        'prefix': 'lamp_floor',
        'asset_dir': 'floor',
    },
    'wall': {
        'generator': generate_wall_lamp,
        'subtypes': WALL_TYPES,
        'prefix': 'lamp_wall',
        'asset_dir': 'wall',
    },
    'ceiling': {
        'generator': generate_ceiling_lamp,
        'subtypes': CEILING_TYPES,
        'prefix': 'lamp_ceiling',
        'asset_dir': 'ceiling',
    },
}


def _generate_fn(item_seed, args, rng):
    if args.type == 'mixed':
        active_types = list(TYPE_MAP.keys())
    else:
        active_types = [args.type]

    chosen_type = rng.choice(active_types)
    tm = TYPE_MAP[chosen_type]

    if args.subtype == 'mixed' or args.subtype not in tm['subtypes']:
        subtype = rng.choice(list(tm['subtypes'].keys()))
    else:
        subtype = args.subtype

    objects = tm['generator'](item_seed, subtype=subtype)

    basename = f"{tm['prefix']}_{subtype}_{item_seed}"

    variant = {
        'basename': basename,
        'seed': item_seed,
        'obj_type': chosen_type,
        'subtype': subtype,
    }

    # Link before save so objects are in collection
    link_objects(objects)

    if args.save_blend:
        from common.generate_base import save_asset_blend
        filepath = os.path.join(project_dir, "assets", "decor", tm['asset_dir'], f"{basename}.blend")
        save_asset_blend(objects, basename, filepath)
        variant['blend_file'] = f"{basename}.blend"

    return objects, variant


def main():
    args = parse_args(
        description="Lamp generator",
        type_choices=['tabletop', 'floor', 'wall', 'ceiling', 'mixed'],
        has_subtype=True,
    )

    run_batch(
        args, project_dir,
        category='lamps',
        generate_fn=_generate_fn,
        asset_subdir=None,
        gallery_title='Lamp Generator',
        gallery_info_fn=lambda v: f"Seed: {v['seed']} — {v['obj_type']} / {v['subtype']}",
        preview_fn=lambda objs: setup_preview(objs, style='product'),
    )


if __name__ == "__main__":
    main()

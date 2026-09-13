"""
Генератор посуды — headless скрипт с рендером и галереей.

Использование:
    blender --background --python tools/generators/kitchenware/generate.py -- [опции]

Опции:
    --type TYPE         Тип: plates, vases, glasses, cups, mixed (по умолчанию mixed)
    --subtype SUBTYPE   Подтип (dinner, soup, classic, tumbler, wine и т.д., по умолчанию mixed)
    --count N           Количество вариантов (по умолчанию 10)
    --output DIR        Папка для результатов (по умолчанию output/kitchenware)
    --seed N            Начальный seed (по умолчанию случайный)
    --resolution WxH    Разрешение рендера (по умолчанию 800x800)
    --save-blend        Сохранять .blend файлы в assets/decor/
"""

import math
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

# Ensure local modules take priority over cached ones from asset_generator addon
for _m in list(sys.modules.keys()):
    if _m in ('bottles','helpers', 'plates', 'vases', 'glasses', 'cups'):
        del sys.modules[_m]

from plates import generate_plate, PLATE_TYPES
from vases import generate_vase, VASE_TYPES
from glasses import generate_glass, GLASS_TYPES
from cups import generate_cup, CUP_TYPES
from bottles import generate_bottle, BOTTLE_TYPES
from common.generate_base import parse_args, run_batch
from common.preview_scene import setup_preview

# Type map: generator function, subtypes dict, prefix
TYPE_MAP = {
    'plates':  {'generator': generate_plate, 'subtypes': PLATE_TYPES, 'prefix': 'plate'},
    'vases':   {'generator': generate_vase,  'subtypes': VASE_TYPES,  'prefix': 'vase'},
    'glasses': {'generator': generate_glass, 'subtypes': GLASS_TYPES, 'prefix': 'glass'},
    'cups':    {'generator': generate_cup,   'subtypes': CUP_TYPES,   'prefix': 'cup'},
    'bottles':    {'generator': generate_bottle,   'subtypes': BOTTLE_TYPES,   'prefix': 'bottle'},
}


def _generate_fn(item_seed, args, rng):
    # Determine active types
    if args.type == 'mixed':
        active_types = list(TYPE_MAP.keys())
    else:
        active_types = [args.type]

    chosen_type = rng.choice(active_types)
    tm = TYPE_MAP[chosen_type]

    # Determine subtype
    if args.subtype == 'mixed' or args.subtype not in tm['subtypes']:
        subtype = rng.choice(list(tm['subtypes'].keys()))
    else:
        subtype = args.subtype

    # Generate object
    if chosen_type == 'plates':
        result = [generate_plate(item_seed, plate_type=subtype)]
    elif chosen_type == 'vases':
        result = [generate_vase(item_seed, vase_type=subtype)]
    elif chosen_type == 'glasses':
        result = [generate_glass(item_seed, glass_type=subtype)]
    elif chosen_type == 'bottles':
        result = [generate_bottle(item_seed, bottle_type=subtype)]
    elif chosen_type == 'cups':
        result = generate_cup(item_seed, cup_type=subtype)  # returns list
        for obj in result:
            obj.rotation_euler = (0, 0, math.radians(-100))

    basename = f"{tm['prefix']}_{subtype}_{item_seed}"
    variant = {
        'basename': basename,
        'seed': item_seed,
        'obj_type': chosen_type,
        'subtype': subtype,
    }
    return result, variant


def main():
    args = parse_args(
        description="Kitchenware generator",
        type_choices=list(TYPE_MAP.keys()) + ['mixed'],
        has_subtype=True,
    )

    run_batch(
        args, project_dir,
        category='kitchenware',
        generate_fn=_generate_fn,
        asset_subdir='tabletop',
        gallery_title='Kitchenware Generator',
        gallery_info_fn=lambda v: f"Seed: {v['seed']} — {v['obj_type']} / {v['subtype']}",
        preview_fn=lambda objs: setup_preview(objs, style='product'),
    )


if __name__ == "__main__":
    main()

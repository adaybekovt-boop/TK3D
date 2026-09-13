"""
Генератор наборов книг — headless скрипт.

Использование:
    blender --background --python tools/generators/booksets/generate.py -- [опции]

Опции:
    --type TYPE         row, stack, leaning, mixed, random
    --count N           Количество (по умолчанию 10)
    --output DIR        Папка для результатов (по умолчанию output/booksets)
    --seed N            Начальный seed
    --resolution WxH    Разрешение рендера (по умолчанию 800x800)
    --save-blend        Сохранять .blend в assets/decor/tabletop/
"""

import os
import sys

# Paths & module cache
script_dir = os.path.dirname(os.path.realpath(__file__))
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)
# common must be importable
generators_dir = os.path.dirname(script_dir)
if generators_dir not in sys.path:
    sys.path.insert(0, generators_dir)
if script_dir in sys.path:
    sys.path.remove(script_dir)
sys.path.insert(0, script_dir)
for _m in list(sys.modules.keys()):
    if _m in ('helpers', 'bookset_types'):
        del sys.modules[_m]

from bookset_types import generate_bookset, BOOKSET_TYPES
from common.generate_base import parse_args, run_batch
from common.preview_scene import setup_preview


def _generate_fn(item_seed, args, rng):
    active_types = list(BOOKSET_TYPES.keys()) if args.type == 'random' else [args.type]
    subtype = rng.choice(active_types)
    objects = generate_bookset(item_seed, subtype=subtype)
    basename = f"bookset_{subtype}_{item_seed}"
    return objects, {'basename': basename, 'seed': item_seed, 'subtype': subtype}


def main():
    args = parse_args(
        description="Bookset generator",
        type_choices=list(BOOKSET_TYPES.keys()) + ['random'],
    )

    run_batch(
        args, project_dir,
        category='booksets',
        generate_fn=_generate_fn,
        asset_subdir='tabletop',
        gallery_title='Bookset Generator',
        gallery_info_fn=lambda v: f"Seed: {v['seed']} — {v['subtype']}",
        preview_fn=lambda objs: setup_preview(objs, style='surface'),
    )


if __name__ == "__main__":
    main()

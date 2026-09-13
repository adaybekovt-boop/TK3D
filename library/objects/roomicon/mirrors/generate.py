"""
Генератор зеркал — headless скрипт.

Использование:
    blender --background --python tools/generators/mirrors/generate.py -- [опции]

Опции:
    --type TYPE         rectangle, round, oval, arched, with_shelf, mixed
    --count N           Количество (по умолчанию 10)
    --output DIR        Папка для результатов (по умолчанию output/mirrors)
    --seed N            Начальный seed
    --resolution WxH    Разрешение рендера (по умолчанию 800x800)
    --save-blend        Сохранять .blend в assets/decor/wall/
"""

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
    if _m in ('helpers', 'mirror_types'):
        del sys.modules[_m]

from mirror_types import generate_mirror, MIRROR_TYPES
from common.generate_base import parse_args, run_batch
from common.preview_scene import setup_preview


def _generate_fn(item_seed, args, rng):
    active_types = list(MIRROR_TYPES.keys()) if args.type == 'mixed' else [args.type]
    subtype = rng.choice(active_types)
    objects = generate_mirror(item_seed, subtype=subtype)
    basename = f"mirror_{subtype}_{item_seed}"
    return objects, {'basename': basename, 'seed': item_seed, 'subtype': subtype}


def main():
    args = parse_args(
        description="Mirror generator",
        type_choices=list(MIRROR_TYPES.keys()) + ['mixed'],
    )

    run_batch(
        args, project_dir,
        category='mirrors',
        generate_fn=_generate_fn,
        asset_subdir='wall',
        gallery_title='Mirror Generator',
        gallery_info_fn=lambda v: f"Seed: {v['seed']} — {v['subtype']}",
        preview_fn=lambda objs: setup_preview(objs, style='wall'),
    )


if __name__ == "__main__":
    main()

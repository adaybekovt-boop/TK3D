"""
Генератор штор — headless скрипт.

Использование:
    blender --background --python tools/generators/curtains/generate.py -- [опции]

Опции:
    --type TYPE         straight, gathered, sheer, mixed
    --count N           Количество (по умолчанию 10)
    --output DIR        Папка для результатов (по умолчанию output/curtains)
    --seed N            Начальный seed
    --resolution WxH    Разрешение рендера (по умолчанию 800x800)
    --save-blend        Сохранять .blend в assets/decor/wall_floor/
    --window-width F    Ширина окна (по умолчанию 1.2)
    --window-top F      Верх окна Z (по умолчанию 2.2)
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
    if _m in ('helpers', 'curtain_types'):
        del sys.modules[_m]

from curtain_types import generate_curtain, CURTAIN_TYPES
from common.generate_base import parse_args, run_batch
from common.preview_scene import setup_preview


def _add_custom_args(args):
    """Parse extra curtain-specific arguments."""
    import argparse
    argv = sys.argv
    if '--' in argv:
        argv = argv[argv.index('--') + 1:]
    else:
        argv = []
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--window-width', type=float, default=1.2)
    parser.add_argument('--window-top', type=float, default=2.2)
    extra, _ = parser.parse_known_args(argv)
    args.window_width = extra.window_width
    args.window_top = extra.window_top


def _generate_fn(item_seed, args, rng):
    active_types = list(CURTAIN_TYPES.keys()) if args.type == 'mixed' else [args.type]
    subtype = rng.choice(active_types)
    objects = generate_curtain(item_seed, subtype=subtype,
                               window_width=args.window_width,
                               window_top_z=args.window_top)
    basename = f"curtain_{subtype}_{item_seed}"
    return objects, {'basename': basename, 'seed': item_seed, 'subtype': subtype}


def main():
    args = parse_args(
        description="Curtain generator",
        type_choices=list(CURTAIN_TYPES.keys()) + ['mixed'],
    )
    _add_custom_args(args)

    run_batch(
        args, project_dir,
        category='curtains',
        generate_fn=_generate_fn,
        asset_subdir='wall_floor',
        gallery_title='Curtain Generator',
        gallery_info_fn=lambda v: f"Seed: {v['seed']} — {v['subtype']}",
        preview_fn=lambda objs: setup_preview(objs, style='wall'),
    )


if __name__ == "__main__":
    main()

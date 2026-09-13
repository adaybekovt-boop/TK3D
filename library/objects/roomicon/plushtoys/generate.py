"""
Plush toys generator — headless script.

Usage:
    blender --background --python tools/generators/plushtoys/generate.py -- [options]

Options:
    --type TYPE         bear, bunny, penguin, duck, mixed
    --count N           Count (default 10)
    --output DIR        Output folder (default output/plushtoys)
    --seed N            Starting seed
    --resolution WxH    Render resolution (default 800x800)
    --save-blend        Save .blend to assets/decor/bed/
"""

import os
import sys

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
    if _m in ('helpers', 'plushtoy_types'):
        del sys.modules[_m]

from plushtoy_types import generate_plushtoy, PLUSHTOY_TYPES
from common.generate_base import parse_args, run_batch
from common.preview_scene import setup_preview


def _generate_fn(item_seed, args, rng):
    active_types = list(PLUSHTOY_TYPES.keys()) if args.type == 'mixed' else [args.type]
    subtype = rng.choice(active_types)
    objects = generate_plushtoy(item_seed, subtype=subtype)
    basename = f"plushtoy_{subtype}_{item_seed}"
    return objects, {'basename': basename, 'seed': item_seed, 'subtype': subtype}


def main():
    args = parse_args(
        description="Plush toy generator",
        type_choices=list(PLUSHTOY_TYPES.keys()) + ['mixed'],
    )
    run_batch(
        args, project_dir,
        category='plushtoys',
        generate_fn=_generate_fn,
        asset_subdir='bed',
        gallery_title='Plush Toy Generator',
        gallery_info_fn=lambda v: f"Seed: {v['seed']} — {v['subtype']}",
        preview_fn=lambda objs: setup_preview(objs, style='surface', rotate_z=3.14159),
    )


if __name__ == "__main__":
    main()

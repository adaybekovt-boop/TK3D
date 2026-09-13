"""
Генератор кроватей и диванов — headless скрипт.

Использование:
    blender --background --python tools/generators/seating/generate.py -- [опции]

Опции:
    --type TYPE         single_bed, double_bed, bunk_bed, sofa, daybed, mixed
    --count N           Количество (по умолчанию 10)
    --output DIR        Папка для результатов (по умолчанию output/seating)
    --seed N            Начальный seed
    --resolution WxH    Разрешение рендера (по умолчанию 800x800)
    --save-blend        Сохранять .blend в assets/furniture/
"""

import bpy
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
    if _m in ('helpers', 'seating_types'):
        del sys.modules[_m]

from seating_types import generate_seating, SEATING_TYPES
from common.generate_base import parse_args, run_batch, link_objects
from common.preview_scene import setup_preview


def _generate_fn(item_seed, args, rng):
    active_types = list(SEATING_TYPES.keys()) if args.type == 'mixed' else [args.type]
    subtype = rng.choice(active_types)
    objects = generate_seating(item_seed, subtype=subtype)
    # Prefix by furniture type (bed/sofa), not generator name (seating)
    if 'bed' in subtype:
        prefix = 'bed'
    elif subtype in ('sofa', 'daybed'):
        prefix = 'sofa'
    else:
        prefix = 'seating'
    basename = f"{prefix}_{subtype}_{item_seed}"

    link_objects(objects)
    if args.save_blend:
        from common.generate_base import save_asset_blend
        filepath = os.path.join(project_dir, "assets", "furniture", f"{basename}.blend")
        save_asset_blend(objects, basename, filepath)

    return objects, {'basename': basename, 'seed': item_seed, 'subtype': subtype}


def main():
    args = parse_args(
        description="Seating & beds generator",
        type_choices=list(SEATING_TYPES.keys()) + ['mixed'],
    )
    run_batch(
        args, project_dir,
        category='seating',
        generate_fn=_generate_fn,
        asset_subdir=None,
        gallery_title='Seating & Beds Generator',
        gallery_info_fn=lambda v: f"Seed: {v['seed']} — {v['subtype']}",
        preview_fn=lambda objs: setup_preview(objs, style='product',
                                               key_energy=60, fill_energy=25),
    )


if __name__ == "__main__":
    main()

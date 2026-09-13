"""
Генератор фоторамок — headless скрипт.

Использование:
    blender --background --python tools/generators/photoframes/generate.py -- [опции]

Опции:
    --type TYPE         tabletop_simple, tabletop_bevel, wall_simple, wall_bevel, mixed
    --count N           Количество (по умолчанию 10)
    --pool DIR          Папка с фотографиями (по умолчанию assets/pool/photoframes)
    --output DIR        Папка для результатов (по умолчанию output/photoframes)
    --seed N            Начальный seed
    --resolution WxH    Разрешение рендера (по умолчанию 800x800)
    --save-blend        Сохранять .blend в assets/decor/tabletop/
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
    if _m in ('helpers', 'photoframe_types'):
        del sys.modules[_m]

from photoframe_types import generate_photoframe, PHOTOFRAME_TYPES
from helpers import list_images
from common.generate_base import parse_args, run_batch
from common.preview_scene import setup_preview


def main():
    args = parse_args(
        description="Photo frame generator",
        type_choices=list(PHOTOFRAME_TYPES.keys()) + ['mixed'],
        has_pool=True,
    )

    if args.pool is None:
        args.pool = os.path.join(project_dir, "assets", "pool", "photoframes")
    pool_dir = os.path.abspath(args.pool)

    images = list_images(pool_dir)
    if images:
        print(f"Image pool: {pool_dir} ({len(images)} images)")
    else:
        print(f"No images in {pool_dir} — using placeholder")

    active_types = list(PHOTOFRAME_TYPES.keys()) if True else []

    def _generate_fn(item_seed, args, rng):
        types = list(PHOTOFRAME_TYPES.keys()) if args.type == 'mixed' else [args.type]
        subtype = rng.choice(types)
        image_path = rng.choice(images) if images else None

        objects = generate_photoframe(item_seed, image_path=image_path, subtype=subtype)

        img_base = ""
        if image_path:
            img_base = os.path.splitext(os.path.basename(image_path))[0] + "_"
        basename = f"photoframe_{subtype}_{img_base}{item_seed}"

        return objects, {
            'basename': basename,
            'seed': item_seed,
            'subtype': subtype,
            'image': image_path or '',
        }

    # Настольные — product, настенные — wall. Смешанный — product.
    preview_style = 'wall' if args.type.startswith('wall') else 'product'

    run_batch(
        args, project_dir,
        category='photoframes',
        generate_fn=_generate_fn,
        asset_subdir='tabletop',
        gallery_title='Photo Frame Generator',
        gallery_info_fn=lambda v: f"Seed: {v['seed']} — {v['subtype']}",
        preview_fn=lambda objs: setup_preview(objs, style=preview_style),
        cleanup_images=True,
    )


if __name__ == "__main__":
    main()

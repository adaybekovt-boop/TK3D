"""
Генератор картин — headless скрипт с рендером и галереей.

Использование:
    blender --background --python tools/generators/paintings/generate.py -- [опции]

Опции:
    --type TYPE         none, simple, bevel, mixed (тип рамки, по умолчанию mixed)
    --count N           Количество вариантов (по умолчанию 10)
    --pool DIR          Папка с картинками (по умолчанию assets/pool/pictures)
    --output DIR        Папка для результатов (по умолчанию output/paintings)
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
    if _m in ('helpers', 'painting_types'):
        del sys.modules[_m]

from painting_types import generate_painting, list_images, PAINTING_TYPES
from common.generate_base import parse_args, run_batch
from common.preview_scene import setup_preview


def main():
    args = parse_args(
        description="Painting generator",
        type_choices=list(PAINTING_TYPES.keys()) + ['mixed'],
        has_pool=True,
    )

    # Resolve image pool
    if args.pool is None:
        args.pool = os.path.join(project_dir, "assets", "pool", "pictures")
    pool_dir = os.path.abspath(args.pool)

    images = list_images(pool_dir)
    if not images:
        print(f"ERROR: No images found in {pool_dir}")
        print("Add .jpg/.png files to assets/pool/pictures/")
        return

    print(f"Image pool: {pool_dir} ({len(images)} images)")

    active_types = list(PAINTING_TYPES.keys()) if args.type == 'mixed' else [args.type]

    def _generate_fn(item_seed, args, rng):
        frame_type = rng.choice(active_types)
        image_path = rng.choice(images)
        objects = generate_painting(item_seed, image_path, frame_type=frame_type)
        img_base = os.path.splitext(os.path.basename(image_path))[0]
        basename = f"painting_{frame_type}_{img_base}_{item_seed}"
        return objects, {
            'basename': basename,
            'seed': item_seed,
            'frame_type': frame_type,
            'image': image_path,
        }

    run_batch(
        args, project_dir,
        category='paintings',
        generate_fn=_generate_fn,
        asset_subdir='wall',
        gallery_title='Painting Generator',
        gallery_info_fn=lambda v: (
            f"Seed: {v['seed']} — {v['frame_type']}<br>"
            f"{os.path.basename(v.get('image', ''))}"
        ),
        cleanup_images=True,
        preview_fn=lambda objs: setup_preview(objs, style='wall'),
    )


if __name__ == "__main__":
    main()

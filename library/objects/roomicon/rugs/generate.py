"""
Генератор ковров — headless скрипт с рендером и галереей.

Использование:
    blender --background --python tools/generators/rugs/generate.py -- [опции]

Опции:
    --type TYPE         rectangle, circle, oval, mixed (тип ковра, по умолчанию mixed)
    --count N           Количество вариантов (по умолчанию 10)
    --pool DIR          Папка с текстурами (по умолчанию assets/pool/rugs)
    --output DIR        Папка для результатов (по умолчанию output/rugs)
    --seed N            Начальный seed
    --resolution WxH    Разрешение рендера (по умолчанию 800x800)
    --save-blend        Сохранять .blend в assets/decor/floor/
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
    if _m in ('helpers', 'rugs_types'):
        del sys.modules[_m]

from rugs_types import generate_rug, list_textures, RUG_TYPES
from common.generate_base import parse_args, run_batch
from common.preview_scene import setup_preview


def main():
    args = parse_args(
        description="Rug generator",
        type_choices=list(RUG_TYPES.keys()) + ['mixed'],
        has_pool=True,
    )

    # Resolve texture pool
    if args.pool is None:
        args.pool = os.path.join(project_dir, "assets", "pool", "rugs")
    pool_dir = os.path.abspath(args.pool)

    textures = list_textures(pool_dir)
    if textures:
        print(f"Texture pool: {pool_dir} ({len(textures)} textures)")
    else:
        print(f"No textures in {pool_dir} — using procedural patterns")

    # Determine active rug types
    if args.type == 'mixed':
        active_types = list(RUG_TYPES.keys())
    else:
        active_types = [args.type]

    def _generate_fn(item_seed, args, rng):
        rug_type = rng.choice(active_types)
        texture_path = rng.choice(textures)

        objects = generate_rug(item_seed, rug_type, texture_path)

        if texture_path:
            tex_base = os.path.splitext(os.path.basename(texture_path))[0]
            basename = f"rug_{rug_type}_{tex_base}_{item_seed}"
        else:
            basename = f"rug_{rug_type}_{item_seed}"

        return objects, {
            'basename': basename,
            'seed': item_seed,
            'rug_type': rug_type,
            'texture': texture_path or '',
        }

    def _gallery_info(v):
        tex_name = os.path.basename(v.get('texture', ''))
        info = f"Seed: {v['seed']} — {v['rug_type']}"
        if tex_name:
            info += f" ({tex_name})"
        return info

    run_batch(
        args, project_dir,
        category='rugs',
        generate_fn=_generate_fn,
        asset_subdir='floor',
        gallery_title='Rug Generator',
        gallery_info_fn=_gallery_info,
        cleanup_images=True,
        preview_fn=lambda objs: setup_preview(objs, style='wall'),
    )


if __name__ == "__main__":
    main()

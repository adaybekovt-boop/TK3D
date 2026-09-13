"""Base utilities for headless generator scripts.

Provides shared boilerplate: argument parsing, scene clearing,
HTML gallery generation, and the main batch loop.
"""

import bpy
import os
import sys
import argparse
import random
import time


def get_project_dir(script_file):
    """Derive project root from a generator's __file__."""
    script_dir = os.path.dirname(os.path.realpath(script_file))
    return os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))


def setup_script_path(script_file, local_modules=None):
    """Set up sys.path for a headless generator script.

    - Adds project_dir to sys.path
    - Puts the script's own directory first
    - Clears cached local_modules from sys.modules

    Args:
        script_file: The generator's __file__ (e.g. generate.py)
        local_modules: Set of module names to clear from cache
                       (e.g. {'helpers', 'bookset_types'})
    Returns:
        (script_dir, project_dir)
    """
    script_dir = os.path.dirname(os.path.realpath(script_file))
    project_dir = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))

    if project_dir not in sys.path:
        sys.path.insert(0, project_dir)
    if script_dir in sys.path:
        sys.path.remove(script_dir)
    sys.path.insert(0, script_dir)

    if local_modules:
        for _m in list(sys.modules.keys()):
            if _m in local_modules:
                del sys.modules[_m]

    return script_dir, project_dir


def parse_args(description, type_choices, has_subtype=False, has_pool=False):
    """Parse common generator CLI arguments.

    Args:
        description: e.g. "Bookset generator"
        type_choices: e.g. ['row', 'stack', 'leaning', 'mixed', 'random']
        has_subtype: Add --subtype argument
        has_pool: Add --pool argument for texture/image pool

    Returns:
        argparse.Namespace
    """
    argv = sys.argv
    if '--' in argv:
        argv = argv[argv.index('--') + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--type', type=str, default=type_choices[-1],
                        choices=type_choices)
    if has_subtype:
        parser.add_argument('--subtype', type=str, default='mixed',
                            help='Subtype (default: mixed)')
    if has_pool:
        parser.add_argument('--pool', type=str, default=None)
    parser.add_argument('--count', type=int, default=10)
    parser.add_argument('--output', type=str, default=None)
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--resolution', type=str, default='800x800')
    parser.add_argument('--save-blend', action='store_true')
    return parser.parse_args(argv)


def clear_scene(cleanup_images=False):
    """Remove all objects and orphan data from the scene."""
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        if mat.users == 0:
            bpy.data.materials.remove(mat)
    if cleanup_images:
        for img in list(bpy.data.images):
            if img.users == 0:
                bpy.data.images.remove(img)
    for cam in list(bpy.data.cameras):
        if cam.users == 0:
            bpy.data.cameras.remove(cam)
    for light in list(bpy.data.lights):
        if light.users == 0:
            bpy.data.lights.remove(light)


def generate_gallery(title, output_dir, variants, info_fn=None):
    """Generate index.html gallery from ALL .png files in output_dir.

    Includes both current variants and previously generated images.
    """
    # Собираем все .png из папки
    all_pngs = sorted(f for f in os.listdir(output_dir) if f.endswith('.png'))

    # Строим lookup из текущих variants для info
    variant_map = {}
    for v in variants:
        variant_map[v['basename']] = v

    count = len(all_pngs)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title} — {count} Variants</title>
<style>
body {{ font-family: -apple-system, sans-serif; background: #1a1a1a; color: #eee; margin: 20px; }}
h1 {{ text-align: center; margin-bottom: 30px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }}
.card {{ background: #2a2a2a; border-radius: 8px; overflow: hidden; }}
.card img {{ width: 100%%; cursor: pointer; display: block; }}
.card .info {{ padding: 8px 12px; font-size: 12px; }}
.card .seed {{ font-weight: bold; color: #7cb3ff; }}
.card .filename {{ color: #888; font-size: 11px; margin-top: 2px; font-family: monospace; word-break: break-all; }}
a {{ color: #7cb3ff; text-decoration: none; }}
</style>
</head>
<body>
<h1>{title} — {count} Variants</h1>
<div class="grid">
"""
    for png in all_pngs:
        bn = png[:-4]  # strip .png
        v = variant_map.get(bn)

        if v and info_fn:
            info_line = info_fn(v)
        elif v:
            parts = [f"Seed: {v['seed']}"]
            if v.get('obj_type'):
                parts.append(v['obj_type'])
            if v.get('subtype'):
                parts.append(v['subtype'])
            info_line = ' — '.join(parts)
        else:
            # Старый файл — парсим имя
            info_line = bn.replace('_', ' ')

        html += f"""<div class="card">
<a href="{png}" target="_blank"><img src="{png}" loading="lazy"></a>
<div class="info"><div class="seed">{info_line}</div><div class="filename">{bn}</div></div>
</div>
"""
    html += "</div>\n</body>\n</html>"

    with open(os.path.join(output_dir, 'index.html'), 'w') as f:
        f.write(html)


def link_objects(objects):
    """Link objects to the current collection (skip if already linked)."""
    col = bpy.context.collection
    existing = {o.name for o in col.objects}
    for obj in objects:
        if obj.name not in existing:
            col.objects.link(obj)


def save_asset_blend(objects, name, filepath):
    """Wrap objects as asset with Empty root and save as .blend."""
    # Import from project root
    _project = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.realpath(__file__)))))
    if _project not in sys.path:
        sys.path.insert(0, _project)
    from core.asset_loader import wrap_as_asset

    root = wrap_as_asset(objects, name)
    if root is None:
        return

    col = bpy.context.collection
    existing = {o.name for o in col.objects}
    if root.name not in existing:
        col.objects.link(root)
    for child in root.children_recursive:
        if child.name not in existing:
            col.objects.link(child)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=filepath, copy=True)


def render_preview(output_path, res_x, res_y):
    """Render current scene to file."""
    scene = bpy.context.scene
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)


def run_batch(args, project_dir, category, generate_fn,
              output_subdir=None, asset_subdir=None,
              gallery_title=None, gallery_info_fn=None,
              cleanup_images=False, preview_fn=None):
    """Main batch loop for headless generation.

    Args:
        args: Parsed argparse namespace (needs: output, seed, resolution, count, save_blend, type)
        project_dir: Project root directory
        category: Short name, e.g. 'booksets'
        generate_fn: Callable(item_seed, args, rng) -> (objects, variant_dict)
            Must return:
              - objects: list of bpy objects to link/render
              - variant_dict: dict with at least 'basename', 'seed'
        output_subdir: Override output subdirectory (default: category)
        asset_subdir: Subdirectory under assets/decor/ for --save-blend
        gallery_title: Override gallery title (default: "{Category} Generator")
        gallery_info_fn: Custom info function for gallery cards
        cleanup_images: Also clean up bpy.data.images on each iteration
        preview_fn: Callable(objects) to set up preview scene.
                    Default: setup_preview(objects, style='product')
    """
    if output_subdir is None:
        output_subdir = category
    if gallery_title is None:
        gallery_title = category.replace('_', ' ').title() + " Generator"

    if args.output is None:
        args.output = os.path.join(project_dir, "output", output_subdir)
    output_dir = os.path.abspath(args.output)
    os.makedirs(output_dir, exist_ok=True)

    if args.seed is None:
        args.seed = random.randint(0, 99999)

    res_x, res_y = [int(x) for x in args.resolution.split('x')]

    # Determine active types
    type_choices = getattr(args, '_type_choices', None)
    mixed_key = 'mixed' if hasattr(args, 'type') and args.type == 'mixed' else None
    random_key = 'random' if hasattr(args, 'type') and args.type == 'random' else None

    rng = random.Random(args.seed)

    print("=" * 50)
    print(f"Generating {args.count} {category}")
    print(f"Type: {args.type}")
    print(f"Output: {output_dir}")
    print(f"Seed: {args.seed}")
    print("=" * 50)

    variants = []
    t_start = time.time()

    for i in range(args.count):
        clear_scene(cleanup_images=cleanup_images)

        item_seed = args.seed + i
        objects, variant = generate_fn(item_seed, args, rng)

        link_objects(objects)

        # Save .blend with asset root before preview setup
        if args.save_blend and asset_subdir:
            ad = os.path.join(project_dir, "assets", "decor", asset_subdir)
            blend_path = os.path.join(ad, f"{variant['basename']}.blend")
            save_asset_blend(objects, variant['basename'], blend_path)

        # Preview + render
        if preview_fn:
            preview_fn(objects)
        else:
            from common.preview_scene import setup_preview
            setup_preview(objects)
        render_preview(
            os.path.join(output_dir, f"{variant['basename']}.png"),
            res_x, res_y)

        variants.append(variant)

        elapsed = time.time() - t_start
        avg = elapsed / (i + 1)
        remaining = avg * (args.count - i - 1)
        print(f"  [{i+1}/{args.count}] {variant['basename']} "
              f"({avg:.1f}s/item, ETA: {remaining:.0f}s)")

    generate_gallery(gallery_title, output_dir, variants, gallery_info_fn)

    total = time.time() - t_start
    print(f"\n{'=' * 50}")
    print(f"Done! {args.count} {category} in {total:.1f}s")
    print(f"Gallery: {os.path.join(output_dir, 'index.html')}")
    print(f"{'=' * 50}")

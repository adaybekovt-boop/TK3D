from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


if __package__ in {None, ""}:
    source_root = Path(__file__).resolve().parents[1]
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))

from geoforge.errors import GeoForgeError


def _arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="geoforge-blender")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("scene_spec")
    build.add_argument("--output-dir", default=None)
    subparsers.add_parser("probe")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    import bpy

    from geoforge.api import compile_scene, load_scene_spec
    from geoforge.geometry.blender import capability_probe

    args = _arguments(list(argv if argv is not None else _after_double_dash(sys.argv)))
    try:
        if args.command == "probe":
            payload = {"status": "PASS", "capabilities": capability_probe()}
            print("GEOFORGE_RESULT=" + json.dumps(payload, sort_keys=True, separators=(",", ":")))
            return 0
        spec_path = Path(args.scene_spec).resolve()
        spec = load_scene_spec(spec_path)
        output_root = Path(args.output_dir).resolve() if args.output_dir else spec_path.parent
        result = compile_scene(spec, output_root=output_root)
        print("GEOFORGE_RESULT=" + result.compact_json())
        return 0 if result.ok else 2
    except GeoForgeError as exc:
        payload = {"status": "FAIL", "stage": "LOAD_SPEC", "error": exc.to_dict()}
        print("GEOFORGE_RESULT=" + json.dumps(payload, sort_keys=True, separators=(",", ":")))
        return 2
    except Exception as exc:
        payload = {
            "status": "FAIL",
            "stage": "UNEXPECTED",
            "error": {"code": "BUILD.UNEXPECTED", "message": f"{type(exc).__name__}: {exc}"},
        }
        print("GEOFORGE_RESULT=" + json.dumps(payload, sort_keys=True, separators=(",", ":")))
        return 3


def _after_double_dash(argv: list[str]) -> list[str]:
    if "--" not in argv:
        return []
    return argv[argv.index("--") + 1 :]


if __name__ == "__main__":
    exit_code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    raise SystemExit(exit_code)


from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .catalog import describe_generator, get_source, list_categories, search_generators, status_counts
from .errors import GeoForgeError
from .paths import repo_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="geoforge.skill")
    sub = parser.add_subparsers(dest="command", required=True)

    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=5)

    describe = sub.add_parser("describe")
    describe.add_argument("generator_id")

    source = sub.add_parser("source")
    source.add_argument("generator_id")
    source.add_argument("--text", action="store_true")

    sub.add_parser("categories")
    sub.add_parser("status")

    validate = sub.add_parser("validate")
    validate.add_argument("scene_spec")

    build = sub.add_parser("build")
    build.add_argument("scene_spec")
    build.add_argument("--output-dir", default=None)
    build.add_argument("--blender", default=None)

    args = parser.parse_args(argv)
    try:
        payload = _dispatch(args)
    except GeoForgeError as exc:
        print(json.dumps({"status": "FAIL", "error": exc.to_dict()}, ensure_ascii=True))
        return 2
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
    if isinstance(payload, dict) and payload.get("status") == "FAIL":
        return 2
    return 0


def _dispatch(args: argparse.Namespace) -> Any:
    if args.command == "search":
        return search_generators(args.query, limit=args.limit)
    if args.command == "describe":
        return describe_generator(args.generator_id)
    if args.command == "source":
        return get_source(args.generator_id, include_text=args.text)
    if args.command == "categories":
        return list_categories()
    if args.command == "status":
        return status_counts()
    if args.command == "validate":
        from .spec import load_scene_spec

        spec = load_scene_spec(args.scene_spec)
        return {"status": "PASS", "scene_id": spec.scene_id, "spec_hash": spec.spec_hash, "kinds": [item.kind for item in spec.entities]}
    if args.command == "build":
        return _build_command(Path(args.scene_spec), args.output_dir, args.blender)
    raise AssertionError(args.command)


def _build_command(spec_path: Path, output_dir: str | None, blender: str | None) -> dict[str, Any]:
    from .spec import load_scene_spec

    spec = load_scene_spec(spec_path)
    output = Path(output_dir).resolve() if output_dir else spec_path.resolve().parent
    blender_exe = _find_blender(blender)
    entry = repo_root() / "src" / "geoforge" / "blender_entry.py"
    command = [
        blender_exe or "<blender>",
        "--background",
        "--factory-startup",
        "--python",
        str(entry),
        "--",
        "build",
        str(spec_path.resolve()),
        "--output-dir",
        str(output),
    ]
    if blender_exe is None:
        return {
            "status": "FAIL",
            "stage": "BLENDER",
            "error": {"code": "BLENDER.UNAVAILABLE", "message": "Blender executable not found"},
            "command": command,
        }
    import subprocess

    completed = subprocess.run(command, check=False, text=True, capture_output=True)
    result_line = ""
    for line in completed.stdout.splitlines():
        if line.startswith("GEOFORGE_RESULT="):
            result_line = line[len("GEOFORGE_RESULT=") :]
    parsed: dict[str, Any]
    if result_line:
        parsed = json.loads(result_line)
    else:
        parsed = {
            "status": "FAIL" if completed.returncode else "PASS",
            "stdout": completed.stdout[-2000:],
            "stderr": completed.stderr[-2000:],
        }
    parsed["command"] = command
    parsed["returncode"] = completed.returncode
    return parsed


def _find_blender(explicit: str | None) -> str | None:
    if explicit:
        return explicit
    from os import environ

    env = environ.get("GEOFORGE_BLENDER")
    if env:
        return env
    default = Path(r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe")
    if default.is_file():
        return str(default)
    return None


if __name__ == "__main__":
    raise SystemExit(main())

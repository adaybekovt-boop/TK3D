#!/usr/bin/env python3
"""Wrapper around `python -m geoforge.skill`."""

from __future__ import annotations

import sys
from pathlib import Path


def _engine_src() -> Path | None:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "src"
        if (candidate / "geoforge" / "__init__.py").is_file():
            return candidate
    return None


SOURCE = _engine_src()
if SOURCE is not None and str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

try:
    from geoforge.skill import main
except ImportError:
    sys.stderr.write(
        "GeoForge engine not found. Download https://github.com/adaybekovt-boop/TK3D "
        "and run this skill from that checkout, or add its src/ to PYTHONPATH.\n"
    )
    raise SystemExit(2)

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Project-local wrapper around `python -m geoforge.skill`."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "src"
if str(SOURCE) not in sys.path:
    sys.path.insert(0, str(SOURCE))

from geoforge.skill import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

# Catalogs

`generators.json` is the canonical TK3D generator index. `runtime-generators.json`
is the stable 35-entry pre-harvest runtime/curated input; `sources.json` and
`integrity.json` are generated normalized indexes. `raw/` preserves archive
metadata without treating it as instructions.

Regenerate with `scripts/consolidate_libraries.py`; do not hand-edit the packaged
mirror under `src/geoforge/catalog/`.

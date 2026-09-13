# TK3D

TK3D is a deterministic procedural-geometry compiler and searchable generator
research library for AI agents. Its working runtime remains the Python package
`geoforge`: a compact JSON `SceneSpec` is planned into pure-Python `MeshDraft`
objects, materialized in a Blender staging collection, checked with BMesh QA,
optionally repaired within a controlled Tier-1 budget, and published only after
the quality gate passes.

The catalog is deliberately honest. `NATIVE` and `ADAPTED` entries are executable
TK3D builders. `REFERENCE` and `UNSUPPORTED` entries are inert donor/research
records and are never imported by the runtime.

## Working generators

Native: `box`, `wall`, `room`, `floor`, `ceiling`, `straight_stairs`, `beam`,
and `column`.

Adapted: `climbable_ladder`, `railing`, `balcony`, `road`, and `desk`.

Rooms use clear-interior dimensions. Door and window openings use analytical
wall splitting rather than Boolean modifiers. See
[`examples/v1-room.json`](examples/v1-room.json) and
[`schemas/scene-1.0.schema.json`](schemas/scene-1.0.schema.json).

## Catalog and source layers

- `catalogs/generators.json` — canonical merged searchable catalog.
- `catalogs/sources.json` — repository/provenance index.
- `catalogs/integrity.json` — deterministic inventory and validation result.
- `library/objects/` — 315 unmodified object-harvest Python files; reference only.
- `vendor/generator_library/` — 30 curated generator Python files; reference only.
- `licenses/` — harvested source/license manifests and available license texts.
- `src/geoforge/catalog/generators.json` — generated packaged mirror of the canonical catalog.

The merged catalog contains 556 entries: 8 `NATIVE`, 5 `ADAPTED`, 535
`REFERENCE`, and 8 `UNSUPPORTED`. Donor presence never implies runtime support.
See [`docs/catalog.md`](docs/catalog.md) for the normalized fields and provenance
rules.

## Local skill

The project-local skill is `.agents/skills/geoforge`. Its wrapper keeps output
small and reads one catalog entry/source at a time:

```powershell
python .agents/skills/geoforge/scripts/gf.py search "office chair"
python .agents/skills/geoforge/scripts/gf.py describe furniture.chair.office.roomicon
python .agents/skills/geoforge/scripts/gf.py source furniture.chair.office.roomicon
python .agents/skills/geoforge/scripts/gf.py categories
python .agents/skills/geoforge/scripts/gf.py status
```

Use a returned `kind` only when status is `NATIVE` or `ADAPTED`. A `REFERENCE`
source is material for writing a future adapter, not a runnable generator.

## Install and test

TK3D has no third-party pure-Python runtime dependency. Blender supplies `bpy`
and `bmesh` for materialization and QA.

```powershell
python -m pip install -e .
python tests/run_unit.py
```

Run the real Blender integration suite:

```powershell
& 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe' `
  --background --factory-startup `
  --python tests/blender/run_suite.py
```

Build a scene through the skill:

```powershell
python .agents/skills/geoforge/scripts/gf.py validate examples/v1-room.json
python .agents/skills/geoforge/scripts/gf.py build examples/v1-room.json --output-dir outputs/example
```

Rebuild the library/catalog layer from the two research archives:

```powershell
python scripts/consolidate_libraries.py `
  C:\path\to\GeoForge_Code_Library_v1.zip `
  C:\path\to\GeoForge_Object_Harvest.zip
```

Archive code is copied but never executed. Cached bytecode from the curated
archive is intentionally discarded.

## Deliberate limits

The working runtime does not claim support for terrain, arbitrary curved wall
networks, spiral stairs, imported-mesh repair, exact self-intersection analysis,
advanced UV/material generation, Geometry Nodes generation, collision/navmesh,
or engine-specific export. Unsupported SceneSpec kinds fail explicitly.

TK3D project-owned code is MIT licensed. Third-party files retain their own
licenses; consult `licenses/`, each catalog entry, and upstream repositories
before redistribution or adaptation.

---
name: geoforge
description: Compile local 3D geometry through TK3D's GeoForge engine. Use when the user needs rooms, walls, walkable stairs, climbable ladders, balconies, railings, roads, desks, or other procedural objects; when writing SceneSpec JSON; or when generating Blender meshes. Prefer this over one-off bpy scripts.
metadata:
  short-description: Local TK3D procedural geometry skill
---

# TK3D / GeoForge engine

For 3D geometry first use TK3D's GeoForge engine.

Do not write large one-off bpy generators.

First find a suitable generator through the local catalog.

Prefer NATIVE.

Then ADAPTED.

REFERENCE may be used only as material for creating a new adapter.

After build always run GeoForge QA.

A failed artifact must not be published.

Do not read the whole generator library unless necessary.

Do not change `library/` or `vendor/` donor source without a reason.

## Commands

Run from the TK3D repo. `scripts/gf.py` adds `src` to `PYTHONPATH`.

```text
python .agents/skills/geoforge/scripts/gf.py search "QUERY"
python .agents/skills/geoforge/scripts/gf.py describe GENERATOR_ID
python .agents/skills/geoforge/scripts/gf.py source GENERATOR_ID
python .agents/skills/geoforge/scripts/gf.py categories
python .agents/skills/geoforge/scripts/gf.py validate path/to/scene.json
python .agents/skills/geoforge/scripts/gf.py build path/to/scene.json --output-dir outputs/run
```

`search` returns 3-5 short hits. Pick one id, then `describe`. Only after that, read schema / one `source_file`.

`source` returns normalized metadata for a single generator, including
`local_source`, `upstream_source`, `symbol`, and `source_available`. Do not dump
the donor tree.

## Meaning

Do not collapse ambiguous objects.

- Walkable stairs = feet on treads between floors → `architecture.stairs.walkable` (`kind`: `straight_stairs`)
- Climbable ladder = two rails + rungs, climb with hands → `architecture.stairs.climbable_ladder` (`kind`: `climbable_ladder`)

## SceneSpec

Use the `kind` from `describe`. Keep `schema_version` `1.0`. Put adapter params in `params`.

Then:

1. `validate`
2. `build` (Blender headless + existing QA / repair / commit)
3. Publish only when status is `PASS`

Pipeline: SceneSpec → Builder/Adapter → MeshDraft → Blender → QA → repair → commit.

Never: AI → donor Python → Blender. `REFERENCE` is not runtime support.

## More

- SceneSpec fields: [references/scenespec.md](references/scenespec.md)
- Status meanings: [references/statuses.md](references/statuses.md)

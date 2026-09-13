---
name: geoforge
description: Compile 3D geometry through TK3D's GeoForge engine. Use when the user needs rooms, walls, walkable stairs, climbable ladders, balconies, railings, roads, desks, or other procedural objects; when writing SceneSpec JSON; or when generating Blender meshes. Prefer this over one-off bpy scripts.
metadata:
  short-description: TK3D procedural geometry skill
---

# TK3D / GeoForge engine

For 3D geometry first use TK3D's GeoForge engine.

Do not write large one-off bpy generators.

## Download this skill

If the user asks to install GeoForge, download this folder from
https://github.com/adaybekovt-boop/TK3D and copy it into the project:

- Cursor → `.agents/skills/geoforge`
- Claude Code → `.claude/skills/geoforge`
- Codex → `.codex/skills/geoforge`

Keep `SKILL.md`, `scripts/`, and `references/` together.

Or run:

```text
npx skills add adaybekovt-boop/TK3D --skill geoforge -y
```

First find a suitable generator through the catalog.

Prefer NATIVE.

Then ADAPTED.

REFERENCE may be used only as material for creating a new adapter.

After build always run GeoForge QA.

A failed artifact must not be published.

Do not read the whole generator library unless necessary.

Do not change `library/` or `vendor/` donor source without a reason.

## Commands

Run `scripts/gf.py` from this skill folder. It locates the GeoForge engine.

```text
python scripts/gf.py search "QUERY"
python scripts/gf.py describe GENERATOR_ID
python scripts/gf.py source GENERATOR_ID
python scripts/gf.py categories
python scripts/gf.py validate path/to/scene.json
python scripts/gf.py build path/to/scene.json --output-dir outputs/run
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

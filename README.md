# TK3D

**Ask your agent for a room. Get a real 3D mesh back.**

GeoForge is a Cursor skill that compiles procedural geometry — rooms, walls,
walkable stairs, climbable ladders, balconies, railings, roads, desks.

You describe the space. The agent builds it. Quality checks run automatically.
If the mesh fails, it does not ship.

## Agent setup

Paste this into **Cursor Agent**:

```
Download the GeoForge skill from https://github.com/adaybekovt-boop/TK3D and install it in this project.
```

The agent downloads the skill from this repo and copies it into the project.

| Agent | Source | Destination |
| --- | --- | --- |
| Cursor | `.agents/skills/geoforge` | `.agents/skills/geoforge` |
| Claude Code | `.agents/skills/geoforge` | `.claude/skills/geoforge` |
| Codex | `.agents/skills/geoforge` | `.codex/skills/geoforge` |

The copied folder must contain `SKILL.md`, `scripts/`, and `references/`.

The agent can download it in one command:

```
npx skills add adaybekovt-boop/TK3D --skill geoforge -y
```

That is the whole setup.

## Then just ask

```
Build a 12×20 m room with a south door, an east window, and walkable stairs.
```

Or type `/geoforge`.

| You ask for | You get |
| --- | --- |
| A room | Walls, floor, ceiling, door and window openings |
| Stairs | Walkable treads between floors |
| A ladder | Two rails and rungs you climb with your hands |
| A balcony, railing, road, or desk | Compiled geometry, not a sketch |

MIT. Third-party donor files keep their own licenses.

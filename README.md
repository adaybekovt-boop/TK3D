# TK3D

**Ask your agent for a room. Get a real 3D mesh back.**

GeoForge is a Cursor skill that compiles procedural geometry — rooms, walls,
walkable stairs, climbable ladders, balconies, railings, roads, desks.

You describe the space. The agent builds it. Quality checks run automatically.
If the mesh fails, it does not ship.

No one-off Blender scripts. No guessing mesh code.

## Install

Open **Cursor Agent** and paste this:

```
Install the GeoForge skill from https://github.com/adaybekovt-boop/TK3D
```

That is the whole setup. The agent installs the skill. You do not run a local
install, clone extra folders, or touch Python yourself.

Works the same in Claude Code, Codex, and any other agent that can install a
skill from GitHub.

## Then just ask

```
Build a 12×20 m room with a south door, an east window, and walkable stairs.
```

Or type `/geoforge` after it is installed.

| You ask for | You get |
| --- | --- |
| A room | Walls, floor, ceiling, door and window openings |
| Stairs | Walkable treads between floors |
| A ladder | Two rails and rungs you climb with your hands |
| A balcony, railing, road, or desk | Compiled geometry, not a sketch |

MIT. Third-party donor files keep their own licenses.

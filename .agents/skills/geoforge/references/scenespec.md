# SceneSpec

Required top-level fields: `schema_version` (`1.0`), `scene_id`, `seed`, `entities`.

Each entity: `id`, `kind`, optional `transform` (`position`, `yaw_deg`), `params`.

Use `kind` from `python -m geoforge.skill describe <id>`, not the generator id.

V1 native kinds: `box`, `wall`, `room`, `floor`, `ceiling`, `straight_stairs`, `beam`, `column`.

Adapted kinds: `climbable_ladder`, `railing`, `balcony`, `road`, `desk`.

Units default to metres. Quality profile is `production` only.

Failed quality gates write reports but do not publish objects.

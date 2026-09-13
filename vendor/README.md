# vendor/

Third-party and donor source code. Nothing in this directory is imported at
runtime by `src/geoforge/`; it is a **reference library** that the TK3D
generator catalog indexes and that adapters were written *from*.

## generator_library/

`GeoForge_Code_Library_v1` unpacked verbatim (only `__pycache__` removed).
File hashes are recorded in `generator_library/INTEGRITY.json` and verified by
`tests/unit/test_catalog.py`.

| File | Purpose |
| --- | --- |
| `CATALOG.json` | Semantic groups: id, meaning, tags, variants, files, source |
| `FILE_INDEX.json` | Per-file origin (project, repo, commit, license, sha256) |
| `SOURCES.json` | Upstream repositories and exact commits |
| `INTEGRITY.json` | SHA-256 of every Python file |
| `_licenses/` | Original license texts (Building Tools MIT, Infinigen BSD-3, ProcFunc BSD-3) |
| `*/metadata.json` | Per-group copy of the catalog entry |

Rules:

- Do not edit donor files. Adapt them into `src/geoforge/adapters/` and keep a
  pointer (`vendor_group`) in `catalogs/runtime-generators.json`.
- Do not delete licenses or origin metadata.
- Origin metadata (project / repo / commit / license) remains authoritative
  here and is normalized into the generated TK3D catalog.

## provenance/

`LICENSE_POLICY.md` and `SOURCE_MANIFEST.json` from
`GeoForge_OSS_Source_Bootstrap` — the harvesting policy and upstream manifest.

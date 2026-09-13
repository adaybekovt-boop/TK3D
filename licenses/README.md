# Licenses and provenance

The repository-root `LICENSE` applies only to TK3D project-owned code.
Third-party source under `library/` and `vendor/` retains its upstream license.

- `OBJECT_HARVEST_SOURCES.md` is the source/license report supplied with the object harvest.
- `code-library/` contains the license texts supplied with the curated archive.
- `pipes-generator-LICENSE` is the standalone license shipped with that donor source.
- Per-entry SPDX-style identifiers, repository URLs, revisions, commits, paths,
  and content hashes are in `catalogs/generators.json`.

Some harvested repositories did not supply a verifiable commit SHA. TK3D keeps
their original branch/harvest label as `source_revision`, leaves
`pinned_commit` null, and reports the exact count in `catalogs/integrity.json`
rather than inventing provenance.

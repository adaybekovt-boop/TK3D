# Generator statuses

- **NATIVE** — implemented inside TK3D's GeoForge runtime and QA-tested. Prefer this.
- **ADAPTED** — donor idea connected through a working adapter into the TK3D pipeline.
- **REFERENCE** — source metadata and sometimes local source exists in `library/objects/` or `vendor/generator_library/`. A Python file is not a working generator. Use only when writing a new adapter.
- **UNSUPPORTED** — helper or incomplete; do not treat as a builder.

A donor file never makes a generator NATIVE or ADAPTED by itself.

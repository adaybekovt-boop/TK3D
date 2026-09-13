# GeoForge Object Harvest

Catalog of reusable procedural **object** generators for later GeoForge adaptation.

Lookup style the catalog is built for:

```
tree.oak
tree.pine
building.house
building.warehouse
furniture.sofa
bathroom.toilet
industrial.pipe
street.lamp
prop.bottle
```

## Files

- `CATALOG.json` — machine-readable object-type candidates
- `SOURCES.md` — repositories, commits, licenses, value notes
- `REJECTED.json` — paid / primitive / unknown-license / documented gaps
- `candidates/` — unmodified upstream `.py` files where the license allows a copy
- `catalog_parts/` — per-lane harvest fragments used to build the catalog

## Policy

- One candidate = one semantic object type, not a helper like `normalize_vector()`.
- Variants from one factory are split only when GeoForge should choose between them
  (dining chair vs office chair, oak vs pine).
- Clear licenses only in the usable catalog (MIT / BSD / Apache / GPL / LGPL / Unlicense).
- Sources are not modified. Nothing is integrated into GeoForge.

## Honesty

These files are **not** one-click `python foo.py` model makers.

- Most need Blender (`bpy`) or CadQuery / FreeCAD.
- Infinigen factories need the Infinigen runtime + node transpiler (`reuse: hard`).
- Roomicon, tree-gen presets, Extra Objects teapot/rocks/pipes/beams, BoltFactory,
  and cqterrain parts are the best adapter targets (`easy` / `medium`).

Open-source does **not** contain 1000 isolated high-quality object-type generators.
Padding primitives or seed variants would inflate the number without helping GeoForge.

## Zip

`/home/workdir/artifacts/GeoForge_Object_Harvest.zip`

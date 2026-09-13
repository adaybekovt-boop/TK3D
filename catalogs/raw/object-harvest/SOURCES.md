# GeoForge Object Harvest — Sources

Research pack of reusable procedural **object** generators for later GeoForge adapters.
Not integrated into GeoForge. Copied sources are unmodified.

## Headline stats

- total candidates: 521
- unique repositories: 39
- candidate source files on disk: 315 (empty: 0)
- rejected / gaps: 63
- reuse: {'medium': 261, 'hard': 80, 'easy': 180}
- licenses: {'BSD-3-Clause': 216, 'GPL-3.0': 162, 'Apache-2.0': 44, 'GPL-2.0-or-later': 32, 'LGPL-2.1-or-later': 22, 'MIT': 21, 'GPL-3.0-or-later': 20, 'GPL-2.0': 3, 'Unlicense': 1}
- runtimes: {'Blender': 451, 'pure-python': 42, 'other': 22, 'CadQuery': 2, 'standalone': 2, 'Unity': 1, 'Godot': 1}

## Counts by top-level category

- buildings: 105
- props: 105
- nature: 92
- furniture: 81
- household: 74
- industrial: 33
- architecture: 14
- street: 10
- interior: 7

## Counts by category

- nature/trees: 38
- props/tableware: 35
- buildings/openings: 26
- nature/plants: 26
- furniture/cabinets: 20
- household/appliances: 19
- props/kitchenware: 16
- furniture/tables: 13
- household/lamps: 12
- buildings/floors: 11
- furniture/chairs: 11
- household/bathroom: 10
- nature/rocks: 10
- furniture/shelves: 9
- architecture/windows: 8
- buildings/roofs: 8
- props/books: 8
- props/food: 8
- buildings/structure: 7
- furniture/beds: 7
- household/textiles: 7
- nature/creatures: 7
- nature/underwater: 7
- buildings/stairs: 6
- furniture/kitchen: 6
- furniture/wardrobes: 6
- household/decor: 6
- industrial/pipes: 6
- props/decor: 6
- props/toys: 6
- buildings/apartments: 5
- buildings/circulation: 5
- buildings/industrial: 5
- household/mirrors: 5
- industrial/fasteners: 5
- interior/lighting: 5
- props/textiles: 5
- buildings/shops: 4
- buildings/walls: 4
- household/clocks: 4
- household/kitchen: 4
- industrial/machinery: 4
- nature/cactus: 4
- props/candles: 4
- props/hardware: 4
- props/plants: 4
- architecture/doors: 3
- buildings/houses: 3
- buildings/rooms: 3
- furniture/sofas: 3
- furniture/storage: 3
- household/lighting: 3
- industrial/doors: 3
- props/containers: 3
- architecture/walls: 2
- buildings/facades: 2
- buildings/plans: 2
- buildings/ruins: 2
- buildings/towers: 2
- furniture/rugs: 2
- household/clothing: 2
- household/electronics: 2
- industrial/hvac: 2
- industrial/mechanical: 2
- interior/window-treatments: 2
- props/clothes: 2
- street/barriers: 2
- street/fences: 2
- architecture/columns: 1
- buildings/concrete: 1
- buildings/elements: 1
- buildings/exterior: 1
- buildings/finishes: 1
- buildings/hardware: 1
- buildings/mixed: 1
- buildings/modular: 1
- buildings/offices: 1
- buildings/panels: 1
- buildings/trim: 1
- furniture/desks: 1
- industrial/access: 1
- industrial/antenna: 1
- industrial/bearings: 1
- industrial/cables: 1
- industrial/electrical: 1
- industrial/equipment: 1
- industrial/platforms: 1
- industrial/props: 1
- industrial/rebar: 1
- industrial/steel: 1
- industrial/storage: 1
- props/industrial: 1
- props/kitchen: 1
- props/storage: 1
- props/vehicles: 1
- street/bridges: 1
- street/furniture: 1
- street/lighting: 1
- street/roads: 1
- street/signs: 1
- street/site: 1

## Top projects by useful generators

- Infinigen: 119
- Roomicon: 85
- Infinigen / Infinigen Indoors: 77
- cqterrain: 32
- FreeCAD BIM/Arch: 22
- Infinite-Mobility: 20
- tree-gen: 20
- Archimesh: 17
- Archipack: 16
- bene-proggen-maps: 15
- Library_Home_Builder: 13
- Home Builder: 11
- Building Tools: 10
- cq_warehouse: 9
- Add Mesh Extra Objects: 7
- JARCH Vis: 6
- blender-building-generator: 5
- procedural_buildings: 4
- blender_furniture_builder: 3
- ND addon: 3
- MTree / modular_tree: 3
- BoltFactory: 2
- CadQuery examples: 2
- furniture_builder: 1
- pipes-generator-blender: 1
- GrowthNodes: 1
- IvyAnywhere: 1
- Blender official addons: 1
- ivygen: 1
- ProceduralIvy: 1
- Rock-Generator: 1
- ProceduralRocks: 1
- blender-low-poly-rock: 1
- Blender-Rock-Generator: 1
- RocksNPillars: 1
- proc-rock: 1
- ArborGen: 1
- improved-sapling-tree-generator: 1
- BookGen: 1
- Blender-Bottle-Builder: 1
- blender-addons extra_objects: 1
- CadQuery: 1
- SpaceshipGenerator: 1

## License verification this session

- Beneking102/bene-proggen-maps → GPL-3.0-or-later (README LICENSE section)
- outerreaches/blender-building-generator → GPL-3.0-or-later
- aaronjolson/Blender-Bottle-Builder → Unlicense
- mikhailefimov/blender_furniture_builder → GPL-2.0-or-later
- princeton-vl/infinigen → BSD-3-Clause @ 3f58bb8
- friggog/tree-gen → GPL-3.0 @ 01e8721
- ranjian0/building_tools → MIT @ 0216534
- medicationforall/cqterrain → Apache-2.0 @ 3848928
- gumyr/cq_warehouse → Apache-2.0
- neurospiritus/roomicon → GPL-3.0

## Honest ceiling

A 1000+ catalog of *distinct object types* is not available in public open source without padding helpers, primitives, or seed variants. Infinigen + Roomicon + Building Tools + tree-gen + FreeCAD BIM + cqterrain + Archimesh/Archipack cover most of the reusable typed factories.

Known missing typed factories (see REJECTED.json gaps):
tank, valve, HVAC/boiler/pump, electrical cabinet, cable tray,
scaffolding, traffic light, manhole, utility pole, bus stop,
barrel, crate/dumpster, locker, hangar/barn/shed-as-type, cave/cliff/roots.

3DCodeBench (gaoypeng/3dcodebench, BSD-3 factory scripts) is a
standalone rewrite of Infinigen factories — same object types, easier
runtime. Not added as 212 extra IDs to avoid double-counting.

## Team source notes

# Benjamin sources — nature + Infinigen factories + tree species

## princeton-vl/infinigen
- License: BSD-3-Clause
- Commit pinned: `3f58bb886bb1bda681d41240344fe3126ac0e9bd` (main at harvest time)
- Value: highest-density open object factory library. Nature: trees (pine/palm/baobab/bamboo/shrub/random + flowering), deformed trees (fallen/hollow/rotten/stump), cactus (columnar/globular/prickly-pear/kalidium), rocks (blender/boulder/glowing/pile), grassland (dandelion/flower/flowerplant/grass tuft), small plants (fern/snake/spider/succulent), tropic (coconut/palm/banana), monocot (agave/banana/grasses/kelp/pinecone/tussock/veratrum), mushroom, corals (elkhorn/fan/star/tree/tube/diff-growth/RD), fruits (8 species), creatures (beetle/bird/carnivore/herbivore/crustacean/fish/dragonfly).
- Also extracted (overlap risk with Lucas/Harper): tableware 17, bathroom 4, appliances 6, lamps 3, stairs 6, pallet, warehouse rack, pillar, clothes.
- Reuse: hard for tree GN pipeline; medium for isolated factory files; easy for pallet/plate-class props.
- Do not copy entire repo into candidates/; pin files + commit.

## friggog/tree-gen
- License: GPL-3.0
- Commit: `01e872182a0f955349e51bb1a68ed4dfd665f81c`
- Value: 19 Weber-Penn species presets (acer, apple, balsam fir, bamboo, black oak, black tupelo, cambridge oak, douglas fir, european larch, fan palm, hill cherry, lombardy poplar, palm, quaking aspen, sassafras, silver birch, small pine, sphere tree, weeping willow) + 10 leaf shapes + 3 blossom shapes.
- Engine: `parametric/gen.py`. Preset files are tiny and easy; engine is medium.

## GoodPie/modular_tree (MTree fork)
- Addon GPL-3.0, core lib MIT. Presets: Oak, Pine, Willow. Node-based, Blender 4.3+. Hard reuse.

## Other nature
- UPBGE/blender-addons `add_curve_ivygen.py` GPL-2.0-or-later — official IvyGen, easy.
- LuncyBloont/IvyAnywhere GPL-3.0 — easy.
- mattiascibien/ivygen GPL-2.0 — standalone C++/Qt, hard.
- Team-Crescendo-Games/ProceduralIvy MIT — Unity, hard.
- lupin4/Blender-Rock-Generator MIT — easy single script.
- versluis/Rock-Generator GPL-2.0 — classic add_mesh_rocks.
- CommanderFoo/blender-low-poly-rock MIT — easy.
- acfaruk/proc-rock GPL-3.0 — geological C++ pipeline, hard.
- Fyrecean/ProceduralRocks MIT — Godot.
- lorentzo/RocksNPillars MIT — rocks + pillars.
- nifets/ArborGen GPL-3.0 — growing oak.
- abpy/improved-sapling-tree-generator GPL-2.0 — Sapling 4.
- smaooo/L-System — 8 L-system grammars, license unverified.
- TheBeautifulOrc/TBO-Tree-Gen, thelazyone/lazy-tree, LuFlo/low-poly-tree-generator, jacobcjohnston/Easy-Tree — license review-needed.

## Not used
- The Grove, Botaniq, Graswald, Superhive vegetation packs — paid.
- Static Megascans / Poly Haven trees — not generators.


# Harper sources — buildings / industrial / street

## Used
- Building Tools MIT https://github.com/ranjian0/building_tools @0216534645b15b3f8aac0bd1d7e6674e2972b9b3
- FreeCAD BIM/Arch LGPL candidates/freecad_bim
- Home Builder GPL candidates/home_builder
- Archimesh GPL candidates/archimesh
- Archipack 2.79 GPL https://github.com/s-leger/archipack
- JARCH Vis GPL https://github.com/BlendingJake/JARCH-Vis
- cqterrain Apache-2.0 https://github.com/medicationforall/cqterrain @3848928597b2ba9ca5b61e11279467c93ad66889
- Infinigen BSD-3 https://github.com/princeton-vl/infinigen @3f58bb886bb1bda681d41240344fe3126ac0e9bd
- Extra Objects GPL: only Wallfactory, beam builder, pipe joints
- pipes-generator-blender MIT candidates/pipes_generator
- ND addon GPL-3 https://github.com/hugemenace/nd
- bene-proggen-maps review-needed https://github.com/Beneking102/bene-proggen-maps
- blender-building-generator review-needed https://github.com/outerreaches/blender-building-generator
- procedural_buildings MIT https://github.com/wsparcie/procedural_buildings
- furniture_builder local review-needed

## Notes
Archipack 2.x paid extras excluded. Extra Objects primitives excluded.


# Lucas sources — furniture / household / props

## Usable

| Project | Repo | License | Commit | Value |
|---|---|---|---|---|
| Infinigen / Indoors | https://github.com/princeton-vl/infinigen | BSD-3-Clause | 3f58bb886bb1bda681d41240344fe3126ac0e9bd | Highest-quality indoor factories (chairs, sofa, bed, tables, cabinets, appliances, bathroom, lamps, tableware). Adapter cost: medium (AssetFactory + nodes). |
| Roomicon | https://github.com/neurospiritus/roomicon | GPL-3.0 | 2dcd3d1 (v1.2.0) | Isolated per-type Python generators. Best easy-reuse furniture set. 8 tables, 6 chairs, 6 beds/sofas, 5 wardrobes + decor. |
| Archimesh | blender-addons/archimesh | GPL-2.0-or-later | bundled | Kitchen cabinets (floor/wall), shelves, books, lamps, curtains, blinds. |
| Library_Home_Builder | https://github.com/CreativeDesigner3D/Library_Home_Builder | GPL-3.0 | — | Parametric kitchen/bath/closet cabinets + range/fridge/dishwasher + doors/windows. Hard reuse (PyClone runtime). |
| blender_furniture_builder | https://github.com/mikhailefimov/blender_furniture_builder | unspecified | — | Self-contained Cabinet/Section library with BOM. Review license. |
| Infinite-Mobility | https://github.com/InternRobotics/Infinite-Mobility | BSD-3-Clause (Infinigen fork) | — | 20 articulated URDF factories. Sibling of Infinigen objects, not new geometry. |
| BookGen | https://github.com/oweissbarth/bookGen | GPL-3.0 | 8c90891 | Best dedicated book filler. |
| Extra Objects | blender-addons/add_mesh_extra_objects | GPL-2.0-or-later | — | Teapot, gems, pipe joints, beams, wall factory. Reject gears/torus/menger. |
| SpaceshipGenerator | https://github.com/a1studmuffin/SpaceshipGenerator | MIT | — | Vehicle prop. |
| pipes-generator-blender | https://github.com/bruchansky/pipes-generator-blender | MIT | — | Industrial pipe runs. |
| PalletDataGenerator | https://github.com/boubakriibrahim/PalletDataGenerator | review | — | Warehouse pallet scenes. |
| storage_grid | https://github.com/Roger-random/storage_grid | review | — | CadQuery dovetail trays. |
| cad-skill gridfinity | https://github.com/flowful-ai/cad-skill | review | — | Gridfinity bins. |

## Notes
- Roomicon types are split into semantic candidates (dining vs office chair, etc.) because GeoForge lookup is `furniture.chair.office` not `generate_chair()`.
- Infinite-Mobility kept as `*.mobility` IDs so merge does not collide with Infinigen geometry factories.
- Do not catalog Roomicon helpers.py / generate.py wrappers as objects.


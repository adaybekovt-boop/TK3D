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

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

GeoForge Code Library v1

Внутри: 30 настоящих Python-файлов с procedural 3D кодом.
Они разложены по смыслу: stairs, ladder, doors, windows, floors, floorplans,
balconies, railings, roads, chairs, desks, kitchen, TV/monitor, aquarium и geometry helpers.

Главный файл для ИИ: CATALOG.json
Он объясняет простыми тегами, ЧТО делает каждый генератор и когда его выбирать.

Пример:
- нужна обычная лестница между этажами -> architecture.stairs.walkable
- нужна лестница с перекладинами, по которой карабкаются -> architecture.stairs.climbable_ladder
- нужен офисный стул -> furniture.chair.office

Важно:
Это donor-code library для GeoForge, а не 30 standalone-скриптов.
Часть файлов зависит от Building Tools / Infinigen / ProcFunc.
Правильный следующий шаг — адаптировать нужные генераторы под уже готовый GeoForge V1 registry,
а не запускать каждый файл отдельно.

Лицензии оригинальных проектов лежат в _licenses/.

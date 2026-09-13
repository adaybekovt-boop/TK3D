# TK3D

**A procedural 3D skill for AI coding agents.**

TK3D gives frontier AI models a reusable 3D generation layer for Blender instead of forcing them to invent large one-off Python scripts for every object and scene.

It combines a searchable procedural object library, reusable generators, deterministic geometry generation, automatic validation, repair and optimization-oriented tooling.

The goal is simple:

> **Make AI-generated 3D significantly more capable, consistent and reliable.**

---

## Install for your AI agent

```bash
npx skills add https://github.com/adaybekovt-boop/TK3D --skill tk3d
```

After installation, ask your coding agent to use **TK3D** when creating or modifying 3D scenes.

---

## Why TK3D

Modern AI coding models can control Blender surprisingly well.

The problem is that without a reusable 3D system they repeatedly have to:

- invent geometry from scratch;
- write large temporary Blender scripts;
- solve the same objects again and again;
- guess topology and dimensions;
- recover from broken meshes;
- waste context on implementation details that already have known solutions.

TK3D changes that workflow.

Instead of rebuilding everything from zero, the agent can search for an existing procedural capability, configure it, combine it with other generators and send the result through the same validation pipeline.

```text
Intent
  ↓
TK3D
  ↓
Search capabilities
  ↓
Select / compose generators
  ↓
Generate geometry
  ↓
Blender
  ↓
QA / repair
  ↓
Final scene
```

---

## Procedural Object Library

TK3D contains a large searchable catalog of reusable procedural 3D capabilities collected from native implementations and open-source procedural projects.

Current core catalog:

| Status | Count |
| --- | ---: |
| NATIVE | 8 |
| ADAPTED | 5 |
| REFERENCE | 535 |
| UNSUPPORTED | 8 |
| **Total** | **556** |

The source library currently contains:

- **345 procedural Python files**
- **39 upstream repositories**
- architecture
- buildings
- furniture
- industrial objects
- household objects
- nature
- props
- street infrastructure
- general geometry tools

The library includes generators and references for objects such as:

- houses
- warehouses
- stairs
- ladders
- roads
- balconies
- railings
- trees
- rocks
- chairs
- sofas
- desks
- cabinets
- appliances
- pipes
- architectural systems
- industrial equipment
- hundreds of other reusable object types

Catalog presence does not automatically mean runtime support.

TK3D clearly separates working generators from research/reference implementations.

---

## Semantic Search

TK3D searches by **meaning**, not just filenames.

For example:

```text
stairs between floors
```

should prefer a staircase designed for walking.

While:

```text
ladder to climb using hands
```

should prefer a ladder with rails and rungs.

This distinction applies throughout the library.

The agent searches compact metadata first and loads implementation details only when required.

That allows the library to grow without dumping thousands of files into the model context.

---

## Generator Status

### NATIVE

Generators implemented directly for TK3D and validated through its geometry pipeline.

Examples:

- rooms
- walls
- floors
- ceilings
- beams
- columns
- walkable stairs

### ADAPTED

External procedural concepts converted into TK3D-compatible generators.

Examples:

- climbable ladders
- balconies
- railings
- roads
- desks

### REFERENCE

Useful procedural implementations indexed for discovery and future adaptation.

Reference code is not treated as executable TK3D support until it has been adapted and validated.

---

## Geometry Pipeline

Executable TK3D generators use a deterministic generation pipeline:

```text
Scene specification
→ Generator
→ Geometry representation
→ Blender staging
→ Geometry QA
→ Controlled repair
→ Commit
```

Generated geometry is validated before publication.

The system can detect problems such as:

- degenerate geometry;
- duplicate vertices or faces;
- loose geometry;
- non-manifold topology;
- invalid transforms;
- invalid numerical values;
- malformed geometry;
- geometry below configured quality limits.

If the quality gate fails, the broken result is not published.

---

## Designed for AI Agents

TK3D is not intended to be a traditional asset browser.

It is structured specifically for modern coding and reasoning agents.

Instead of thinking in thousands of low-level mesh operations, an agent can reason at a higher level:

```text
building.shell
building.stairs
industrial.pipes
industrial.ducts
furniture.desks
nature.tree
street.lamp
```

TK3D then provides reusable implementations and references behind those concepts.

This allows the model to spend more of its reasoning budget on the scene itself instead of repeatedly reinventing basic 3D geometry.

---

## Growing Library

TK3D is designed to continuously expand.

New capabilities can be added as:

```text
REFERENCE
→ ADAPTED
→ production-ready capability
```

The project is actively expanding in three major areas:

- procedural object generators;
- materials and PBR textures;
- automatic scene optimization.

The long-term goal is to provide AI agents with a reusable **3D standard library**.

---

## Quality Philosophy

TK3D does not attempt to replace the reasoning ability of the model.

It gives the model better tools.

The AI still decides:

- what should exist in the scene;
- which generators should be used;
- how objects should be combined;
- what dimensions and styles make sense;
- when a new procedural capability is needed.

TK3D handles reusable geometry knowledge, generation infrastructure and validation.

---

## License

TK3D-owned source code is released under the MIT License.

Third-party procedural source files and references retain their original licenses.

License and provenance metadata are stored alongside catalog entries and source records.

---

# Русский

## TK3D

**Procedural 3D skill для AI-агентов.**

TK3D даёт современным AI-моделям готовый слой для процедурной работы с 3D в Blender, вместо того чтобы заставлять модель каждый раз с нуля придумывать огромные одноразовые Python-скрипты.

TK3D объединяет:

- библиотеку процедурных объектов;
- поиск генераторов по смыслу;
- переиспользуемую геометрию;
- автоматическую проверку;
- контролируемое исправление ошибок;
- основу для оптимизации больших сцен.

Главная цель:

> **Сделать 3D, создаваемое AI-моделями, значительно качественнее, стабильнее и предсказуемее.**

---

## Установка для AI-агента

```bash
npx skills add https://github.com/adaybekovt-boop/TK3D --skill tk3d
```

После установки достаточно попросить coding agent использовать **TK3D** при создании или изменении 3D-сцен.

---

## Зачем нужен TK3D

Современные флагманские AI-модели уже достаточно хорошо умеют управлять Blender.

Проблема в другом.

Без специализированного 3D-слоя модель постоянно вынуждена:

- придумывать геометрию заново;
- писать большие временные `bpy`-скрипты;
- повторно решать одни и те же задачи;
- угадывать размеры и топологию;
- чинить дырки и сломанную геометрию;
- тратить контекст на уже давно решённые задачи.

TK3D меняет этот процесс.

Вместо генерации всего с нуля модель сначала ищет подходящую готовую возможность, задаёт параметры, при необходимости комбинирует несколько генераторов и отправляет результат через единый pipeline проверки.

```text
Задача
  ↓
TK3D
  ↓
Поиск возможностей
  ↓
Выбор / комбинация генераторов
  ↓
Генерация
  ↓
Blender
  ↓
QA / исправление
  ↓
Готовая сцена
```

---

## Библиотека объектов

TK3D содержит большой searchable-каталог процедурных 3D-возможностей.

Текущий основной каталог:

| Статус | Количество |
| --- | ---: |
| NATIVE | 8 |
| ADAPTED | 5 |
| REFERENCE | 535 |
| UNSUPPORTED | 8 |
| **Всего** | **556** |

Библиотека исходников содержит:

- **345 Python-файлов**
- **39 open-source проектов**
- архитектуру
- здания
- мебель
- индустриальные объекты
- бытовые предметы
- природу
- пропсы
- уличную инфраструктуру
- общие инструменты работы с геометрией

В библиотеке есть генераторы и reference-реализации для:

- домов
- складов
- лестниц
- вертикальных лестниц
- дорог
- балконов
- перил
- деревьев
- камней
- стульев
- диванов
- столов
- шкафов
- бытовой техники
- труб
- архитектурных систем
- промышленного оборудования
- сотен других типов объектов

Наличие объекта в каталоге не означает, что он автоматически считается полностью поддерживаемым.

TK3D отдельно отмечает рабочие генераторы и reference-код.

---

## Поиск по смыслу

TK3D ищет объекты не только по названию файла, а по их назначению.

Например:

```text
лестница между первым и вторым этажом
```

должна привести к обычной лестнице со ступенями.

А:

```text
вертикальная лестница, по которой нужно карабкаться руками
```

должна привести к лестнице с двумя стойками и перекладинами.

Такой принцип используется во всей библиотеке.

Модель сначала получает короткий список подходящих возможностей и только затем открывает детали выбранного генератора.

Поэтому даже очень большая библиотека не должна забивать контекст модели.

---

## Статусы генераторов

### NATIVE

Генераторы, изначально реализованные для TK3D и прошедшие его pipeline проверки.

Например:

- комнаты
- стены
- полы
- потолки
- балки
- колонны
- обычные лестницы

### ADAPTED

Внешние процедурные решения, адаптированные под TK3D.

Например:

- вертикальные лестницы
- балконы
- перила
- дороги
- столы

### REFERENCE

Полезный open-source procedural код, который модель может находить и использовать как основу для будущего генератора.

REFERENCE не считается полноценной runtime-поддержкой до адаптации и проверки.

---

## Pipeline геометрии

Рабочие генераторы TK3D проходят единый pipeline:

```text
Описание сцены
→ Генератор
→ Представление геометрии
→ Staging в Blender
→ Geometry QA
→ Контролируемое исправление
→ Commit
```

До публикации геометрия проверяется автоматически.

TK3D способен обнаруживать:

- вырожденные полигоны;
- дублирующиеся вершины и поверхности;
- loose geometry;
- non-manifold геометрию;
- неправильные transforms;
- NaN и другие некорректные значения;
- повреждённую геометрию;
- слишком мелкие или некорректные элементы.

Если quality gate не пройден, сломанный результат не публикуется.

---

## Сделано для AI

TK3D — не обычный Blender asset browser.

Проект специально построен вокруг работы AI coding/reasoning agents.

Вместо размышлений на уровне тысяч операций с вершинами модель может работать на уровне объектов:

```text
building.house
building.stairs
industrial.pipe
industrial.vent
furniture.desk
nature.tree
street.lamp
```

А TK3D предоставляет соответствующую библиотеку генераторов и procedural knowledge.

В результате модель может тратить reasoning на сам дизайн сцены, а не на повторное изобретение базовой геометрии.

---

## Развитие

TK3D рассчитан на постоянное расширение.

Новые возможности могут проходить путь:

```text
REFERENCE
→ ADAPTED
→ production-ready
```

Сейчас библиотека расширяется сразу в нескольких направлениях:

- новые procedural objects;
- PBR-материалы и текстуры;
- автоматическая оптимизация больших сцен.

Долгосрочная цель TK3D — стать своеобразной **3D standard library для AI-агентов**.

---

## Подход

TK3D не пытается заменить интеллект модели.

Он даёт модели более сильный инструментарий.

AI по-прежнему решает:

- что должно находиться в сцене;
- какой дизайн использовать;
- какие генераторы комбинировать;
- какие размеры подходят;
- какой стиль нужен;
- когда требуется создать новую capability.

TK3D отвечает за переиспользуемые знания о геометрии, инфраструктуру генерации и проверку результата.

---

## Лицензия

Собственный код TK3D распространяется под MIT License.

Сторонние procedural implementations сохраняют оригинальные лицензии.

Информация об источнике, лицензии и происхождении хранится в каталоге TK3D.

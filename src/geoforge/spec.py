from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence, TypeAlias

from .errors import SpecError, UnsupportedFeatureError


SCHEMA_VERSION = "1.0"
SUPPORTED_KINDS = frozenset(
    {
        "box",
        "wall",
        "room",
        "floor",
        "ceiling",
        "straight_stairs",
        "beam",
        "column",
    }
)
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_UNIT_FACTORS = {"m": 1.0, "cm": 0.01, "mm": 0.001}


@dataclass(frozen=True)
class TransformSpec:
    position: tuple[float, float, float] = (0.0, 0.0, 0.0)
    yaw_deg: float = 0.0


@dataclass(frozen=True)
class OpeningSpec:
    id: str
    kind: str
    offset: float
    width: float
    height: float
    bottom: float
    wall: str | None = None

    @property
    def left(self) -> float:
        return self.offset - self.width * 0.5

    @property
    def right(self) -> float:
        return self.offset + self.width * 0.5

    @property
    def top(self) -> float:
        return self.bottom + self.height


@dataclass(frozen=True)
class BoxParams:
    width: float
    depth: float
    height: float


@dataclass(frozen=True)
class WallParams:
    length: float
    height: float
    thickness: float
    openings: tuple[OpeningSpec, ...] = ()


@dataclass(frozen=True)
class RoomParams:
    width: float
    length: float
    height: float
    wall_thickness: float
    floor_thickness: float
    ceiling: bool
    ceiling_thickness: float
    openings: tuple[OpeningSpec, ...] = ()
    size_mode: str = "CLEAR_INTERIOR"


@dataclass(frozen=True)
class FloorParams:
    width: float
    length: float
    thickness: float


@dataclass(frozen=True)
class CeilingParams:
    width: float
    length: float
    thickness: float


@dataclass(frozen=True)
class StairsParams:
    width: float
    run: float
    rise: float
    max_riser: float
    min_tread: float


@dataclass(frozen=True)
class BeamParams:
    length: float
    width: float
    height: float


@dataclass(frozen=True)
class ColumnParams:
    width: float
    depth: float
    height: float


@dataclass(frozen=True)
class ExtensionParams:
    """Validated adapter-kind parameters. Values are already in metres."""

    kind: str
    values: tuple[tuple[str, float | int | bool | str], ...]

    def as_dict(self) -> dict[str, float | int | bool | str]:
        return dict(self.values)


EntityParams: TypeAlias = (
    BoxParams
    | WallParams
    | RoomParams
    | FloorParams
    | CeilingParams
    | StairsParams
    | BeamParams
    | ColumnParams
    | ExtensionParams
)


@dataclass(frozen=True)
class EntitySpec:
    id: str
    kind: str
    transform: TransformSpec
    params: EntityParams


@dataclass(frozen=True)
class QualitySpec:
    profile: str = "production"
    min_feature_size: float = 0.01


@dataclass(frozen=True)
class OutputSpec:
    save_blend: bool = False
    blend: str = "scene.blend"
    report: str = "build-report.json"
    manifest: str = "build-manifest.json"


@dataclass(frozen=True)
class SceneSpec:
    schema_version: str
    scene_id: str
    seed: int
    units: str
    entities: tuple[EntitySpec, ...]
    quality: QualitySpec
    output: OutputSpec
    source_units: str = "m"

    def to_normalized_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "scene_id": self.scene_id,
            "seed": self.seed,
            "units": "m",
            "entities": [_entity_to_dict(entity) for entity in self.entities],
            "quality": {
                "profile": self.quality.profile,
                "min_feature_size": self.quality.min_feature_size,
            },
            "output": {
                "save_blend": self.output.save_blend,
                "blend": self.output.blend,
                "report": self.output.report,
                "manifest": self.output.manifest,
            },
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.to_normalized_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )

    @property
    def spec_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def _entity_to_dict(entity: EntitySpec) -> dict[str, Any]:
    params = entity.params
    if isinstance(params, BoxParams):
        params_dict: dict[str, Any] = {
            "width": params.width,
            "depth": params.depth,
            "height": params.height,
        }
    elif isinstance(params, WallParams):
        params_dict = {
            "length": params.length,
            "height": params.height,
            "thickness": params.thickness,
            "openings": [_opening_to_dict(item) for item in params.openings],
        }
    elif isinstance(params, RoomParams):
        params_dict = {
            "width": params.width,
            "length": params.length,
            "height": params.height,
            "wall_thickness": params.wall_thickness,
            "floor_thickness": params.floor_thickness,
            "ceiling": params.ceiling,
            "ceiling_thickness": params.ceiling_thickness,
            "size_mode": params.size_mode,
            "openings": [_opening_to_dict(item) for item in params.openings],
        }
    elif isinstance(params, FloorParams | CeilingParams):
        params_dict = {
            "width": params.width,
            "length": params.length,
            "thickness": params.thickness,
        }
    elif isinstance(params, StairsParams):
        params_dict = {
            "width": params.width,
            "run": params.run,
            "rise": params.rise,
            "max_riser": params.max_riser,
            "min_tread": params.min_tread,
        }
    elif isinstance(params, BeamParams):
        params_dict = {
            "length": params.length,
            "width": params.width,
            "height": params.height,
        }
    elif isinstance(params, ColumnParams):
        params_dict = {
            "width": params.width,
            "depth": params.depth,
            "height": params.height,
        }
    elif isinstance(params, ExtensionParams):
        params_dict = dict(params.values)
    else:  # pragma: no cover - guarded by the EntityParams type
        raise TypeError(f"Unhandled params type: {type(params)!r}")

    return {
        "id": entity.id,
        "kind": entity.kind,
        "transform": {
            "position": list(entity.transform.position),
            "yaw_deg": entity.transform.yaw_deg,
        },
        "params": params_dict,
    }


def _opening_to_dict(opening: OpeningSpec) -> dict[str, Any]:
    result: dict[str, Any] = {
        "id": opening.id,
        "kind": opening.kind,
        "offset": opening.offset,
        "width": opening.width,
        "height": opening.height,
        "bottom": opening.bottom,
    }
    if opening.wall is not None:
        result["wall"] = opening.wall
    return result


def stable_hash_int(*parts: object, bits: int = 64) -> int:
    payload = json.dumps(parts, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    return int.from_bytes(digest[: bits // 8], byteorder="big", signed=False)


def derive_entity_seed(
    global_seed: int,
    entity_id: str,
    builder_kind: str,
    builder_version: str,
) -> int:
    return stable_hash_int(global_seed, entity_id, builder_kind, builder_version)


def entity_spec_hash(entity: EntitySpec) -> str:
    encoded = json.dumps(
        _entity_to_dict(entity),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def load_scene_spec(path: str | Path) -> SceneSpec:
    source = Path(path)
    try:
        data = json.loads(
            source.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_json_fields,
        )
    except OSError as exc:
        raise SpecError(
            f"Cannot read SceneSpec: {exc}", code="SPEC.READ_FAILED", path=str(source)
        ) from exc
    except json.JSONDecodeError as exc:
        raise SpecError(
            f"Invalid JSON: {exc.msg}",
            code="SPEC.INVALID_JSON",
            path=f"{source}:{exc.lineno}:{exc.colno}",
        ) from exc
    return decode_scene_spec(data)


def _reject_duplicate_json_fields(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SpecError(
                f"Duplicate JSON field {key!r}",
                code="SPEC.DUPLICATE_FIELD",
                path="/",
            )
        result[key] = value
    return result


def decode_scene_spec(data: Any) -> SceneSpec:
    root = _object(data, path="/")
    _only(
        root,
        {"schema_version", "scene_id", "seed", "units", "entities", "quality", "output"},
        path="/",
    )

    version = _string(_required(root, "schema_version", "/"), "/schema_version")
    if version != SCHEMA_VERSION:
        raise UnsupportedFeatureError(
            f"Unsupported schema version {version!r}; expected {SCHEMA_VERSION!r}",
            path="/schema_version",
        )

    scene_id = _identifier(_required(root, "scene_id", "/"), "/scene_id")
    seed = _integer(_required(root, "seed", "/"), "/seed")
    source_units = _string(root.get("units", "m"), "/units")
    if source_units not in _UNIT_FACTORS:
        raise SpecError(
            f"Unsupported units {source_units!r}", code="SPEC.UNSUPPORTED_UNITS", path="/units"
        )
    factor = _UNIT_FACTORS[source_units]

    quality = _parse_quality(root.get("quality", {}), factor)
    output = _parse_output(root.get("output", {}), scene_id)

    entities_value = _required(root, "entities", "/")
    if not isinstance(entities_value, list):
        raise SpecError("entities must be an array", path="/entities")
    entities = tuple(
        _parse_entity(value, factor, f"/entities/{index}")
        for index, value in enumerate(entities_value)
    )
    ids = [entity.id for entity in entities]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        raise SpecError(
            f"Duplicate entity IDs: {', '.join(duplicates)}",
            code="SPEC.DUPLICATE_ENTITY_ID",
            path="/entities",
        )

    spec = SceneSpec(
        schema_version=version,
        scene_id=scene_id,
        seed=seed,
        units="m",
        source_units=source_units,
        entities=entities,
        quality=quality,
        output=output,
    )
    _validate_semantics(spec)
    return spec


def validate_scene_spec(data: Any) -> tuple[bool, dict[str, Any]]:
    try:
        spec = decode_scene_spec(data)
    except SpecError as exc:
        return False, exc.to_dict()
    return True, {"status": "PASS", "spec_hash": spec.spec_hash}


def _parse_entity(value: Any, factor: float, path: str) -> EntitySpec:
    obj = _object(value, path)
    _only(obj, {"id", "kind", "transform", "params"}, path)
    entity_id = _identifier(_required(obj, "id", path), f"{path}/id")
    kind = _string(_required(obj, "kind", path), f"{path}/kind")
    if kind not in SUPPORTED_KINDS and not _is_adapter_kind(kind):
        raise UnsupportedFeatureError(f"Unsupported entity kind {kind!r}", path=f"{path}/kind")
    transform = _parse_transform(obj.get("transform", {}), factor, f"{path}/transform")
    params_obj = _object(_required(obj, "params", path), f"{path}/params")
    params = _parse_params(kind, params_obj, factor, f"{path}/params")
    return EntitySpec(entity_id, kind, transform, params)


def _parse_transform(value: Any, factor: float, path: str) -> TransformSpec:
    obj = _object(value, path)
    _only(obj, {"position", "yaw_deg"}, path)
    raw_position = obj.get("position", [0.0, 0.0, 0.0])
    if not isinstance(raw_position, list) or len(raw_position) != 3:
        raise SpecError("position must contain exactly three numbers", path=f"{path}/position")
    position = tuple(
        _number(item, f"{path}/position/{index}") * factor
        for index, item in enumerate(raw_position)
    )
    yaw_deg = _number(obj.get("yaw_deg", 0.0), f"{path}/yaw_deg")
    return TransformSpec(position=position, yaw_deg=yaw_deg)


def _parse_params(kind: str, obj: Mapping[str, Any], factor: float, path: str) -> EntityParams:
    def length(name: str) -> float:
        return _positive(_required(obj, name, path), f"{path}/{name}") * factor

    if kind == "box":
        _only(obj, {"width", "depth", "height"}, path)
        return BoxParams(length("width"), length("depth"), length("height"))
    if kind == "wall":
        _only(obj, {"length", "height", "thickness", "openings"}, path)
        openings = _parse_openings(obj.get("openings", []), factor, path, require_wall=False)
        return WallParams(length("length"), length("height"), length("thickness"), openings)
    if kind == "room":
        _only(
            obj,
            {
                "width",
                "length",
                "height",
                "wall_thickness",
                "floor_thickness",
                "ceiling",
                "ceiling_thickness",
                "size_mode",
                "openings",
            },
            path,
        )
        width = length("width")
        room_length = length("length")
        height = length("height")
        wall_thickness = length("wall_thickness")
        floor_thickness = length("floor_thickness")
        ceiling = _boolean(obj.get("ceiling", False), f"{path}/ceiling")
        ceiling_thickness = (
            _positive(obj["ceiling_thickness"], f"{path}/ceiling_thickness") * factor
            if "ceiling_thickness" in obj
            else floor_thickness
        )
        size_mode = _string(obj.get("size_mode", "CLEAR_INTERIOR"), f"{path}/size_mode")
        if size_mode != "CLEAR_INTERIOR":
            raise UnsupportedFeatureError(
                "V1 supports only size_mode='CLEAR_INTERIOR'", path=f"{path}/size_mode"
            )
        openings = _parse_openings(obj.get("openings", []), factor, path, require_wall=True)
        return RoomParams(
            width,
            room_length,
            height,
            wall_thickness,
            floor_thickness,
            ceiling,
            ceiling_thickness,
            openings,
            size_mode,
        )
    if kind in {"floor", "ceiling"}:
        _only(obj, {"width", "length", "thickness"}, path)
        values = (length("width"), length("length"), length("thickness"))
        return FloorParams(*values) if kind == "floor" else CeilingParams(*values)
    if kind == "straight_stairs":
        _only(obj, {"width", "run", "rise", "max_riser", "min_tread"}, path)
        max_riser = (
            _positive(obj["max_riser"], f"{path}/max_riser") * factor
            if "max_riser" in obj
            else 0.20
        )
        min_tread = (
            _positive(obj["min_tread"], f"{path}/min_tread") * factor
            if "min_tread" in obj
            else 0.20
        )
        return StairsParams(length("width"), length("run"), length("rise"), max_riser, min_tread)
    if kind == "beam":
        _only(obj, {"length", "width", "height"}, path)
        return BeamParams(length("length"), length("width"), length("height"))
    if kind == "column":
        _only(obj, {"width", "depth", "height"}, path)
        return ColumnParams(length("width"), length("depth"), length("height"))
    if _is_adapter_kind(kind):
        return _parse_extension_params(kind, obj, factor, path)
    raise UnsupportedFeatureError(f"Unsupported entity kind {kind!r}", path=path)


def _parse_openings(
    value: Any,
    factor: float,
    parent_path: str,
    *,
    require_wall: bool,
) -> tuple[OpeningSpec, ...]:
    path = f"{parent_path}/openings"
    if not isinstance(value, list):
        raise SpecError("openings must be an array", path=path)
    result: list[OpeningSpec] = []
    for index, raw in enumerate(value):
        item_path = f"{path}/{index}"
        obj = _object(raw, item_path)
        _only(obj, {"id", "kind", "wall", "offset", "width", "height", "bottom"}, item_path)
        opening_id = _identifier(_required(obj, "id", item_path), f"{item_path}/id")
        kind = _string(_required(obj, "kind", item_path), f"{item_path}/kind")
        if kind not in {"door", "window"}:
            raise UnsupportedFeatureError(f"Unsupported opening kind {kind!r}", path=f"{item_path}/kind")
        wall = obj.get("wall")
        if require_wall:
            wall = _string(_required(obj, "wall", item_path), f"{item_path}/wall")
            if wall not in {"south", "north", "west", "east"}:
                raise SpecError("wall must be south, north, west, or east", path=f"{item_path}/wall")
        elif wall is not None:
            raise SpecError("standalone wall openings must not specify wall", path=f"{item_path}/wall")
        offset = _number(_required(obj, "offset", item_path), f"{item_path}/offset") * factor
        width = _positive(_required(obj, "width", item_path), f"{item_path}/width") * factor
        height = _positive(_required(obj, "height", item_path), f"{item_path}/height") * factor
        if kind == "window" and "bottom" not in obj:
            raise SpecError("window opening requires bottom", path=f"{item_path}/bottom")
        bottom = _number(obj.get("bottom", 0.0), f"{item_path}/bottom") * factor
        if bottom < 0.0:
            raise SpecError("opening bottom must be >= 0", path=f"{item_path}/bottom")
        if kind == "door" and not math.isclose(bottom, 0.0, abs_tol=1e-12):
            raise UnsupportedFeatureError("V1 door openings must start at floor level", path=f"{item_path}/bottom")
        result.append(OpeningSpec(opening_id, kind, offset, width, height, bottom, wall))

    ids = [item.id for item in result]
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        raise SpecError(
            f"Duplicate opening IDs: {', '.join(duplicates)}",
            code="SPEC.DUPLICATE_OPENING_ID",
            path=path,
        )
    return tuple(result)


def _parse_quality(value: Any, factor: float) -> QualitySpec:
    obj = _object(value, "/quality")
    _only(obj, {"profile", "min_feature_size"}, "/quality")
    profile = _string(obj.get("profile", "production"), "/quality/profile")
    if profile != "production":
        raise UnsupportedFeatureError(
            f"V1 supports only quality profile 'production', not {profile!r}",
            path="/quality/profile",
        )
    min_feature = (
        _positive(obj["min_feature_size"], "/quality/min_feature_size") * factor
        if "min_feature_size" in obj
        else 0.01
    )
    return QualitySpec(profile, min_feature)


def _parse_output(value: Any, scene_id: str) -> OutputSpec:
    obj = _object(value, "/output")
    _only(obj, {"save_blend", "blend", "report", "manifest"}, "/output")
    save_blend = _boolean(obj.get("save_blend", False), "/output/save_blend")
    blend = _relative_path(obj.get("blend", f"{scene_id}.blend"), "/output/blend")
    report = _relative_path(obj.get("report", "build-report.json"), "/output/report")
    manifest = _relative_path(obj.get("manifest", "build-manifest.json"), "/output/manifest")
    paths = (blend, report, manifest)
    if len({path.casefold() for path in paths}) != len(paths):
        raise SpecError(
            "blend, report, and manifest paths must be distinct",
            code="SPEC.OUTPUT_PATH_COLLISION",
            path="/output",
        )
    return OutputSpec(save_blend, blend, report, manifest)


def _validate_semantics(spec: SceneSpec) -> None:
    for entity_index, entity in enumerate(spec.entities):
        path = f"/entities/{entity_index}/params"
        params = entity.params
        if isinstance(params, WallParams):
            _validate_openings(params.openings, params.length, params.height, spec.quality.min_feature_size, path)
        elif isinstance(params, RoomParams):
            for wall in ("south", "north", "west", "east"):
                wall_length = params.width if wall in {"south", "north"} else params.length
                wall_openings = tuple(item for item in params.openings if item.wall == wall)
                _validate_openings(wall_openings, wall_length, params.height, spec.quality.min_feature_size, path)
        elif isinstance(params, StairsParams):
            risers = max(1, math.ceil(params.rise / params.max_riser))
            tread = params.run / risers
            if tread + 1e-12 < params.min_tread:
                raise SpecError(
                    f"stairs are infeasible: tread {tread:.6g}m is below min_tread {params.min_tread:.6g}m",
                    code="SPEC.INFEASIBLE_STAIRS",
                    path=path,
                )
        elif isinstance(params, ExtensionParams):
            from .adapters.schema import validate_extension_values

            validate_extension_values(params.kind, params.as_dict(), path)


def _validate_openings(
    openings: Sequence[OpeningSpec],
    wall_length: float,
    wall_height: float,
    min_feature: float,
    path: str,
) -> None:
    for opening in openings:
        if opening.left < -1e-12 or opening.right > wall_length + 1e-12:
            raise SpecError(
                f"opening {opening.id!r} does not fit within its wall",
                code="SPEC.OPENING_OUT_OF_BOUNDS",
                path=f"{path}/openings",
            )
        if opening.top > wall_height + 1e-12:
            raise SpecError(
                f"opening {opening.id!r} is higher than its wall",
                code="SPEC.OPENING_OUT_OF_BOUNDS",
                path=f"{path}/openings",
            )
    ordered = sorted(openings, key=lambda item: (item.left, item.bottom, item.id))
    for index, first in enumerate(ordered):
        for second in ordered[index + 1 :]:
            x_overlap = min(first.right, second.right) - max(first.left, second.left)
            z_overlap = min(first.top, second.top) - max(first.bottom, second.bottom)
            if x_overlap > 0.0 and z_overlap > 0.0:
                raise SpecError(
                    f"openings {first.id!r} and {second.id!r} overlap",
                    code="SPEC.OVERLAPPING_OPENINGS",
                    path=f"{path}/openings",
                )
            horizontal_gap = max(second.left - first.right, first.left - second.right, 0.0)
            vertical_overlap = z_overlap > 0.0
            if vertical_overlap and 0.0 < horizontal_gap < min_feature:
                raise SpecError(
                    f"openings {first.id!r} and {second.id!r} leave a feature below min_feature_size",
                    code="SPEC.FEATURE_TOO_SMALL",
                    path=f"{path}/openings",
                )


def _object(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise SpecError("expected an object", path=path)
    return value


def _only(obj: Mapping[str, Any], allowed: set[str], path: str) -> None:
    unknown = sorted(set(obj) - allowed)
    if unknown:
        raise SpecError(
            f"Unknown field(s): {', '.join(unknown)}",
            code="SPEC.UNKNOWN_FIELD",
            path=path,
            context={"fields": unknown},
        )


def _required(obj: Mapping[str, Any], key: str, path: str) -> Any:
    if key not in obj:
        raise SpecError(f"Missing required field {key!r}", code="SPEC.MISSING_FIELD", path=f"{path.rstrip('/')}/{key}")
    return obj[key]


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise SpecError("expected a non-empty string", path=path)
    return value


def _identifier(value: Any, path: str) -> str:
    result = _string(value, path)
    if not _ID_RE.fullmatch(result):
        raise SpecError("invalid stable identifier", code="SPEC.INVALID_ID", path=path)
    return result


def _number(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SpecError("expected a finite number", path=path)
    result = float(value)
    if not math.isfinite(result):
        raise SpecError("expected a finite number", code="SPEC.NON_FINITE_NUMBER", path=path)
    return result


def _positive(value: Any, path: str) -> float:
    result = _number(value, path)
    if result <= 0.0:
        raise SpecError("expected a value > 0", code="SPEC.NON_POSITIVE_DIMENSION", path=path)
    return result


def _integer(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise SpecError("expected an integer", path=path)
    return value


def _boolean(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise SpecError("expected a boolean", path=path)
    return value


def _relative_path(value: Any, path: str) -> str:
    result = _string(value, path)
    candidate = Path(result)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise SpecError("output path must be relative and remain below output root", code="SPEC.UNSAFE_PATH", path=path)
    return candidate.as_posix()


def _is_adapter_kind(kind: str) -> bool:
    from .adapters.schema import is_adapter_kind

    return is_adapter_kind(kind)


def _parse_extension_params(kind: str, obj: Mapping[str, Any], factor: float, path: str) -> ExtensionParams:
    from .adapters.schema import schema_fields

    fields = schema_fields(kind)
    _only(obj, set(fields), path)
    parsed: list[tuple[str, float | int | bool | str]] = []
    for name, field in fields.items():
        required = bool(field.get("required")) or "default" not in field
        if name in obj:
            raw = obj[name]
        elif required:
            raise SpecError(f"Missing required field {name!r}", code="SPEC.MISSING_FIELD", path=f"{path}/{name}")
        else:
            parsed.append((name, field["default"]))
            continue
        field_path = f"{path}/{name}"
        kind_name = field["type"]
        if kind_name == "float":
            if field.get("unit") == "length":
                value = _positive(raw, field_path) * factor if field.get("min", 0) > 0 else _number(raw, field_path) * factor
            else:
                value = _number(raw, field_path)
            minimum = field.get("min")
            maximum = field.get("max")
            if minimum is not None and value + 1e-12 < float(minimum):
                raise SpecError(
                    f"{name} must be >= {minimum}",
                    code="SPEC.VALUE_OUT_OF_RANGE",
                    path=field_path,
                )
            if maximum is not None and value - 1e-12 > float(maximum):
                raise SpecError(
                    f"{name} must be <= {maximum}",
                    code="SPEC.VALUE_OUT_OF_RANGE",
                    path=field_path,
                )
            parsed.append((name, value))
        elif kind_name == "int":
            value_int = _integer(raw, field_path)
            minimum = field.get("min")
            maximum = field.get("max")
            if minimum is not None and value_int < int(minimum):
                raise SpecError(
                    f"{name} must be >= {minimum}",
                    code="SPEC.VALUE_OUT_OF_RANGE",
                    path=field_path,
                )
            if maximum is not None and value_int > int(maximum):
                raise SpecError(
                    f"{name} must be <= {maximum}",
                    code="SPEC.VALUE_OUT_OF_RANGE",
                    path=field_path,
                )
            parsed.append((name, value_int))
        elif kind_name == "bool":
            parsed.append((name, _boolean(raw, field_path)))
        elif kind_name == "enum":
            text = _string(raw, field_path)
            allowed = list(field["values"])
            if text not in allowed:
                raise SpecError(
                    f"{name} must be one of {', '.join(allowed)}",
                    code="SPEC.INVALID_ENUM",
                    path=field_path,
                )
            parsed.append((name, text))
        else:  # pragma: no cover
            raise SpecError(f"Unsupported parameter type {kind_name!r}", path=field_path)
    parsed.sort(key=lambda item: item[0])
    return ExtensionParams(kind, tuple(parsed))

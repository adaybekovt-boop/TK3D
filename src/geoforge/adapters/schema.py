from __future__ import annotations

from typing import Any

from ..errors import SpecError


# Canonical metres / degrees. SceneSpec converts incoming units before these mins apply.
SCHEMAS: dict[str, dict[str, Any]] = {
    "climbable_ladder": {
        "generator_id": "architecture.stairs.climbable_ladder",
        "params": {
            "height": {"type": "float", "unit": "length", "min": 0.5, "required": True},
            "width": {"type": "float", "unit": "length", "min": 0.2, "required": True},
            "rung_spacing": {"type": "float", "unit": "length", "min": 0.1, "default": 0.28},
            "rail_radius": {"type": "float", "unit": "length", "min": 0.01, "default": 0.03},
            "rung_radius": {"type": "float", "unit": "length", "min": 0.01, "default": 0.015},
            "lean_deg": {"type": "float", "min": -45.0, "max": 45.0, "default": 14.0},
        },
    },
    "railing": {
        "generator_id": "architecture.railing",
        "params": {
            "length": {"type": "float", "unit": "length", "min": 0.3, "required": True},
            "height": {"type": "float", "unit": "length", "min": 0.4, "required": True},
            "post_size": {"type": "float", "unit": "length", "min": 0.02, "default": 0.04},
            "rail_thickness": {"type": "float", "unit": "length", "min": 0.02, "default": 0.03},
            "post_spacing": {"type": "float", "unit": "length", "min": 0.08, "default": 0.16},
            "rail_count": {"type": "int", "min": 1, "max": 8, "default": 2},
            "fill": {"type": "enum", "values": ["posts", "rails", "wall"], "default": "posts"},
            "bottom_rail": {"type": "bool", "default": True},
        },
    },
    "balcony": {
        "generator_id": "architecture.balcony",
        "params": {
            "width": {"type": "float", "unit": "length", "min": 0.6, "required": True},
            "depth": {"type": "float", "unit": "length", "min": 0.4, "required": True},
            "slab_thickness": {"type": "float", "unit": "length", "min": 0.04, "default": 0.12},
            "has_railing": {"type": "bool", "default": True},
            "rail_height": {"type": "float", "unit": "length", "min": 0.4, "default": 1.0},
            "post_size": {"type": "float", "unit": "length", "min": 0.02, "default": 0.04},
            "post_spacing": {"type": "float", "unit": "length", "min": 0.1, "default": 0.2},
        },
    },
    "road": {
        "generator_id": "infrastructure.road",
        "params": {
            "length": {"type": "float", "unit": "length", "min": 1.0, "required": True},
            "width": {"type": "float", "unit": "length", "min": 2.0, "required": True},
            "thickness": {"type": "float", "unit": "length", "min": 0.04, "default": 0.12},
            "sidewalks": {"type": "bool", "default": False},
            "sidewalk_width": {"type": "float", "unit": "length", "min": 0.4, "default": 1.5},
            "sidewalk_height": {"type": "float", "unit": "length", "min": 0.04, "default": 0.15},
            "shoulders": {"type": "bool", "default": False},
            "shoulder_width": {"type": "float", "unit": "length", "min": 0.2, "default": 0.5},
        },
    },
    "desk": {
        "generator_id": "furniture.desk.simple",
        "params": {
            "width": {"type": "float", "unit": "length", "min": 0.5, "required": True},
            "depth": {"type": "float", "unit": "length", "min": 0.4, "required": True},
            "height": {"type": "float", "unit": "length", "min": 0.5, "required": True},
            "thickness": {"type": "float", "unit": "length", "min": 0.02, "default": 0.03},
            "leg_size": {"type": "float", "unit": "length", "min": 0.02, "default": 0.05},
            "leg_inset": {"type": "float", "unit": "length", "min": 0.02, "default": 0.05},
        },
    },
}


def adapter_kind_set() -> frozenset[str]:
    return frozenset(SCHEMAS)


def is_adapter_kind(kind: str) -> bool:
    return kind in SCHEMAS


def schema_fields(kind: str) -> dict[str, dict[str, Any]]:
    return SCHEMAS[kind]["params"]


def public_param_schema(kind: str) -> dict[str, Any]:
    entry = SCHEMAS[kind]
    params: dict[str, Any] = {}
    for name, field in entry["params"].items():
        item = {key: field[key] for key in ("type", "min", "max", "default", "values") if key in field}
        if field.get("required"):
            item["required"] = True
        params[name] = item
    return {"generator": entry["generator_id"], "kind": kind, "params": params}


def public_param_schema_for_generator(generator_id: str) -> dict[str, Any] | None:
    for kind, entry in SCHEMAS.items():
        if entry["generator_id"] == generator_id:
            return public_param_schema(kind)
    return None


def kind_for_generator(generator_id: str) -> str | None:
    for kind, entry in SCHEMAS.items():
        if entry["generator_id"] == generator_id:
            return kind
    return None


def validate_extension_values(kind: str, values: dict[str, Any], path: str) -> None:
    if kind == "climbable_ladder":
        if values["width"] < 4.0 * values["rail_radius"]:
            raise SpecError(
                "ladder width must leave a usable gap between rails",
                code="SPEC.INFEASIBLE_LADDER",
                path=path,
            )
        if values["height"] <= 2.0 * values["rung_radius"] + values["rung_spacing"]:
            raise SpecError(
                "ladder height cannot fit a rung at the given spacing",
                code="SPEC.INFEASIBLE_LADDER",
                path=path,
            )
    elif kind == "railing":
        if values["length"] <= 2.0 * values["post_size"]:
            raise SpecError(
                "railing length must fit two end posts",
                code="SPEC.INFEASIBLE_RAILING",
                path=path,
            )
    elif kind == "balcony":
        if values["has_railing"] and (
            values["width"] <= 2.0 * values["post_size"] or values["depth"] <= 2.0 * values["post_size"]
        ):
            raise SpecError(
                "balcony slab is too small for a railing",
                code="SPEC.INFEASIBLE_BALCONY",
                path=path,
            )
    elif kind == "desk":
        span_x = 2.0 * (values["leg_inset"] + values["leg_size"])
        span_y = 2.0 * (values["leg_inset"] + values["leg_size"])
        if values["width"] <= span_x or values["depth"] <= span_y:
            raise SpecError(
                "desk top is too small for four inset legs",
                code="SPEC.INFEASIBLE_DESK",
                path=path,
            )
        if values["height"] <= values["thickness"]:
            raise SpecError(
                "desk height must exceed top thickness",
                code="SPEC.INFEASIBLE_DESK",
                path=path,
            )

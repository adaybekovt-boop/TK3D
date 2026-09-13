from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from ..adapters.schema import public_param_schema_for_generator
from ..errors import SpecError
from ..paths import catalog_json_path, repo_root, vendor_library_root

STATUSES = ("NATIVE", "ADAPTED", "REFERENCE", "UNSUPPORTED")

_NATIVE_SCHEMAS: dict[str, dict[str, Any]] = {
    "geometry.box": {
        "generator": "geometry.box",
        "kind": "box",
        "params": {
            "width": {"type": "float", "required": True},
            "depth": {"type": "float", "required": True},
            "height": {"type": "float", "required": True},
        },
    },
    "architecture.wall": {
        "generator": "architecture.wall",
        "kind": "wall",
        "params": {
            "length": {"type": "float", "required": True},
            "height": {"type": "float", "required": True},
            "thickness": {"type": "float", "required": True},
            "openings": {"type": "array"},
        },
    },
    "architecture.room": {
        "generator": "architecture.room",
        "kind": "room",
        "params": {
            "width": {"type": "float", "required": True},
            "length": {"type": "float", "required": True},
            "height": {"type": "float", "required": True},
            "wall_thickness": {"type": "float", "required": True},
            "floor_thickness": {"type": "float", "required": True},
            "ceiling": {"type": "bool", "default": False},
            "ceiling_thickness": {"type": "float"},
            "size_mode": {"type": "enum", "values": ["CLEAR_INTERIOR"], "default": "CLEAR_INTERIOR"},
            "openings": {"type": "array"},
        },
    },
    "architecture.floor": {
        "generator": "architecture.floor",
        "kind": "floor",
        "params": {
            "width": {"type": "float", "required": True},
            "length": {"type": "float", "required": True},
            "thickness": {"type": "float", "required": True},
        },
    },
    "architecture.ceiling": {
        "generator": "architecture.ceiling",
        "kind": "ceiling",
        "params": {
            "width": {"type": "float", "required": True},
            "length": {"type": "float", "required": True},
            "thickness": {"type": "float", "required": True},
        },
    },
    "architecture.stairs.walkable": {
        "generator": "architecture.stairs.walkable",
        "kind": "straight_stairs",
        "params": {
            "width": {"type": "float", "required": True},
            "run": {"type": "float", "required": True},
            "rise": {"type": "float", "required": True},
            "max_riser": {"type": "float", "default": 0.2},
            "min_tread": {"type": "float", "default": 0.2},
        },
    },
    "architecture.beam": {
        "generator": "architecture.beam",
        "kind": "beam",
        "params": {
            "length": {"type": "float", "required": True},
            "width": {"type": "float", "required": True},
            "height": {"type": "float", "required": True},
        },
    },
    "architecture.column": {
        "generator": "architecture.column",
        "kind": "column",
        "params": {
            "width": {"type": "float", "required": True},
            "depth": {"type": "float", "required": True},
            "height": {"type": "float", "required": True},
        },
    },
}


@lru_cache(maxsize=1)
def load_catalog() -> tuple[dict[str, Any], ...]:
    raw = json.loads(catalog_json_path().read_text(encoding="utf-8"))
    vendor_groups = _vendor_groups()
    file_index = _file_index()
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in raw["generators"]:
        entry = dict(item)
        generator_id = entry["id"]
        if generator_id in seen:
            raise ValueError(f"Duplicate generator id {generator_id!r}")
        seen.add(generator_id)
        if entry["status"] not in STATUSES:
            raise ValueError(f"Invalid status for {generator_id}: {entry['status']}")
        entry.setdefault("current_tk3d_status", entry["status"])
        entry.setdefault("local_source", entry.get("source_file"))
        entry.setdefault("source_file", entry.get("local_source"))
        entry.setdefault("repository", entry.get("source_repo"))
        entry.setdefault("pinned_commit", entry.get("source_commit"))
        entry.setdefault("upstream_source", entry.get("source_file"))
        entry.setdefault("source_available", bool(entry.get("local_source")))
        vendor = vendor_groups.get(entry.get("vendor_group") or "")
        if vendor:
            source = vendor["source"]
            entry.setdefault("source_project", source.get("project"))
            entry.setdefault("source_repo", source.get("repo"))
            entry.setdefault("source_commit", source.get("commit"))
            entry.setdefault("license", source.get("license"))
            if not entry.get("source_file") and vendor.get("files"):
                entry["source_file"] = f"vendor/generator_library/{vendor['files'][0]}"
        origin = entry.get("origin") or {}
        entry.setdefault("source_project", origin.get("project"))
        entry.setdefault("source_repo", entry.get("repository") or origin.get("repo"))
        entry.setdefault("source_commit", entry.get("pinned_commit") or origin.get("commit"))
        entry.setdefault("license", origin.get("license"))
        source_file = entry.get("source_file")
        if source_file:
            rel = source_file.replace("\\", "/")
            info = file_index.get(rel.removeprefix("vendor/generator_library/"))
            if info:
                entry.setdefault("sha256", info.get("sha256"))
                entry.setdefault("source_project", info["source"].get("project"))
                entry.setdefault("source_repo", info["source"].get("repo"))
                entry.setdefault("source_commit", info["source"].get("commit"))
                entry.setdefault("license", info["source"].get("license"))
        if entry["status"] in {"NATIVE", "ADAPTED"}:
            entry["param_schema"] = public_param_schema_for_generator(generator_id) or _NATIVE_SCHEMAS.get(
                generator_id
            )
        else:
            entry["param_schema"] = None
        entries.append(entry)
    return tuple(entries)


def catalog_by_id() -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in load_catalog()}


def get_generator(generator_id: str) -> dict[str, Any]:
    try:
        return catalog_by_id()[generator_id]
    except KeyError as exc:
        raise SpecError(
            f"Unknown generator {generator_id!r}",
            code="CATALOG.UNKNOWN_GENERATOR",
            path=generator_id,
        ) from exc


def describe_generator(generator_id: str) -> dict[str, Any]:
    entry = get_generator(generator_id)
    return {
        "id": entry["id"],
        "name": entry["name"],
        "meaning": entry["meaning"],
        "not_this": entry.get("not_this"),
        "params": entry.get("param_schema"),
        "backend": entry.get("backend"),
        "status": entry["status"],
        "adapter": entry.get("adapter"),
        "kind": entry.get("kind"),
        "category": entry.get("category"),
        "capability": entry.get("capability"),
        "local_source": entry.get("local_source"),
        "upstream_source": entry.get("upstream_source"),
        "implementation_source": entry.get("implementation_source"),
        "symbol": entry.get("symbol"),
        "source_available": entry.get("source_available", False),
        "reuse_difficulty": entry.get("reuse_difficulty"),
        "license": entry.get("license"),
        "source_project": entry.get("source_project"),
        "repository": entry.get("repository") or entry.get("source_repo"),
        "pinned_commit": entry.get("pinned_commit") or entry.get("source_commit"),
        "source_revision": entry.get("source_revision"),
        "limitations": entry.get("limitations"),
        "variants": entry.get("variants", []),
        "tags": entry.get("tags", []),
        "dependency_reason": entry.get("dependency_reason"),
    }


def get_source(generator_id: str, *, include_text: bool = False) -> dict[str, Any]:
    entry = get_generator(generator_id)
    rel = entry.get("local_source") or entry.get("source_file")
    payload = {
        "id": generator_id,
        "status": entry["status"],
        "source_file": rel.replace("\\", "/") if rel else None,
        "local_source": rel.replace("\\", "/") if rel else None,
        "upstream_source": entry.get("upstream_source"),
        "symbol": entry.get("symbol"),
        "source_available": bool(rel and entry.get("source_available", True)),
        "license": entry.get("license"),
        "source_project": entry.get("source_project"),
        "repository": entry.get("repository") or entry.get("source_repo"),
        "pinned_commit": entry.get("pinned_commit") or entry.get("source_commit"),
        "source_revision": entry.get("source_revision"),
        "reuse_difficulty": entry.get("reuse_difficulty"),
        "bytes": None,
        "sha256": entry.get("sha256"),
        "note": "Reference metadata only; donor source is never imported by TK3D runtime.",
    }
    if not rel or not payload["source_available"]:
        if include_text:
            raise SpecError(
                f"Generator {generator_id!r} has no local source text",
                code="CATALOG.NO_LOCAL_SOURCE",
                path=generator_id,
            )
        return payload
    path = _resolve_source(rel)
    payload.update(
        {
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "note": "Single local source file only. Do not load the rest of the library.",
        }
    )
    if include_text:
        payload["text"] = path.read_text(encoding="utf-8")
    return payload


def list_categories() -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for entry in load_catalog():
        category = str(entry.get("category") or entry["id"]).replace("\\", "/").split("/", 1)[0]
        counts[category] = counts.get(category, 0) + 1
    return [{"id": name, "count": counts[name]} for name in sorted(counts)]


def status_counts() -> dict[str, int]:
    counts = {status: 0 for status in STATUSES}
    for entry in load_catalog():
        counts[entry["status"]] += 1
    counts["total"] = len(load_catalog())
    return counts


def _resolve_source(rel: str) -> Path:
    candidate = (repo_root() / rel).resolve()
    root = repo_root().resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise SpecError("source path escapes repository", code="CATALOG.UNSAFE_PATH") from exc
    if not candidate.is_file():
        raise SpecError(f"Source file missing: {rel}", code="CATALOG.SOURCE_MISSING", path=rel)
    return candidate


@lru_cache(maxsize=1)
def _vendor_groups() -> dict[str, Any]:
    path = vendor_library_root() / "CATALOG.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data.get("generator_groups", [])}


@lru_cache(maxsize=1)
def _file_index() -> dict[str, Any]:
    path = vendor_library_root() / "FILE_INDEX.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {item["file"].replace("\\", "/"): item for item in data}

#!/usr/bin/env python3
"""Safely consolidate TK3D's curated and object-generator research archives.

Archive Python is copied as inert reference source. Nothing from either archive is
imported or executed. The root ``catalogs/generators.json`` file is canonical; a
byte-identical package mirror is emitted for installed ``geoforge`` consumers.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import shutil
import sys
import warnings
import zipfile
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[1]
CATALOG_DIR = ROOT / "catalogs"
RUNTIME_CATALOG = CATALOG_DIR / "runtime-generators.json"
CANONICAL_CATALOG = CATALOG_DIR / "generators.json"
PACKAGE_CATALOG = ROOT / "src" / "geoforge" / "catalog" / "generators.json"
VENDOR_ROOT = ROOT / "vendor" / "generator_library"
OBJECT_ROOT = ROOT / "library" / "objects"
LICENSE_ROOT = ROOT / "licenses"

CODE_ARCHIVE_ROOT = "GeoForge_Code_Library_v1/"
OBJECT_ARCHIVE_ROOT = "GeoForge_Object_Harvest/"
OBJECT_CATALOG_MEMBER = OBJECT_ARCHIVE_ROOT + "CATALOG.json"

VALID_STATUSES = ("NATIVE", "ADAPTED", "REFERENCE", "UNSUPPORTED")
TARGET_REPOSITORY = "https://github.com/adaybekovt-boop/TK3D"

NATIVE_SYMBOLS = {
    "geometry.box": "BoxBuilder",
    "architecture.wall": "WallBuilder",
    "architecture.room": "RoomBuilder",
    "architecture.floor": "FloorBuilder",
    "architecture.ceiling": "CeilingBuilder",
    "architecture.stairs.walkable": "StraightStairsBuilder",
    "architecture.beam": "BeamBuilder",
    "architecture.column": "ColumnBuilder",
}

ADAPTER_IMPLEMENTATIONS = {
    "ClimbableLadderBuilder": "src/geoforge/adapters/ladder.py",
    "BalconyBuilder": "src/geoforge/adapters/balcony.py",
    "RailingBuilder": "src/geoforge/adapters/railing.py",
    "RoadBuilder": "src/geoforge/adapters/road.py",
    "SimpleDeskBuilder": "src/geoforge/adapters/desk.py",
}

SYMBOL_PATTERNS = (
    re.compile(
        r"(?i)(?:factory/class|factory|class|function|operator|generator)\s*[:=]?\s*`?([A-Za-z_]\w*)"
    ),
    re.compile(r"\b([A-Za-z_]\w*Factory)\b"),
    re.compile(r"\b((?:generate|create|make|build)_[A-Za-z_]\w*)\b"),
)


class ConsolidationError(RuntimeError):
    pass


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.read_bytes() == data:
        return
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


def _write_json(path: Path, payload: Any) -> None:
    data = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n").encode("utf-8")
    _write_bytes(path, data)


def _load_json_bytes(data: bytes, label: str) -> Any:
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ConsolidationError(f"Invalid JSON in {label}: {exc}") from exc


def _safe_members(archive: zipfile.ZipFile, required_root: str) -> dict[str, zipfile.ZipInfo]:
    result: dict[str, zipfile.ZipInfo] = {}
    for info in archive.infolist():
        name = info.filename.replace("\\", "/")
        pure = PurePosixPath(name)
        if pure.is_absolute() or ".." in pure.parts or not name.startswith(required_root):
            raise ConsolidationError(f"Unsafe archive member: {info.filename!r}")
        if info.is_dir():
            continue
        if name in result:
            raise ConsolidationError(f"Duplicate archive member: {name!r}")
        result[name] = info
    return result


def _extract_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo, destination: Path) -> bytes:
    data = archive.read(info)
    _write_bytes(destination, data)
    return data


def _ingest_code_library(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        members = _safe_members(archive, CODE_ARCHIVE_ROOT)
        copied = 0
        skipped_pyc = 0
        python_files = 0
        for name, info in sorted(members.items()):
            relative = name.removeprefix(CODE_ARCHIVE_ROOT)
            if relative.endswith(".pyc"):
                skipped_pyc += 1
                continue
            data = _extract_member(archive, info, VENDOR_ROOT / PurePosixPath(relative))
            copied += 1
            if relative.endswith(".py"):
                python_files += 1
            if not data:
                raise ConsolidationError(f"Empty curated source file: {relative}")

        raw_catalog = archive.read(members[CODE_ARCHIVE_ROOT + "CATALOG.json"])
        _write_bytes(CATALOG_DIR / "raw" / "code-library" / "CATALOG.json", raw_catalog)

    if copied != 56 or python_files != 30 or skipped_pyc != 30:
        raise ConsolidationError(
            f"Unexpected code-library inventory: copied={copied}, py={python_files}, pyc={skipped_pyc}"
        )
    return {
        "archive": path.name,
        "archive_sha256": _sha256(path.read_bytes()),
        "copied_files": copied,
        "python_files": python_files,
        "skipped_pyc": skipped_pyc,
    }


def _ingest_object_library(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    with zipfile.ZipFile(path) as archive:
        members = _safe_members(archive, OBJECT_ARCHIVE_ROOT)
        source_files = 0
        empty_files: list[str] = []
        for name, info in sorted(members.items()):
            if not name.startswith(OBJECT_ARCHIVE_ROOT + "candidates/"):
                continue
            relative = name.removeprefix(OBJECT_ARCHIVE_ROOT + "candidates/")
            data = _extract_member(archive, info, OBJECT_ROOT / PurePosixPath(relative))
            if name.endswith(".py"):
                source_files += 1
                if not data:
                    empty_files.append(relative)

        raw_root = CATALOG_DIR / "raw" / "object-harvest"
        for relative in ("CATALOG.json", "REJECTED.json", "README.md", "SOURCES.md"):
            member = members[OBJECT_ARCHIVE_ROOT + relative]
            _extract_member(archive, member, raw_root / relative)
        for name, info in sorted(members.items()):
            if name.startswith(OBJECT_ARCHIVE_ROOT + "catalog_parts/"):
                relative = name.removeprefix(OBJECT_ARCHIVE_ROOT + "catalog_parts/")
                _extract_member(archive, info, raw_root / "catalog_parts" / PurePosixPath(relative))

        catalog = _load_json_bytes(archive.read(members[OBJECT_CATALOG_MEMBER]), OBJECT_CATALOG_MEMBER)
        sources = archive.read(members[OBJECT_ARCHIVE_ROOT + "SOURCES.md"])
        _write_bytes(LICENSE_ROOT / "OBJECT_HARVEST_SOURCES.md", sources)
        pipe_license = members.get(OBJECT_ARCHIVE_ROOT + "candidates/pipes_generator/LICENSE")
        if pipe_license is not None:
            _extract_member(archive, pipe_license, LICENSE_ROOT / "pipes-generator-LICENSE")

    if source_files != 315:
        raise ConsolidationError(f"Expected 315 object source files, found {source_files}")
    if empty_files:
        raise ConsolidationError(f"Empty object source files: {empty_files[:10]}")
    candidates = catalog.get("candidates")
    if catalog.get("count") != 521 or not isinstance(candidates, list) or len(candidates) != 521:
        raise ConsolidationError("Object catalog does not contain the declared 521 candidates")
    return catalog, {
        "archive": path.name,
        "archive_sha256": _sha256(path.read_bytes()),
        "catalog_entries": len(candidates),
        "python_files": source_files,
        "empty_python_files": len(empty_files),
    }


def _bootstrap_runtime_catalog() -> dict[str, Any]:
    if RUNTIME_CATALOG.is_file():
        return json.loads(RUNTIME_CATALOG.read_text(encoding="utf-8"))
    if not PACKAGE_CATALOG.is_file():
        raise ConsolidationError("Existing runtime catalog is missing")
    raw = json.loads(PACKAGE_CATALOG.read_text(encoding="utf-8"))
    generators = raw.get("generators")
    if not isinstance(generators, list) or not generators:
        raise ConsolidationError("Existing runtime catalog is invalid")
    if any(item.get("catalog_source") == "object-harvest" for item in generators):
        raise ConsolidationError("Cannot bootstrap runtime catalog from an already merged package catalog")
    _write_json(RUNTIME_CATALOG, raw)
    return raw


def _normalize_repository(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    parsed = urlsplit(value)
    if parsed.scheme and parsed.netloc:
        path = parsed.path.rstrip("/")
        if path.lower().endswith(".git"):
            path = path[:-4]
        return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, "", ""))
    return value.rstrip("/")


def _repository_key(value: str | None) -> str:
    return (_normalize_repository(value) or "").casefold()


def _normalize_commit(value: str | None) -> str | None:
    candidate = str(value or "").strip().lower()
    return candidate if re.fullmatch(r"[0-9a-f]{7,40}", candidate) else None


def _slug(value: str) -> str:
    words = re.findall(r"[a-z0-9]+", value.casefold())
    ignored = {"generator", "generators", "library", "blender", "the"}
    words = [word for word in words if word not in ignored]
    return "_".join(words[:3]) or "source"


def _category_for_id(generator_id: str) -> str:
    parts = generator_id.split(".")
    return "/".join(parts[:-1]) if len(parts) > 1 else parts[0]


def _vendor_metadata() -> tuple[dict[str, Any], dict[str, Any]]:
    catalog = json.loads((VENDOR_ROOT / "CATALOG.json").read_text(encoding="utf-8"))
    groups = {item["id"]: item for item in catalog.get("generator_groups", [])}
    index_raw = json.loads((VENDOR_ROOT / "FILE_INDEX.json").read_text(encoding="utf-8"))
    index = {item["file"].replace("\\", "/"): item for item in index_raw}
    return groups, index


def _source_symbols(path: Path, cache: dict[Path, tuple[str, ...]]) -> tuple[str, ...]:
    if path in cache:
        return cache[path]
    try:
        text = path.read_text(encoding="utf-8-sig")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(text, filename=str(path))
    except (OSError, UnicodeDecodeError, SyntaxError):
        cache[path] = ()
        return ()
    result = tuple(
        node.name for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    )
    cache[path] = result
    return result


def _identify_symbol(notes: str, source_path: Path | None, cache: dict[Path, tuple[str, ...]]) -> str | None:
    for pattern in SYMBOL_PATTERNS:
        match = pattern.search(notes)
        if match:
            return match.group(1)
    if source_path is None or not source_path.is_file():
        return None
    symbols = _source_symbols(source_path, cache)
    generator_like = [
        symbol
        for symbol in symbols
        if symbol.endswith("Factory")
        or symbol.lower().startswith(("generate", "create", "make", "build", "add_"))
    ]
    if len(generator_like) == 1:
        return generator_like[0]
    if len(symbols) == 1:
        return symbols[0]
    return None


def _normalize_runtime_entries(raw: dict[str, Any]) -> list[dict[str, Any]]:
    groups, file_index = _vendor_metadata()
    symbol_cache: dict[Path, tuple[str, ...]] = {}
    normalized: list[dict[str, Any]] = []
    for original in raw["generators"]:
        item = dict(original)
        generator_id = str(item["id"])
        status = str(item["status"])
        if status not in VALID_STATUSES:
            raise ConsolidationError(f"Invalid runtime status for {generator_id}: {status}")
        vendor = groups.get(item.get("vendor_group") or "") or {}
        origin = item.get("origin") or {}
        vendor_source = vendor.get("source") or {}
        local_source = (item.get("source_file") or "").replace("\\", "/") or None
        index_key = (local_source or "").removeprefix("vendor/generator_library/")
        indexed = file_index.get(index_key) or {}
        indexed_source = indexed.get("source") or {}
        project = indexed_source.get("project") or vendor_source.get("project") or origin.get("project")
        repository = _normalize_repository(
            indexed_source.get("repo") or vendor_source.get("repo") or origin.get("repo")
        )
        source_revision = indexed_source.get("commit") or vendor_source.get("commit") or origin.get("commit")
        commit = _normalize_commit(source_revision)
        license_id = indexed_source.get("license") or vendor_source.get("license") or origin.get("license")
        if status == "NATIVE":
            project = "TK3D"
            repository = TARGET_REPOSITORY
            license_id = license_id or "MIT"
        source_path = ROOT / local_source if local_source else None
        source_available = bool(source_path and source_path.is_file() and source_path.stat().st_size > 0)
        symbol = item.get("adapter") or NATIVE_SYMBOLS.get(generator_id)
        if not symbol:
            symbol = _identify_symbol(str(item.get("dependency_reason") or ""), source_path, symbol_cache)
        implementation_source = None
        if status == "NATIVE":
            implementation_source = local_source
        elif status == "ADAPTED":
            implementation_source = ADAPTER_IMPLEMENTATIONS.get(str(item.get("adapter") or ""))
        result = {
            "id": generator_id,
            "name": item.get("name") or generator_id,
            "description": item.get("meaning") or item.get("description") or "",
            "meaning": item.get("meaning") or item.get("description") or "",
            "not_this": item.get("not_this"),
            "category": item.get("category") or _category_for_id(generator_id),
            "capability": generator_id,
            "tags": list(item.get("tags") or []),
            "aliases": list(item.get("aliases") or []),
            "variants": list(item.get("variants") or []),
            "status": status,
            "current_tk3d_status": status,
            "backend": item.get("backend"),
            "kind": item.get("kind"),
            "adapter": item.get("adapter"),
            "implementation_source": implementation_source,
            "reuse_difficulty": (
                "native" if status == "NATIVE" else "adapted" if status == "ADAPTED" else "hard"
            ),
            "source_project": project,
            "repository": repository,
            "pinned_commit": commit,
            "source_revision": source_revision if source_revision and not commit else None,
            "license": license_id,
            "upstream_source": index_key if local_source and local_source.startswith("vendor/") else local_source,
            "local_source": local_source,
            "symbol": symbol,
            "source_available": source_available,
            "sha256": _sha256(source_path.read_bytes()) if source_available and source_path else None,
            "runtime": "TK3D" if status in {"NATIVE", "ADAPTED"} else "reference-only",
            "dependencies": [],
            "limitations": item.get("limitations"),
            "dependency_reason": item.get("dependency_reason"),
            "catalog_source": "runtime-curated",
        }
        normalized.append(result)
    return normalized


def _repo_commit_defaults(candidates: Iterable[dict[str, Any]]) -> dict[str, str]:
    values: dict[str, set[str]] = defaultdict(set)
    for item in candidates:
        key = _repository_key(item.get("repo"))
        commit = _normalize_commit(item.get("commit"))
        if key and commit:
            values[key].add(commit)
    return {key: next(iter(commits)) for key, commits in values.items() if len(commits) == 1}


def _object_upstream_path(source_file: str) -> str:
    normalized = source_file.replace("\\", "/")
    if normalized.startswith(("http://", "https://")):
        return normalized
    parts = PurePosixPath(normalized).parts
    if len(parts) >= 3 and parts[0] == "candidates":
        return "/".join(parts[2:])
    return normalized


def _object_local_path(
    source_file: str,
    item: dict[str, Any],
    repository_roots: dict[str, set[str]],
) -> str | None:
    normalized = source_file.replace("\\", "/")
    if normalized.startswith(("http://", "https://")):
        return None
    if not normalized.startswith("candidates/"):
        direct = None
    else:
        direct = "library/objects/" + normalized.removeprefix("candidates/")
        if (ROOT / direct).is_file():
            return direct

    raw_parts = PurePosixPath(normalized).parts
    roots: set[str] = set()
    if len(raw_parts) >= 2 and raw_parts[0] == "candidates":
        roots.add(raw_parts[1])
    roots.update(repository_roots.get(_repository_key(item.get("repo")), set()))
    if not roots:
        return None
    python_files = sorted(
        path
        for root_name in roots
        for path in (OBJECT_ROOT / root_name).rglob("*.py")
        if (OBJECT_ROOT / root_name).is_dir()
    )
    basename = raw_parts[-1].casefold() if raw_parts else ""
    if basename.endswith(".py"):
        suffix_length = 1 if len(raw_parts) == 1 else 2
        raw_suffix = tuple(part.casefold() for part in raw_parts[-suffix_length:])
        same_suffix = [
            path
            for path in python_files
            if tuple(part.casefold() for part in path.parts[-suffix_length:]) == raw_suffix
        ]
        if len(same_suffix) == 1:
            return same_suffix[0].relative_to(ROOT).as_posix()
        return None

    direct_directory = ROOT / direct if direct else None
    if direct_directory is None or not direct_directory.is_dir():
        return None
    python_files = sorted(direct_directory.rglob("*.py"))

    tokens = {
        token
        for token in re.findall(
            r"[a-z0-9]+",
            " ".join(
                [
                    str(item.get("id") or ""),
                    str(item.get("name") or ""),
                    " ".join(item.get("tags") or []),
                ]
            ).casefold(),
        )
        if len(token) >= 3 and token not in {"prop", "object", "generator", "infinigen"}
    }
    ranked: list[tuple[int, Path]] = []
    for path in python_files:
        stem = path.stem.casefold()
        score = sum(2 for token in tokens if token == stem or token in stem or stem in token)
        if score:
            ranked.append((score, path))
    ranked.sort(key=lambda pair: (-pair[0], pair[1].as_posix()))
    if ranked and (len(ranked) == 1 or ranked[0][0] > ranked[1][0]):
        return ranked[0][1].relative_to(ROOT).as_posix()
    return None


def _normalize_object_entries(
    candidates: list[dict[str, Any]], used_ids: set[str]
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    commit_defaults = _repo_commit_defaults(candidates)
    repository_roots: dict[str, set[str]] = defaultdict(set)
    for candidate in candidates:
        source = str(candidate.get("source_file") or "").replace("\\", "/")
        parts = PurePosixPath(source).parts
        if len(parts) >= 2 and parts[0] == "candidates":
            repository_roots[_repository_key(candidate.get("repo"))].add(parts[1])
    symbol_cache: dict[Path, tuple[str, ...]] = {}
    normalized: list[dict[str, Any]] = []
    remaps: list[dict[str, str]] = []
    for original in candidates:
        harvest_id = str(original["id"])
        generator_id = harvest_id
        if generator_id in used_ids:
            base = f"{harvest_id}.{_slug(str(original.get('source_project') or original.get('repo') or 'source'))}"
            generator_id = base
            suffix = 2
            while generator_id in used_ids:
                generator_id = f"{base}_{suffix}"
                suffix += 1
            remaps.append({"harvest_id": harvest_id, "merged_id": generator_id})
        used_ids.add(generator_id)

        original_source = str(original.get("source_file") or "")
        local_source = _object_local_path(original_source, original, repository_roots)
        source_path = ROOT / local_source if local_source else None
        source_available = bool(source_path and source_path.is_file() and source_path.stat().st_size > 0)
        notes = str(original.get("notes") or "")
        symbol = _identify_symbol(notes, source_path, symbol_cache)
        repository = _normalize_repository(original.get("repo"))
        source_revision = str(original.get("commit") or "").strip() or None
        explicit_commit = _normalize_commit(source_revision)
        inferred_commit = None if explicit_commit else commit_defaults.get(_repository_key(repository))
        result = {
            "id": generator_id,
            "original_id": harvest_id if generator_id != harvest_id else None,
            "name": original.get("name") or generator_id,
            "description": original.get("description") or "",
            "meaning": original.get("description") or "",
            "not_this": None,
            "category": original.get("category") or _category_for_id(harvest_id),
            "capability": harvest_id,
            "tags": list(original.get("tags") or []),
            "aliases": [harvest_id] if generator_id != harvest_id else [],
            "variants": list(original.get("variants") or []),
            "status": "REFERENCE",
            "current_tk3d_status": "REFERENCE",
            "backend": "object-harvest",
            "kind": None,
            "adapter": None,
            "implementation_source": None,
            "reuse_difficulty": str(original.get("estimated_reuse") or "unknown").lower(),
            "source_project": original.get("source_project"),
            "repository": repository,
            "pinned_commit": explicit_commit or inferred_commit,
            "source_revision": source_revision if source_revision and not explicit_commit else None,
            "commit_inferred": bool(inferred_commit),
            "license": original.get("license"),
            "upstream_source": _object_upstream_path(original_source),
            "harvest_source": original_source,
            "local_source": local_source,
            "symbol": symbol,
            "source_available": source_available,
            "sha256": _sha256(source_path.read_bytes()) if source_available and source_path else None,
            "language": original.get("language"),
            "runtime": original.get("runtime"),
            "dependencies": list(original.get("dependencies") or []),
            "limitations": "Reference source only; not registered as a TK3D runtime builder.",
            "dependency_reason": notes or None,
            "catalog_source": "object-harvest",
        }
        normalized.append(result)
    return normalized, remaps


def _deduplicate(entries: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Remove only provenance-identical duplicates of the same semantic capability."""
    seen: dict[tuple[str, str, str, str, str], str] = {}
    kept: list[dict[str, Any]] = []
    removed: list[dict[str, str]] = []
    for entry in entries:
        key = (
            _repository_key(entry.get("repository")),
            str(entry.get("pinned_commit") or "").casefold(),
            str(entry.get("upstream_source") or "").casefold(),
            str(entry.get("symbol") or "").casefold(),
            str(entry.get("capability") or entry["id"]).casefold(),
        )
        if all(key[:3]) and key in seen:
            removed.append({"removed_id": entry["id"], "kept_id": seen[key]})
            continue
        seen[key] = entry["id"]
        kept.append(entry)
    return kept, removed


def _source_catalog(entries: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, dict[str, Any]] = {}
    for entry in entries:
        repository = entry.get("repository")
        key = _repository_key(repository)
        if not key:
            continue
        record = grouped.setdefault(
            key,
            {
                "repository": repository,
                "projects": set(),
                "pinned_commits": set(),
                "licenses": set(),
                "entry_ids": [],
                "local_sources": set(),
            },
        )
        if entry.get("source_project"):
            record["projects"].add(entry["source_project"])
        if entry.get("pinned_commit"):
            record["pinned_commits"].add(entry["pinned_commit"])
        if entry.get("license"):
            record["licenses"].add(entry["license"])
        record["entry_ids"].append(entry["id"])
        if entry.get("source_available") and entry.get("local_source"):
            record["local_sources"].add(entry["local_source"])
    sources = []
    for key in sorted(grouped):
        record = grouped[key]
        entry_ids = sorted(record["entry_ids"])
        sources.append(
            {
                "repository": record["repository"],
                "projects": sorted(record["projects"]),
                "pinned_commits": sorted(record["pinned_commits"]),
                "licenses": sorted(record["licenses"]),
                "entries": len(entry_ids),
                "local_source_files": len(record["local_sources"]),
                "entry_ids": entry_ids,
            }
        )
    return {"format_version": 1, "project": "TK3D", "sources": sources}


def _validate(entries: list[dict[str, Any]], remaps: list[dict[str, str]], removed: list[dict[str, str]]) -> dict[str, Any]:
    ids = [entry["id"] for entry in entries]
    duplicate_ids = sorted({generator_id for generator_id in ids if ids.count(generator_id) > 1})
    broken_sources: list[str] = []
    empty_sources: list[str] = []
    hash_mismatches: list[str] = []
    for entry in entries:
        local = entry.get("local_source")
        if not local:
            continue
        path = (ROOT / local).resolve()
        try:
            path.relative_to(ROOT.resolve())
        except ValueError:
            broken_sources.append(entry["id"])
            continue
        if not path.is_file():
            broken_sources.append(entry["id"])
            continue
        if path.stat().st_size == 0:
            empty_sources.append(entry["id"])
        expected = entry.get("sha256")
        if expected and _sha256(path.read_bytes()) != expected:
            hash_mismatches.append(entry["id"])

    status_counts = {status: 0 for status in VALID_STATUSES}
    for entry in entries:
        status = entry.get("status")
        if status not in status_counts:
            raise ConsolidationError(f"Invalid merged status: {status!r}")
        status_counts[status] += 1

    local_source_files = {entry["local_source"] for entry in entries if entry.get("source_available")}
    upstream_repositories = {
        _repository_key(entry.get("repository"))
        for entry in entries
        if entry.get("repository") and entry.get("repository") != TARGET_REPOSITORY
    }
    missing_license = sorted(entry["id"] for entry in entries if not entry.get("license"))
    missing_repository = sorted(
        entry["id"]
        for entry in entries
        if entry["catalog_source"] == "object-harvest" and not entry.get("repository")
    )
    missing_commit = sorted(
        entry["id"]
        for entry in entries
        if entry["catalog_source"] == "object-harvest"
        and entry.get("repository")
        and not entry.get("pinned_commit")
    )
    integrity = {
        "status": "PASS"
        if not (duplicate_ids or broken_sources or empty_sources or hash_mismatches or missing_license or missing_repository)
        else "FAIL",
        "total_entries": len(entries),
        "status_counts": status_counts,
        "catalog_local_source_files": len(local_source_files),
        "curated_python_files": len(list(VENDOR_ROOT.rglob("*.py"))),
        "object_python_files": len(list(OBJECT_ROOT.rglob("*.py"))),
        "library_python_files": len(list(VENDOR_ROOT.rglob("*.py"))) + len(list(OBJECT_ROOT.rglob("*.py"))),
        "unique_upstream_repositories": len(upstream_repositories),
        "remote_only_entries": sum(1 for entry in entries if not entry.get("source_available")),
        "unavailable_source_entries": sum(1 for entry in entries if not entry.get("source_available")),
        "identified_symbols": sum(1 for entry in entries if entry.get("symbol")),
        "missing_pinned_commit_count": len(missing_commit),
        "missing_pinned_commit_ids": missing_commit,
        "missing_license_ids": missing_license,
        "missing_repository_ids": missing_repository,
        "broken_local_source_ids": sorted(set(broken_sources)),
        "empty_local_source_ids": sorted(set(empty_sources)),
        "hash_mismatch_ids": sorted(set(hash_mismatches)),
        "duplicate_ids": duplicate_ids,
        "id_remaps": remaps,
        "deduplicated_entries": removed,
    }
    return integrity


def _copy_curated_licenses() -> None:
    source = VENDOR_ROOT / "_licenses"
    for path in sorted(source.glob("*.txt")):
        destination = LICENSE_ROOT / "code-library" / path.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)


def consolidate(code_archive: Path, object_archive: Path) -> dict[str, Any]:
    for path in (code_archive, object_archive):
        if not path.is_file():
            raise ConsolidationError(f"Archive not found: {path}")

    code_stats = _ingest_code_library(code_archive)
    object_raw, object_stats = _ingest_object_library(object_archive)
    runtime_raw = _bootstrap_runtime_catalog()
    runtime_entries = _normalize_runtime_entries(runtime_raw)
    used_ids = {entry["id"] for entry in runtime_entries}
    object_entries, remaps = _normalize_object_entries(object_raw["candidates"], used_ids)
    entries, removed = _deduplicate(runtime_entries + object_entries)
    entries.sort(key=lambda entry: entry["id"])

    merged = {
        "format_version": 2,
        "project": "TK3D",
        "policy": "NATIVE and ADAPTED are executable; REFERENCE and UNSUPPORTED are never runtime imports.",
        "generators": entries,
    }
    integrity = _validate(entries, remaps, removed)
    if integrity["status"] != "PASS":
        raise ConsolidationError(json.dumps(integrity, ensure_ascii=False))

    _write_json(CANONICAL_CATALOG, merged)
    _write_json(PACKAGE_CATALOG, merged)
    _write_json(CATALOG_DIR / "sources.json", _source_catalog(entries))
    _write_json(CATALOG_DIR / "integrity.json", integrity)
    _write_json(
        CATALOG_DIR / "archive-manifest.json",
        {"format_version": 1, "project": "TK3D", "archives": [code_stats, object_stats]},
    )
    _copy_curated_licenses()
    return integrity


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("code_archive", type=Path)
    parser.add_argument("object_archive", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = consolidate(args.code_archive.resolve(), args.object_archive.resolve())
    except (ConsolidationError, OSError, zipfile.BadZipFile) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

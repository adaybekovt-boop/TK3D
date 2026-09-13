from __future__ import annotations

from pathlib import Path


def package_dir() -> Path:
    return Path(__file__).resolve().parent


def repo_root() -> Path:
    """Repository root when running from a source checkout or editable install."""
    return package_dir().parents[1]


def vendor_library_root() -> Path:
    return repo_root() / "vendor" / "generator_library"


def object_library_root() -> Path:
    return repo_root() / "library" / "objects"


def catalogs_root() -> Path:
    return repo_root() / "catalogs"


def catalog_json_path() -> Path:
    canonical = catalogs_root() / "generators.json"
    if canonical.is_file():
        return canonical
    return package_dir() / "catalog" / "generators.json"

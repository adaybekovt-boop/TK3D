from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import bpy

from geoforge.scene import remove_object_and_data


ROOT = Path(__file__).resolve().parents[2]
TEST_OUTPUT_ROOT = ROOT / ".test-output"
TEST_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)


def simple_scene(entities: list[dict], *, scene_id: str = "blender_test") -> dict:
    return {
        "schema_version": "1.0",
        "scene_id": scene_id,
        "seed": 12345,
        "units": "m",
        "entities": entities,
        "quality": {"profile": "production", "min_feature_size": 0.02},
        "output": {
            "save_blend": False,
            "blend": "test.blend",
            "report": "build-report.json",
            "manifest": "build-manifest.json",
        },
    }


def room_entity(*, opening_kind: str = "door") -> dict:
    opening = {
        "id": f"{opening_kind}.main",
        "kind": opening_kind,
        "wall": "south",
        "offset": 3.0,
        "width": 1.0,
        "height": 1.2 if opening_kind == "window" else 2.1,
    }
    if opening_kind == "window":
        opening["bottom"] = 0.9
    return {
        "id": "room.main",
        "kind": "room",
        "transform": {"position": [1.0, 2.0, 0.0], "yaw_deg": 15.0},
        "params": {
            "width": 8.0,
            "length": 10.0,
            "height": 3.2,
            "wall_thickness": 0.2,
            "floor_thickness": 0.2,
            "ceiling": True,
            "openings": [opening],
        },
    }


def box_entity(entity_id: str = "box.main") -> dict:
    return {
        "id": entity_id,
        "kind": "box",
        "params": {"width": 2.0, "depth": 3.0, "height": 4.0},
    }


def cleanup_generated() -> None:
    collections = [collection for collection in bpy.data.collections if collection.name.startswith("GF_")]
    objects = {obj for collection in collections for obj in collection.objects}
    for obj in objects:
        if obj.name in bpy.data.objects:
            remove_object_and_data(obj)
    for collection in collections:
        if collection.name in bpy.data.collections:
            bpy.data.collections.remove(collection)


def staging_collections() -> list[bpy.types.Collection]:
    return [collection for collection in bpy.data.collections if collection.name.startswith("GF_STAGING_")]


class WorkspaceTemporaryDirectory:
    """Temporary output directory without tempfile's Windows 0o700 ACL.

    Python 3.12's ``tempfile`` deliberately creates private directories on
    Windows.  A sandboxed Blender subprocess can create such a directory but
    subsequently lose access to it because its restricted token does not match
    the owner-only ACL.  Test output is non-sensitive, so an ordinary inherited
    workspace ACL is the correct behavior here.
    """

    def __init__(self) -> None:
        path = TEST_OUTPUT_ROOT / f"run-{uuid.uuid4().hex}"
        path.mkdir(parents=False, exist_ok=False)
        self.name = str(path)

    def cleanup(self) -> None:
        shutil.rmtree(self.name, ignore_errors=True)

    def __enter__(self) -> str:
        return self.name

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.cleanup()


def temporary_directory() -> WorkspaceTemporaryDirectory:
    return WorkspaceTemporaryDirectory()

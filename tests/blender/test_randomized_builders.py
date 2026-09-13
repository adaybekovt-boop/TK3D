from __future__ import annotations

import math
import random
import unittest

import bpy

from geoforge.operations.transaction import StagingTransaction
from geoforge.pipeline import compile_drafts
from geoforge.quality.mesh import validate_contacts, validate_materialized
from geoforge.spec import decode_scene_spec
from tests.blender.support import cleanup_generated, staging_collections


def _scene(entity: dict, case: int) -> dict:
    return {
        "schema_version": "1.0",
        "scene_id": f"blender_fuzz_{case}",
        "seed": 700_000 + case,
        "units": "m",
        "entities": [entity],
        "quality": {"profile": "production", "min_feature_size": 0.01},
    }


class RandomizedBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        cleanup_generated()

    def tearDown(self) -> None:
        cleanup_generated()

    def _assert_materialized_pass(self, entity: dict, case: int) -> None:
        spec = decode_scene_spec(_scene(entity, case))
        first = compile_drafts(spec)
        second = compile_drafts(spec)
        self.assertEqual(
            [artifact.draft.fingerprint() for artifact in first.artifacts],
            [artifact.draft.fingerprint() for artifact in second.artifacts],
        )
        transaction = StagingTransaction()
        try:
            materialized = [transaction.materialize(artifact) for artifact in first.artifacts]
            for item in materialized:
                report = validate_materialized(item)
                self.assertEqual(report.status, "PASS", report.compact_dict())
                self.assertEqual(item.artifact.draft.bounds, item.artifact.contract.local_bounds)
                self.assertEqual(item.artifact.draft.bounds.dimensions, item.artifact.contract.dimensions)
            contacts = validate_contacts(materialized, first.contacts)
            self.assertEqual(contacts.status, "PASS", contacts.compact_dict())
        finally:
            transaction.rollback()

    def _room(self, rng: random.Random, opening_kind: str, case: int) -> dict:
        width = rng.uniform(3.0, 50.0)
        length = rng.uniform(3.0, 50.0)
        height = rng.uniform(2.4, 5.5)
        wall = rng.choice(("south", "north", "west", "east"))
        wall_length = width if wall in {"south", "north"} else length
        opening_width = rng.uniform(0.65, min(2.5, wall_length * 0.4))
        offset = rng.uniform(opening_width * 0.5 + 0.1, wall_length - opening_width * 0.5 - 0.1)
        opening = {
            "id": f"{opening_kind}.main",
            "kind": opening_kind,
            "wall": wall,
            "offset": offset,
            "width": opening_width,
        }
        if opening_kind == "door":
            opening["height"] = rng.uniform(1.8, min(2.5, height - 0.1))
        else:
            bottom = rng.uniform(0.35, min(1.3, height - 0.7))
            opening.update(
                {
                    "bottom": bottom,
                    "height": rng.uniform(0.5, height - bottom - 0.1),
                }
            )
        return {
            "id": "room.random",
            "kind": "room",
            "transform": {
                "position": [rng.uniform(-25.0, 25.0), rng.uniform(-25.0, 25.0), rng.uniform(-2.0, 2.0)],
                "yaw_deg": rng.uniform(-180.0, 180.0),
            },
            "params": {
                "width": width,
                "length": length,
                "height": height,
                "wall_thickness": rng.uniform(0.08, 0.4),
                "floor_thickness": rng.uniform(0.08, 0.35),
                "ceiling": bool(case % 2),
                "openings": [opening],
            },
        }

    def test_100_rooms_with_doors_materialize_and_pass_bmesh_qa(self) -> None:
        rng = random.Random(8101)
        object_count = len(bpy.data.objects)
        mesh_count = len(bpy.data.meshes)
        for case in range(100):
            self._assert_materialized_pass(self._room(rng, "door", case), case)
        self.assertEqual(len(bpy.data.objects), object_count)
        self.assertEqual(len(bpy.data.meshes), mesh_count)
        self.assertFalse(staging_collections())

    def test_100_rooms_with_windows_materialize_and_pass_bmesh_qa(self) -> None:
        rng = random.Random(8102)
        object_count = len(bpy.data.objects)
        mesh_count = len(bpy.data.meshes)
        for case in range(100):
            self._assert_materialized_pass(self._room(rng, "window", case), 1000 + case)
        self.assertEqual(len(bpy.data.objects), object_count)
        self.assertEqual(len(bpy.data.meshes), mesh_count)
        self.assertFalse(staging_collections())

    def test_100_stairs_materialize_and_pass_bmesh_qa(self) -> None:
        rng = random.Random(8103)
        object_count = len(bpy.data.objects)
        mesh_count = len(bpy.data.meshes)
        for case in range(100):
            rise = rng.uniform(0.5, 5.0)
            max_riser = rng.uniform(0.15, 0.23)
            risers = max(1, math.ceil(rise / max_riser))
            min_tread = rng.uniform(0.18, 0.3)
            entity = {
                "id": "stairs.random",
                "kind": "straight_stairs",
                "transform": {
                    "position": [rng.uniform(-10.0, 10.0), rng.uniform(-10.0, 10.0), rng.uniform(-1.0, 1.0)],
                    "yaw_deg": rng.uniform(-180.0, 180.0),
                },
                "params": {
                    "width": rng.uniform(0.7, 2.5),
                    "run": risers * rng.uniform(min_tread, 0.45),
                    "rise": rise,
                    "max_riser": max_riser,
                    "min_tread": min_tread,
                },
            }
            self._assert_materialized_pass(entity, 2000 + case)
        self.assertEqual(len(bpy.data.objects), object_count)
        self.assertEqual(len(bpy.data.meshes), mesh_count)
        self.assertFalse(staging_collections())


if __name__ == "__main__":
    unittest.main()

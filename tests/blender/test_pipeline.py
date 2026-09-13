from __future__ import annotations

import json
import unittest
from pathlib import Path

import bpy

from geoforge.api import regenerate_entity
from geoforge.pipeline import compile_scene
from geoforge.spec import decode_scene_spec
from tests.blender.support import box_entity, cleanup_generated, room_entity, simple_scene, staging_collections, temporary_directory


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        cleanup_generated()

    def tearDown(self) -> None:
        cleanup_generated()

    def _compile(self, entities: list[dict]):
        temporary = temporary_directory()
        self.addCleanup(temporary.cleanup)
        spec = decode_scene_spec(simple_scene(entities))
        result = compile_scene(spec, output_root=temporary.name)
        return spec, result, Path(temporary.name)

    def test_room_with_door_commits_and_writes_outputs(self) -> None:
        spec, result, output = self._compile([room_entity(opening_kind="door")])
        self.assertTrue(result.ok, result.report.full_dict())
        self.assertFalse(staging_collections())
        final = bpy.data.collections.get("GF_FINAL")
        self.assertIsNotNone(final)
        self.assertEqual(len(final.objects), 8)
        for obj in final.objects:
            self.assertEqual(tuple(obj.scale), (1.0, 1.0, 1.0))
            self.assertEqual(obj["gf_entity_id"], "room.main")
            self.assertIn("gf_mesh_fingerprint", obj)
            self.assertEqual(obj["gf_spec_hash"], spec.spec_hash)
        self.assertTrue((output / spec.output.report).is_file())
        self.assertTrue((output / spec.output.manifest).is_file())
        manifest = json.loads((output / spec.output.manifest).read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "PASS")
        self.assertTrue(all(item["published"] for item in manifest["artifacts"]))

    def test_room_with_window_passes(self) -> None:
        _, result, _ = self._compile([room_entity(opening_kind="window")])
        self.assertTrue(result.ok, result.report.full_dict())
        self.assertGreaterEqual(len(result.report.committed_objects), 9)

    def test_large_room_with_door_and_window_float32_bounds_regression(self) -> None:
        room = room_entity()
        room["params"].update({"width": 12.0, "length": 20.0, "wall_thickness": 0.18})
        room["params"]["openings"] = [
            room["params"]["openings"][0],
            {
                "id": "window.east",
                "kind": "window",
                "wall": "east",
                "offset": 8.0,
                "width": 1.8,
                "height": 1.2,
                "bottom": 0.9,
            },
        ]
        _, result, _ = self._compile([room])
        self.assertTrue(result.ok, result.report.full_dict())

    def test_stairs_beam_and_column_pass(self) -> None:
        entities = [
            {
                "id": "stairs.main",
                "kind": "straight_stairs",
                "params": {"width": 1.2, "run": 4.2, "rise": 3.2, "max_riser": 0.18, "min_tread": 0.2},
            },
            {"id": "beam.main", "kind": "beam", "params": {"length": 4.0, "width": 0.2, "height": 0.3}},
            {"id": "column.main", "kind": "column", "params": {"width": 0.3, "depth": 0.3, "height": 3.2}},
        ]
        _, result, _ = self._compile(entities)
        self.assertTrue(result.ok, result.report.full_dict())
        self.assertEqual(len(result.report.committed_objects), 3)

    def test_standalone_box_wall_floor_and_ceiling_pass(self) -> None:
        entities = [
            box_entity(),
            {
                "id": "wall.main",
                "kind": "wall",
                "params": {
                    "length": 10.0,
                    "height": 3.2,
                    "thickness": 0.2,
                    "openings": [
                        {"id": "door", "kind": "door", "offset": 2.0, "width": 1.0, "height": 2.1},
                        {
                            "id": "window",
                            "kind": "window",
                            "offset": 6.0,
                            "width": 1.8,
                            "height": 1.2,
                            "bottom": 0.9,
                        },
                    ],
                },
            },
            {"id": "floor.main", "kind": "floor", "params": {"width": 4.0, "length": 5.0, "thickness": 0.2}},
            {
                "id": "ceiling.main",
                "kind": "ceiling",
                "transform": {"position": [0.0, 0.0, 3.0]},
                "params": {"width": 4.0, "length": 5.0, "thickness": 0.2},
            },
        ]
        _, result, _ = self._compile(entities)
        self.assertTrue(result.ok, result.report.full_dict())
        self.assertEqual({item.builder_id for item in result.manifest.artifacts}, {"box", "wall", "floor", "ceiling"})

    def test_repeated_build_replaces_objects_without_growth(self) -> None:
        temporary = temporary_directory()
        self.addCleanup(temporary.cleanup)
        spec = decode_scene_spec(simple_scene([room_entity()]))
        first = compile_scene(spec, output_root=temporary.name)
        first_fingerprints = [item.mesh_fingerprint for item in first.manifest.artifacts]
        first_count = len(bpy.data.collections["GF_FINAL"].objects)
        first_mesh_count = len(bpy.data.meshes)
        second = compile_scene(spec, output_root=temporary.name)
        self.assertTrue(first.ok and second.ok)
        self.assertEqual(first_fingerprints, [item.mesh_fingerprint for item in second.manifest.artifacts])
        self.assertEqual(len(bpy.data.collections["GF_FINAL"].objects), first_count)
        self.assertEqual(len(bpy.data.meshes), first_mesh_count)
        self.assertFalse(staging_collections())

    def test_failed_minimum_feature_quality_gate_publishes_nothing(self) -> None:
        temporary = temporary_directory()
        self.addCleanup(temporary.cleanup)
        data = simple_scene([box_entity("box.tiny")])
        data["entities"][0]["params"]["width"] = 0.005
        result = compile_scene(decode_scene_spec(data), output_root=temporary.name)
        self.assertFalse(result.ok)
        self.assertIn("GEOM.FEATURE_TOO_SMALL", result.report.compact_dict()["issue_counts"])
        final = bpy.data.collections.get("GF_FINAL")
        self.assertTrue(final is None or len(final.objects) == 0)
        self.assertFalse(staging_collections())
        self.assertTrue(all(not artifact.published for artifact in result.manifest.artifacts))

    def test_regenerate_entity_replaces_only_selected_entity(self) -> None:
        temporary = temporary_directory()
        self.addCleanup(temporary.cleanup)
        original_data = simple_scene([box_entity("box.a"), box_entity("box.b")])
        original = compile_scene(decode_scene_spec(original_data), output_root=temporary.name)
        self.assertTrue(original.ok)
        final = bpy.data.collections["GF_FINAL"]
        before = {obj["gf_entity_id"]: (obj.as_pointer(), obj["gf_mesh_fingerprint"]) for obj in final.objects}

        changed_data = simple_scene([box_entity("box.a"), box_entity("box.b")])
        changed_data["entities"][0]["params"]["width"] = 4.0
        changed = regenerate_entity(
            decode_scene_spec(changed_data),
            "box.a",
            output_root=temporary.name,
        )
        self.assertTrue(changed.ok, changed.report.full_dict())
        after = {obj["gf_entity_id"]: (obj.as_pointer(), obj["gf_mesh_fingerprint"]) for obj in final.objects}
        self.assertEqual(after["box.b"], before["box.b"])
        self.assertNotEqual(after["box.a"], before["box.a"])
        self.assertEqual(len(final.objects), 2)


if __name__ == "__main__":
    unittest.main()

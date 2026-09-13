from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

from geoforge.errors import SpecError, UnsupportedFeatureError
from geoforge.spec import RoomParams, decode_scene_spec
from tests.common import clone, valid_room_scene


ROOT = Path(__file__).resolve().parents[2]


class SceneSpecTests(unittest.TestCase):
    def test_decodes_and_normalizes_valid_room(self) -> None:
        spec = decode_scene_spec(valid_room_scene())
        self.assertEqual(spec.units, "m")
        self.assertEqual(spec.schema_version, "1.0")
        self.assertEqual(len(spec.entities), 1)
        self.assertIsInstance(spec.entities[0].params, RoomParams)
        self.assertEqual(len(spec.spec_hash), 64)

    def test_rejects_unknown_top_level_field(self) -> None:
        data = valid_room_scene()
        data["surprise"] = True
        with self.assertRaises(SpecError) as caught:
            decode_scene_spec(data)
        self.assertEqual(caught.exception.code, "SPEC.UNKNOWN_FIELD")

    def test_rejects_unknown_param_field(self) -> None:
        data = valid_room_scene()
        data["entities"][0]["params"]["magic"] = 1
        with self.assertRaises(SpecError) as caught:
            decode_scene_spec(data)
        self.assertEqual(caught.exception.code, "SPEC.UNKNOWN_FIELD")

    def test_rejects_unsupported_kind(self) -> None:
        data = valid_room_scene()
        data["entities"][0]["kind"] = "terrain"
        with self.assertRaises(UnsupportedFeatureError) as caught:
            decode_scene_spec(data)
        self.assertEqual(caught.exception.code, "SPEC.UNSUPPORTED_FEATURE")

    def test_rejects_unsupported_schema_version(self) -> None:
        data = valid_room_scene()
        data["schema_version"] = "2.0"
        with self.assertRaises(UnsupportedFeatureError) as caught:
            decode_scene_spec(data)
        self.assertEqual(caught.exception.code, "SPEC.UNSUPPORTED_FEATURE")

    def test_rejects_unimplemented_quality_profile(self) -> None:
        data = valid_room_scene()
        data["quality"]["profile"] = "draft"
        with self.assertRaises(UnsupportedFeatureError) as caught:
            decode_scene_spec(data)
        self.assertEqual(caught.exception.code, "SPEC.UNSUPPORTED_FEATURE")

    def test_rejects_duplicate_entity_ids(self) -> None:
        data = valid_room_scene()
        data["entities"].append(clone(data["entities"][0]))
        with self.assertRaises(SpecError) as caught:
            decode_scene_spec(data)
        self.assertEqual(caught.exception.code, "SPEC.DUPLICATE_ENTITY_ID")

    def test_units_normalize_to_equivalent_hash(self) -> None:
        meters = {
            "schema_version": "1.0",
            "scene_id": "units",
            "seed": 7,
            "units": "m",
            "entities": [{"id": "a", "kind": "box", "params": {"width": 1, "depth": 2, "height": 3}}],
            "quality": {"min_feature_size": 0.01},
        }
        centimeters = clone(meters)
        centimeters["units"] = "cm"
        centimeters["entities"][0]["params"] = {"width": 100, "depth": 200, "height": 300}
        centimeters["quality"]["min_feature_size"] = 1
        self.assertEqual(decode_scene_spec(meters).spec_hash, decode_scene_spec(centimeters).spec_hash)

    def test_rejects_opening_outside_wall(self) -> None:
        data = valid_room_scene()
        data["entities"][0]["params"]["openings"][0]["offset"] = 0.1
        with self.assertRaises(SpecError) as caught:
            decode_scene_spec(data)
        self.assertEqual(caught.exception.code, "SPEC.OPENING_OUT_OF_BOUNDS")

    def test_window_requires_bottom(self) -> None:
        data = valid_room_scene()
        opening = data["entities"][0]["params"]["openings"][0]
        opening["kind"] = "window"
        with self.assertRaises(SpecError):
            decode_scene_spec(data)

    def test_rejects_overlapping_openings(self) -> None:
        data = valid_room_scene()
        data["entities"][0]["params"]["openings"].append(
            {
                "id": "door.overlap",
                "kind": "door",
                "wall": "south",
                "offset": 3.2,
                "width": 1.0,
                "height": 2.0,
            }
        )
        with self.assertRaises(SpecError) as caught:
            decode_scene_spec(data)
        self.assertEqual(caught.exception.code, "SPEC.OVERLAPPING_OPENINGS")

    def test_rejects_infeasible_stairs(self) -> None:
        data = valid_room_scene()
        data["entities"] = [
            {
                "id": "stairs",
                "kind": "straight_stairs",
                "params": {"width": 1, "run": 1, "rise": 4, "max_riser": 0.2, "min_tread": 0.2},
            }
        ]
        with self.assertRaises(SpecError) as caught:
            decode_scene_spec(data)
        self.assertEqual(caught.exception.code, "SPEC.INFEASIBLE_STAIRS")

    def test_rejects_non_finite_number(self) -> None:
        data = valid_room_scene()
        data["entities"][0]["params"]["width"] = math.inf
        with self.assertRaises(SpecError) as caught:
            decode_scene_spec(data)
        self.assertEqual(caught.exception.code, "SPEC.NON_FINITE_NUMBER")

    def test_rejects_unsafe_output_path(self) -> None:
        data = valid_room_scene()
        data["output"]["report"] = "../report.json"
        with self.assertRaises(SpecError) as caught:
            decode_scene_spec(data)
        self.assertEqual(caught.exception.code, "SPEC.UNSAFE_PATH")

    def test_rejects_colliding_output_paths(self) -> None:
        data = valid_room_scene()
        data["output"]["manifest"] = data["output"]["report"]
        with self.assertRaises(SpecError) as caught:
            decode_scene_spec(data)
        self.assertEqual(caught.exception.code, "SPEC.OUTPUT_PATH_COLLISION")

    def test_bundled_schema_is_valid_json(self) -> None:
        schema = json.loads((ROOT / "schemas" / "scene-1.0.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["$defs"]["roomEntity"]["properties"]["kind"]["const"], "room")


if __name__ == "__main__":
    unittest.main()

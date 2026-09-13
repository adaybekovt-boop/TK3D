from __future__ import annotations

import unittest

from geoforge.errors import SpecError
from geoforge.pipeline import compile_drafts
from geoforge.spec import ExtensionParams, decode_scene_spec


def scene(entity: dict, seed: int = 9) -> dict:
    return {
        "schema_version": "1.0",
        "scene_id": f"adapter_{entity['kind']}",
        "seed": seed,
        "units": "m",
        "entities": [entity],
        "quality": {"profile": "production", "min_feature_size": 0.01},
    }


class AdapterDraftTests(unittest.TestCase):
    def _compile(self, entity: dict):
        spec = decode_scene_spec(scene(entity))
        first = compile_drafts(spec)
        second = compile_drafts(spec)
        self.assertEqual(
            [item.draft.fingerprint() for item in first.artifacts],
            [item.draft.fingerprint() for item in second.artifacts],
        )
        for artifact in first.artifacts:
            self.assertEqual(artifact.draft.check(), ())
            self.assertGreater(artifact.draft.signed_volume(), 0.0)
        return first

    def test_climbable_ladder_drafts(self) -> None:
        result = self._compile(
            {
                "id": "ladder.main",
                "kind": "climbable_ladder",
                "params": {"height": 3.0, "width": 0.4, "lean_deg": 14.0},
            }
        )
        parts = {item.part for item in result.artifacts}
        self.assertIn("rail.L", parts)
        self.assertIn("rail.R", parts)
        self.assertTrue(any(part.startswith("rung.") for part in parts))
        self.assertTrue(result.contacts)
        spec = decode_scene_spec(
            scene({"id": "ladder.main", "kind": "climbable_ladder", "params": {"height": 3.0, "width": 0.4}})
        )
        self.assertIsInstance(spec.entities[0].params, ExtensionParams)

    def test_railing_balcony_road_desk_drafts(self) -> None:
        cases = [
            {"id": "rail.main", "kind": "railing", "params": {"length": 2.0, "height": 1.0, "fill": "posts"}},
            {"id": "rail.wall", "kind": "railing", "params": {"length": 2.0, "height": 1.0, "fill": "wall"}},
            {"id": "balc.main", "kind": "balcony", "params": {"width": 2.4, "depth": 1.2, "has_railing": True}},
            {"id": "road.main", "kind": "road", "params": {"length": 12.0, "width": 6.0, "sidewalks": True}},
            {"id": "desk.main", "kind": "desk", "params": {"width": 1.4, "depth": 0.7, "height": 0.75}},
        ]
        for entity in cases:
            with self.subTest(kind=entity["kind"], id=entity["id"]):
                result = self._compile(entity)
                self.assertGreaterEqual(len(result.artifacts), 1)

    def test_rejects_infeasible_ladder(self) -> None:
        with self.assertRaises(SpecError) as caught:
            decode_scene_spec(
                scene(
                    {
                        "id": "ladder.bad",
                        "kind": "climbable_ladder",
                        "params": {"height": 3.0, "width": 0.2, "rail_radius": 0.06},
                    }
                )
            )
        self.assertEqual(caught.exception.code, "SPEC.INFEASIBLE_LADDER")

    def test_rejects_unknown_adapter_field(self) -> None:
        with self.assertRaises(SpecError) as caught:
            decode_scene_spec(
                scene(
                    {
                        "id": "desk.bad",
                        "kind": "desk",
                        "params": {"width": 1.2, "depth": 0.6, "height": 0.75, "magic": 1},
                    }
                )
            )
        self.assertEqual(caught.exception.code, "SPEC.UNKNOWN_FIELD")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest

from geoforge.pipeline import compile_drafts
from geoforge.spec import decode_scene_spec
from tests.common import valid_room_scene


class DraftCompilationTests(unittest.TestCase):
    def test_room_compiles_to_contracted_valid_drafts(self) -> None:
        spec = decode_scene_spec(valid_room_scene())
        result = compile_drafts(spec)
        self.assertEqual(len(result.artifacts), 8)
        self.assertTrue(result.contacts)
        for artifact in result.artifacts:
            self.assertIsNotNone(artifact.contract)
            self.assertEqual(artifact.draft.check(), ())
            self.assertGreater(artifact.draft.signed_volume(), 0.0)
            self.assertEqual(artifact.contract.local_bounds, artifact.draft.bounds)
            self.assertEqual(
                {anchor.name for anchor in artifact.contract.named_anchors},
                {"min", "base_center", "top_center"},
            )

    def test_compilation_is_deterministic(self) -> None:
        spec = decode_scene_spec(valid_room_scene())
        first = compile_drafts(spec)
        second = compile_drafts(spec)
        self.assertEqual(
            [(item.artifact_id, item.entity_seed, item.draft.fingerprint()) for item in first.artifacts],
            [(item.artifact_id, item.entity_seed, item.draft.fingerprint()) for item in second.artifacts],
        )

    def test_sanitized_blender_names_cannot_collide(self) -> None:
        data = valid_room_scene()
        data["entities"] = [
            {"id": "thing-a", "kind": "box", "params": {"width": 1, "depth": 1, "height": 1}},
            {"id": "thing_a", "kind": "box", "params": {"width": 1, "depth": 1, "height": 1}},
        ]
        result = compile_drafts(decode_scene_spec(data))
        self.assertEqual(len({artifact.object_name for artifact in result.artifacts}), 2)


if __name__ == "__main__":
    unittest.main()

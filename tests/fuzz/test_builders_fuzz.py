from __future__ import annotations

import random
import unittest

from geoforge.errors import SpecError
from geoforge.pipeline import compile_drafts
from geoforge.spec import decode_scene_spec


def scene(entity: dict, seed: int) -> dict:
    return {
        "schema_version": "1.0",
        "scene_id": f"fuzz_{seed}",
        "seed": seed,
        "units": "m",
        "entities": [entity],
        "quality": {"profile": "production", "min_feature_size": 0.01},
    }


class BuilderFuzzTests(unittest.TestCase):
    def test_100_rooms_with_valid_doors(self) -> None:
        rng = random.Random(1001)
        for case in range(100):
            width = rng.uniform(3.0, 20.0)
            length = rng.uniform(3.0, 20.0)
            height = rng.uniform(2.4, 5.0)
            wall = rng.choice(("south", "north", "west", "east"))
            wall_length = width if wall in {"south", "north"} else length
            opening_width = rng.uniform(0.7, min(2.0, wall_length * 0.35))
            offset = rng.uniform(opening_width * 0.5 + 0.1, wall_length - opening_width * 0.5 - 0.1)
            entity = {
                "id": "room.main",
                "kind": "room",
                "params": {
                    "width": width,
                    "length": length,
                    "height": height,
                    "wall_thickness": rng.uniform(0.1, 0.35),
                    "floor_thickness": rng.uniform(0.1, 0.3),
                    "ceiling": bool(case % 2),
                    "openings": [
                        {
                            "id": "door",
                            "kind": "door",
                            "wall": wall,
                            "offset": offset,
                            "width": opening_width,
                            "height": rng.uniform(1.9, min(2.4, height - 0.1)),
                        }
                    ],
                },
            }
            spec = decode_scene_spec(scene(entity, case))
            first = compile_drafts(spec)
            second = compile_drafts(spec)
            self.assertEqual(
                [item.draft.fingerprint() for item in first.artifacts],
                [item.draft.fingerprint() for item in second.artifacts],
            )
            for artifact in first.artifacts:
                self.assertEqual(artifact.draft.check(), ())
                self.assertGreater(artifact.draft.signed_volume(), 0.0)
                self.assertEqual(artifact.draft.bounds.dimensions, artifact.contract.dimensions)

    def test_100_rooms_with_valid_windows(self) -> None:
        rng = random.Random(1002)
        for case in range(100):
            width = rng.uniform(4.0, 16.0)
            length = rng.uniform(4.0, 16.0)
            height = rng.uniform(2.6, 4.5)
            wall = rng.choice(("south", "north", "west", "east"))
            wall_length = width if wall in {"south", "north"} else length
            opening_width = rng.uniform(0.6, min(2.5, wall_length * 0.4))
            offset = rng.uniform(opening_width * 0.5 + 0.1, wall_length - opening_width * 0.5 - 0.1)
            bottom = rng.uniform(0.4, 1.2)
            window_height = rng.uniform(0.5, height - bottom - 0.1)
            entity = {
                "id": "room.window",
                "kind": "room",
                "params": {
                    "width": width,
                    "length": length,
                    "height": height,
                    "wall_thickness": 0.2,
                    "floor_thickness": 0.2,
                    "ceiling": True,
                    "openings": [
                        {
                            "id": "window",
                            "kind": "window",
                            "wall": wall,
                            "offset": offset,
                            "width": opening_width,
                            "height": window_height,
                            "bottom": bottom,
                        }
                    ],
                },
            }
            compilation = compile_drafts(decode_scene_spec(scene(entity, case)))
            self.assertTrue(all(not item.draft.check() for item in compilation.artifacts))

    def test_100_staircases(self) -> None:
        rng = random.Random(1003)
        for case in range(100):
            rise = rng.uniform(0.5, 5.0)
            max_riser = rng.uniform(0.16, 0.22)
            risers = max(1, int(-(-rise // max_riser)))
            min_tread = rng.uniform(0.18, 0.25)
            run = risers * rng.uniform(min_tread, 0.4)
            entity = {
                "id": "stairs.main",
                "kind": "straight_stairs",
                "params": {
                    "width": rng.uniform(0.7, 2.5),
                    "run": run,
                    "rise": rise,
                    "max_riser": max_riser,
                    "min_tread": min_tread,
                },
            }
            spec = decode_scene_spec(scene(entity, case))
            artifact = compile_drafts(spec).artifacts[0]
            self.assertEqual(artifact.draft.check(), ())
            self.assertGreater(artifact.draft.signed_volume(), 0.0)
            self.assertAlmostEqual(artifact.contract.dimensions[0], run)
            self.assertAlmostEqual(artifact.contract.dimensions[2], rise)

    def test_invalid_opening_boundary_cases(self) -> None:
        for case in range(25):
            opening = {
                "id": "bad",
                "kind": "door",
                "wall": "south",
                "offset": 2.5,
                "width": 1.0,
                "height": 2.0,
            }
            mode = case % 5
            if mode == 0:
                opening["offset"] = -0.01 * (case + 1)
            elif mode == 1:
                opening["offset"] = 5.0 + 0.01 * (case + 1)
            elif mode == 2:
                opening["height"] = 3.0 + 0.01 * (case + 1)
            elif mode == 3:
                opening["bottom"] = 0.1
            entity = {
                "id": "room.bad",
                "kind": "room",
                "params": {
                    "width": 5.0,
                    "length": 5.0,
                    "height": 3.0,
                    "wall_thickness": 0.2,
                    "floor_thickness": 0.2,
                    "openings": [opening],
                },
            }
            if mode == 4:
                entity["params"]["openings"].append(
                    {
                        "id": "overlap",
                        "kind": "door",
                        "wall": "south",
                        "offset": 2.6,
                        "width": 1.0,
                        "height": 2.0,
                    }
                )
            with self.assertRaises(SpecError):
                decode_scene_spec(scene(entity, case))


if __name__ == "__main__":
    unittest.main()

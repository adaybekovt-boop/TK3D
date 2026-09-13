from __future__ import annotations

import unittest
from pathlib import Path

from geoforge.errors import SpecError
from geoforge.spec import load_scene_spec


ROOT = Path(__file__).resolve().parent


class RegressionSpecTests(unittest.TestCase):
    def test_opening_out_of_bounds_fixture(self) -> None:
        with self.assertRaises(SpecError) as caught:
            load_scene_spec(ROOT / "specs" / "opening_out_of_bounds.json")
        self.assertEqual(caught.exception.code, "SPEC.OPENING_OUT_OF_BOUNDS")

    def test_duplicate_json_field_fixture(self) -> None:
        with self.assertRaises(SpecError) as caught:
            load_scene_spec(ROOT / "specs" / "duplicate_field.json")
        self.assertEqual(caught.exception.code, "SPEC.DUPLICATE_FIELD")


if __name__ == "__main__":
    unittest.main()

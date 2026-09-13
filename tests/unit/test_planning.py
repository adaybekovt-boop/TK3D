from __future__ import annotations

import unittest

from geoforge.planning import plan_stairs, plan_wall_cells
from geoforge.spec import OpeningSpec, StairsParams


class PlanningTests(unittest.TestCase):
    def test_door_splits_wall_into_three_solids(self) -> None:
        opening = OpeningSpec("door", "door", 2.0, 1.0, 2.1, 0.0)
        cells = plan_wall_cells(5.0, 3.0, (opening,))
        self.assertEqual(len(cells), 3)
        area = sum(cell.width * cell.height for cell in cells)
        self.assertAlmostEqual(area, 5.0 * 3.0 - 1.0 * 2.1)

    def test_window_splits_wall_into_four_solids(self) -> None:
        opening = OpeningSpec("window", "window", 2.0, 1.0, 1.0, 1.0)
        cells = plan_wall_cells(5.0, 3.0, (opening,))
        self.assertEqual(len(cells), 4)
        area = sum(cell.width * cell.height for cell in cells)
        self.assertAlmostEqual(area, 14.0)

    def test_opening_flush_with_wall_boundary_creates_no_zero_size_cell(self) -> None:
        opening = OpeningSpec("door", "door", 0.5, 1.0, 2.1, 0.0)
        cells = plan_wall_cells(5.0, 3.0, (opening,))
        self.assertTrue(all(cell.width > 0.0 and cell.height > 0.0 for cell in cells))
        self.assertAlmostEqual(sum(cell.width * cell.height for cell in cells), 12.9)

    def test_stairs_reach_exact_target(self) -> None:
        plan = plan_stairs(StairsParams(1.2, 4.2, 3.2, 0.18, 0.2))
        self.assertEqual(plan.riser_count, 18)
        self.assertAlmostEqual(plan.riser_height * plan.riser_count, 3.2)
        self.assertAlmostEqual(plan.tread_depth * plan.riser_count, 4.2)
        self.assertEqual(plan.profile[2], (4.2, 3.2))


if __name__ == "__main__":
    unittest.main()

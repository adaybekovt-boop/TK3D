from __future__ import annotations

import unittest
import json

from geoforge.pipeline import RegenerationGuard
from geoforge.quality.model import BuildReport, Issue, ValidationReport
from geoforge.registry import create_default_registry
from geoforge.repair.policy import decide_tier1


class RegistryAndReportTests(unittest.TestCase):
    def test_default_registry_contains_v1_builders(self) -> None:
        registry = create_default_registry()
        kinds = {item.kind for item in registry.describe()}
        self.assertEqual(
            kinds,
            {"box", "wall", "room", "floor", "ceiling", "straight_stairs", "beam", "column"},
        )
        room = registry.describe("room")[0]
        self.assertIn("wall_thickness", room.required_params)
        self.assertIn("openings", room.optional_params)
        json.dumps(room.to_dict(), allow_nan=False)

    def test_repair_policy_accepts_only_tier1_codes(self) -> None:
        repairable = ValidationReport("a", "a/body", "SOLID", "POST_BUILD", issues=[Issue("TOPO.LOOSE_VERTEX", "loose")])
        fatal = ValidationReport("a", "a/body", "SOLID", "POST_BUILD", issues=[Issue("TOPO.BOUNDARY_EDGE", "hole")])
        self.assertTrue(decide_tier1(repairable).allowed)
        self.assertFalse(decide_tier1(fatal).allowed)

    def test_report_serialization_is_compact(self) -> None:
        report = BuildReport("scene", "abc", stage="COMPLETE")
        report.committed_objects.append("GF__box__body")
        value = report.compact_dict()
        self.assertEqual(value["status"], "PASS")
        self.assertNotIn("artifact_reports", value)
        self.assertEqual(value["committed_object_count"], 1)

    def test_regeneration_guard_stops_repeated_invalid_hash(self) -> None:
        guard = RegenerationGuard()
        self.assertTrue(guard.record_failure("entity", "hash"))
        self.assertFalse(guard.record_failure("entity", "hash"))
        self.assertTrue(guard.record_failure("entity", "other-hash"))


if __name__ == "__main__":
    unittest.main()

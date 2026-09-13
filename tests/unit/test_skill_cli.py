from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WRAPPER = ROOT / ".agents" / "skills" / "geoforge" / "scripts" / "gf.py"


class SkillCliTests(unittest.TestCase):
    def _run(self, *args: str):
        completed = subprocess.run(
            [sys.executable, str(WRAPPER), *args],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        return json.loads(completed.stdout)

    def test_search_describe_source_categories_and_status(self) -> None:
        hits = self._run("search", "office chair")
        self.assertGreaterEqual(len(hits), 1)
        self.assertLessEqual(len(hits), 5)
        self.assertTrue(any("chair" in hit["id"] for hit in hits))

        described = self._run("describe", "furniture.chair.office.roomicon")
        self.assertEqual(described["status"], "REFERENCE")
        self.assertEqual(described["symbol"], "generate_chair")
        self.assertTrue(described["source_available"])

        source = self._run("source", "furniture.chair.office.roomicon")
        self.assertTrue(source["source_available"])
        self.assertTrue(source["local_source"].endswith("roomicon/chairs/chair_types.py"))
        self.assertGreater(source["bytes"], 0)

        categories = {item["id"] for item in self._run("categories")}
        self.assertTrue({"architecture", "furniture", "nature", "props"} <= categories)

        status = self._run("status")
        self.assertEqual(status, {"ADAPTED": 5, "NATIVE": 8, "REFERENCE": 535, "UNSUPPORTED": 8, "total": 556})


if __name__ == "__main__":
    unittest.main()

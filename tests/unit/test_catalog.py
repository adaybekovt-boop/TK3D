from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from geoforge.catalog import (
    describe_generator,
    get_source,
    list_categories,
    load_catalog,
    search_generators,
    status_counts,
)
from geoforge.errors import SpecError
from geoforge.paths import catalog_json_path, catalogs_root, object_library_root, repo_root, vendor_library_root
from geoforge.registry import create_default_registry, create_full_registry


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / ".agents" / "skills" / "geoforge"


class CatalogTests(unittest.TestCase):
    def test_vendor_python_hashes_match_integrity(self) -> None:
        integrity = json.loads((vendor_library_root() / "INTEGRITY.json").read_text(encoding="utf-8"))
        self.assertEqual(integrity["python_files"], 30)
        for rel, expected in integrity["sha256"].items():
            data = (vendor_library_root() / rel).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), expected, rel)

    def test_vendor_origin_files_are_present(self) -> None:
        root = vendor_library_root()
        for name in ("CATALOG.json", "FILE_INDEX.json", "SOURCES.json", "metadata.json"):
            if name == "metadata.json":
                self.assertTrue((root / "architecture" / "stairs_walkable" / name).is_file())
            else:
                self.assertTrue((root / name).is_file())
        self.assertTrue((root / "_licenses" / "BUILDING_TOOLS_MIT.txt").is_file())
        self.assertTrue((root / "_licenses" / "INFINIGEN_BSD3.txt").is_file())
        self.assertTrue((root / "_licenses" / "PROCFUNC_BSD3.txt").is_file())

    def test_status_counts_and_native_builders(self) -> None:
        counts = status_counts()
        self.assertEqual(counts["NATIVE"], 8)
        self.assertEqual(counts["ADAPTED"], 5)
        self.assertEqual(counts["REFERENCE"], 535)
        self.assertEqual(counts["UNSUPPORTED"], 8)
        self.assertEqual(counts["total"], 556)
        kinds = {item.kind for item in create_default_registry().describe()}
        self.assertEqual(
            kinds,
            {"box", "wall", "room", "floor", "ceiling", "straight_stairs", "beam", "column"},
        )
        full = {item.kind for item in create_full_registry().describe()}
        self.assertTrue(kinds <= full)
        self.assertEqual(
            full - kinds,
            {"climbable_ladder", "railing", "balcony", "road", "desk"},
        )

    def test_search_prefers_walkable_stairs_between_floors(self) -> None:
        results = search_generators("stairs between floors")
        ids = [item["id"] for item in results]
        self.assertEqual(ids[0], "architecture.stairs.walkable")
        industrial = search_generators("Нужна промышленная лестница между этажами")
        self.assertEqual(industrial[0]["id"], "architecture.stairs.walkable")

    def test_search_prefers_climbable_ladder_for_hands(self) -> None:
        results = search_generators("ladder to climb using hands", limit=8)
        self.assertEqual(results[0]["id"], "architecture.stairs.climbable_ladder")
        self.assertEqual(results[0]["status"], "ADAPTED")
        ids = [item["id"] for item in results]
        if "architecture.stairs.walkable" in ids:
            self.assertLess(ids.index("architecture.stairs.climbable_ladder"), ids.index("architecture.stairs.walkable"))

    def test_describe_and_source_are_single_generator(self) -> None:
        described = describe_generator("architecture.stairs.climbable_ladder")
        self.assertEqual(described["status"], "ADAPTED")
        self.assertEqual(described["kind"], "climbable_ladder")
        self.assertIn("height", described["params"]["params"])
        self.assertEqual(described["license"], "project-owned generated code")
        source = get_source("architecture.stairs.climbable_ladder")
        self.assertTrue(source["source_file"].endswith("climbable_parametric_ladder.py"))
        self.assertEqual(source["source_file"], source["local_source"])
        self.assertTrue(source["source_available"])
        self.assertNotIn("text", source)
        self.assertNotIn("stairs_types.py", source["source_file"])
        with_text = get_source("architecture.room", include_text=True)
        self.assertIn("class RoomBuilder", with_text["text"])

    def test_get_source_rejects_unknown_id(self) -> None:
        with self.assertRaises(SpecError):
            get_source("not.a.generator")

    def test_categories_include_expected_roots(self) -> None:
        names = {item["id"] for item in list_categories()}
        self.assertTrue(
            {
                "architecture",
                "buildings",
                "decor",
                "electronics",
                "furniture",
                "geometry",
                "household",
                "industrial",
                "infrastructure",
                "interior",
                "nature",
                "props",
                "shared",
                "street",
            }
            <= names
        )

    def test_merged_catalog_integrity_and_package_mirror(self) -> None:
        integrity = json.loads((catalogs_root() / "integrity.json").read_text(encoding="utf-8"))
        self.assertEqual(integrity["status"], "PASS")
        self.assertEqual(integrity["total_entries"], 556)
        self.assertEqual(integrity["library_python_files"], 345)
        self.assertEqual(integrity["object_python_files"], 315)
        self.assertEqual(integrity["curated_python_files"], 30)
        self.assertEqual(integrity["duplicate_ids"], [])
        self.assertEqual(integrity["broken_local_source_ids"], [])
        self.assertEqual(integrity["empty_local_source_ids"], [])
        self.assertEqual(integrity["hash_mismatch_ids"], [])
        self.assertEqual(integrity["missing_license_ids"], [])
        self.assertEqual(integrity["missing_repository_ids"], [])
        self.assertEqual(catalog_json_path(), catalogs_root() / "generators.json")
        self.assertEqual(
            (catalogs_root() / "generators.json").read_bytes(),
            (repo_root() / "src" / "geoforge" / "catalog" / "generators.json").read_bytes(),
        )
        self.assertEqual(len(list(object_library_root().rglob("*.py"))), 315)

    def test_every_declared_local_source_is_present_and_nonempty(self) -> None:
        entries = load_catalog()
        ids = [entry["id"] for entry in entries]
        self.assertEqual(len(ids), len(set(ids)))
        for entry in entries:
            with self.subTest(generator=entry["id"]):
                self.assertTrue(entry.get("license"))
                local = entry.get("local_source")
                if not local:
                    self.assertFalse(entry.get("source_available"))
                    continue
                path = repo_root() / local
                self.assertTrue(path.is_file(), local)
                self.assertGreater(path.stat().st_size, 0, local)
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry["sha256"])

    def test_harvest_reference_is_searchable_and_remote_source_is_explicit(self) -> None:
        results = search_generators("toilet bathroom", limit=5)
        self.assertTrue(results)
        self.assertTrue(any("toilet" in item["id"] for item in results))
        remote = get_source("architecture.pillar.infinigen")
        self.assertEqual(remote["status"] if "status" in remote else "REFERENCE", "REFERENCE")
        self.assertFalse(remote["source_available"])
        self.assertIsNone(remote["local_source"])
        self.assertEqual(remote["symbol"], "PillarFactory")
        with self.assertRaises(SpecError) as caught:
            get_source("architecture.pillar.infinigen", include_text=True)
        self.assertEqual(caught.exception.code, "CATALOG.NO_LOCAL_SOURCE")

    def test_provenance_collision_is_disambiguated_not_dropped(self) -> None:
        by_id = {item["id"]: item for item in load_catalog()}
        self.assertEqual(by_id["furniture.chair.office"]["source_project"], "Infinigen")
        roomicon = by_id["furniture.chair.office.roomicon"]
        self.assertEqual(roomicon["original_id"], "furniture.chair.office")
        self.assertEqual(roomicon["source_project"], "Roomicon")
        self.assertTrue(roomicon["source_available"])

    def test_native_entries_have_kinds_and_schemas(self) -> None:
        by_id = {item["id"]: item for item in load_catalog()}
        self.assertEqual(by_id["architecture.room"]["kind"], "room")
        self.assertEqual(by_id["architecture.stairs.walkable"]["status"], "NATIVE")
        self.assertIsNotNone(by_id["architecture.stairs.walkable"]["param_schema"])
        self.assertIsNone(by_id["architecture.door"]["param_schema"])
        self.assertEqual(by_id["architecture.door"]["status"], "REFERENCE")

    def test_project_skill_is_discoverable(self) -> None:
        skill_md = SKILL / "SKILL.md"
        self.assertTrue(skill_md.is_file(), skill_md)
        text = skill_md.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---"))
        self.assertIn("name: geoforge", text)
        self.assertIn("scripts/gf.py search", text)
        self.assertTrue((SKILL / "scripts" / "gf.py").is_file())
        self.assertEqual(SKILL.relative_to(repo_root()).as_posix(), ".agents/skills/geoforge")


if __name__ == "__main__":
    unittest.main()

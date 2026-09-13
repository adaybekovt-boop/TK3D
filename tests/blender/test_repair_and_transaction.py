from __future__ import annotations

import unittest
from dataclasses import replace

import bpy

from geoforge.builders.architecture import BoxBuilder
from geoforge.builders.base import BuildProduct
from geoforge.geometry.model import TopologyIntent
from geoforge.geometry.primitives import box, merge_drafts
from geoforge.operations.transaction import StagingTransaction
from geoforge.pipeline import RegenerationGuard, compile_drafts, compile_scene
from geoforge.quality.mesh import validate_materialized
from geoforge.registry import create_default_registry
from geoforge.repair.cheap import begin_tier1_repair
from geoforge.repair.policy import decide_tier1
from geoforge.spec import decode_scene_spec
from tests.blender.support import box_entity, cleanup_generated, simple_scene, staging_collections, temporary_directory


class BrokenBoxBuilder(BoxBuilder):
    version = "broken-1"

    def build(self, plan, context):
        product = super().build(plan, context)
        artifact = product.artifacts[0]
        broken = replace(
            artifact,
            draft=replace(artifact.draft, faces=artifact.draft.faces[:-1], semantic_regions=()),
        )
        return BuildProduct((broken,))


class RepairableBoxBuilder(BoxBuilder):
    version = "repairable-1"

    def build(self, plan, context):
        product = super().build(plan, context)
        artifact = product.artifacts[0]
        changed = replace(
            artifact,
            draft=replace(artifact.draft, vertices=artifact.draft.vertices + (artifact.draft.vertices[0],)),
        )
        return BuildProduct((changed,))


class InvalidReferenceBoxBuilder(BoxBuilder):
    version = "invalid-reference-1"

    def build(self, plan, context):
        product = super().build(plan, context)
        artifact = product.artifacts[0]
        faces = list(artifact.draft.faces)
        faces[0] = (999, *faces[0][1:])
        changed = replace(
            artifact,
            draft=replace(artifact.draft, faces=tuple(faces), semantic_regions=()),
        )
        return BuildProduct((changed,))


class RepairAndTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        cleanup_generated()

    def tearDown(self) -> None:
        cleanup_generated()

    def test_tier1_repairs_loose_duplicate_and_preserves_bounds(self) -> None:
        spec = decode_scene_spec(simple_scene([box_entity()]))
        artifact = compile_drafts(spec).artifacts[0]
        broken = replace(artifact, draft=replace(artifact.draft, vertices=artifact.draft.vertices + (artifact.draft.vertices[0],)))
        transaction = StagingTransaction()
        self.addCleanup(transaction.rollback)
        item = transaction.materialize(broken)
        before = validate_materialized(item)
        self.assertTrue(decide_tier1(before).allowed)
        attempt = begin_tier1_repair(item.object, item.artifact.contract)
        after = validate_materialized(item, stage="POST_REPAIR")
        self.assertEqual(after.status, "PASS", after.compact_dict())
        self.assertTrue(attempt.within_budget(item.artifact.contract))
        attempt.commit()

    def test_tier1_repairs_flipped_winding(self) -> None:
        spec = decode_scene_spec(simple_scene([box_entity()]))
        artifact = compile_drafts(spec).artifacts[0]
        faces = list(artifact.draft.faces)
        faces[0] = tuple(reversed(faces[0]))
        broken = replace(artifact, draft=replace(artifact.draft, faces=tuple(faces)))
        transaction = StagingTransaction()
        self.addCleanup(transaction.rollback)
        item = transaction.materialize(broken)
        self.assertIn("TOPO.INCONSISTENT_WINDING", validate_materialized(item).issue_counts)
        attempt = begin_tier1_repair(item.object, item.artifact.contract)
        after = validate_materialized(item, stage="POST_REPAIR")
        self.assertEqual(after.status, "PASS", after.compact_dict())
        attempt.rollback()
        self.assertIn("TOPO.INCONSISTENT_WINDING", validate_materialized(item).issue_counts)

    def test_tier1_repairs_fully_inverted_solid(self) -> None:
        spec = decode_scene_spec(simple_scene([box_entity()]))
        artifact = compile_drafts(spec).artifacts[0]
        inverted = replace(
            artifact,
            draft=replace(artifact.draft, faces=tuple(tuple(reversed(face)) for face in artifact.draft.faces)),
        )
        transaction = StagingTransaction()
        self.addCleanup(transaction.rollback)
        item = transaction.materialize(inverted)
        before = validate_materialized(item)
        self.assertIn("TOPO.INWARD_ORIENTATION", before.issue_counts)
        self.assertTrue(decide_tier1(before).allowed)
        attempt = begin_tier1_repair(item.object, item.artifact.contract)
        after = validate_materialized(item, stage="POST_REPAIR")
        self.assertEqual(after.status, "PASS", after.compact_dict())
        attempt.commit()

    def test_controlled_weld_does_not_merge_disconnected_components(self) -> None:
        spec = decode_scene_spec(simple_scene([box_entity()]))
        artifact = compile_drafts(spec).artifacts[0]
        draft = merge_drafts(
            (
                box(1.0, 1.0, 1.0),
                box(1.0, 1.0, 1.0, origin=(1.0, 0.0, 0.0)),
            )
        )
        contract = replace(
            artifact.contract,
            topology_intent=TopologyIntent.ASSEMBLY,
            expected_component_count=2,
            local_bounds=draft.bounds,
            dimensions=draft.bounds.dimensions,
        )
        transaction = StagingTransaction()
        self.addCleanup(transaction.rollback)
        item = transaction.materialize(replace(artifact, draft=draft, contract=contract))
        before = validate_materialized(item)
        self.assertEqual(before.metrics["components"], 2)
        self.assertIn("GEOM.DUPLICATE_VERTEX", before.issue_counts)
        attempt = begin_tier1_repair(item.object, contract)
        after = validate_materialized(item, stage="POST_REPAIR")
        self.assertEqual(after.metrics["components"], 2)
        self.assertIn("GEOM.DUPLICATE_VERTEX", after.issue_counts)
        attempt.rollback()

    def test_pipeline_applies_allowed_tier1_repair(self) -> None:
        registry = create_default_registry()
        registry.register(RepairableBoxBuilder(), replace=True)
        spec = decode_scene_spec(simple_scene([box_entity()]))
        with temporary_directory() as output:
            result = compile_scene(spec, output_root=output, registry=registry)
        self.assertTrue(result.ok, result.report.full_dict())
        self.assertEqual(result.report.repaired_artifacts, ["box.main/body"])
        self.assertEqual(result.report.repair_records[0]["outcome"], "COMMITTED")
        self.assertIn("GEOM.DUPLICATE_VERTEX", result.report.repair_records[0]["before_issue_counts"])
        self.assertEqual(result.report.repair_records[0]["after_issue_counts"], {})

    def test_failed_replacement_preserves_existing_final_and_leaks_nothing(self) -> None:
        spec = decode_scene_spec(simple_scene([box_entity()]))
        with temporary_directory() as output:
            good = compile_scene(spec, output_root=output)
            self.assertTrue(good.ok)
            final = bpy.data.collections["GF_FINAL"]
            old_object = final.objects[0]
            old_fingerprint = old_object["gf_mesh_fingerprint"]
            object_count = len(bpy.data.objects)
            mesh_count = len(bpy.data.meshes)
            registry = create_default_registry()
            registry.register(BrokenBoxBuilder(), replace=True)
            failed = compile_scene(spec, output_root=output, registry=registry)
        self.assertFalse(failed.ok)
        self.assertEqual(len(final.objects), 1)
        self.assertEqual(final.objects[0].as_pointer(), old_object.as_pointer())
        self.assertEqual(final.objects[0]["gf_mesh_fingerprint"], old_fingerprint)
        self.assertEqual(len(bpy.data.objects), object_count)
        self.assertEqual(len(bpy.data.meshes), mesh_count)
        self.assertFalse(staging_collections())
        self.assertTrue(all(not item.published for item in failed.manifest.artifacts))

    def test_explicit_rollback_removes_objects_meshes_and_collection(self) -> None:
        spec = decode_scene_spec(simple_scene([box_entity()]))
        artifact = compile_drafts(spec).artifacts[0]
        object_count = len(bpy.data.objects)
        mesh_count = len(bpy.data.meshes)
        transaction = StagingTransaction()
        transaction.materialize(artifact)
        self.assertTrue(staging_collections())
        transaction.rollback()
        self.assertEqual(len(bpy.data.objects), object_count)
        self.assertEqual(len(bpy.data.meshes), mesh_count)
        self.assertFalse(staging_collections())

    def test_repeated_invalid_draft_hash_becomes_builder_bug(self) -> None:
        registry = create_default_registry()
        registry.register(InvalidReferenceBoxBuilder(), replace=True)
        spec = decode_scene_spec(simple_scene([box_entity()]))
        guard = RegenerationGuard()
        with temporary_directory() as output:
            first = compile_scene(spec, output_root=output, registry=registry, regeneration_guard=guard)
            second = compile_scene(spec, output_root=output, registry=registry, regeneration_guard=guard)
        self.assertFalse(first.ok)
        self.assertFalse(second.ok)
        self.assertIn("TOPO.INVALID_FACE_INDEX", first.report.compact_dict()["issue_counts"])
        self.assertIn("BUILD.BUILDER_BUG", second.report.compact_dict()["issue_counts"])
        self.assertFalse(staging_collections())


if __name__ == "__main__":
    unittest.main()

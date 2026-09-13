from __future__ import annotations

from dataclasses import replace
import unittest

import bpy

from geoforge.adapters.ladder import ClimbableLadderBuilder
from geoforge.builders.base import BuildProduct
from geoforge.pipeline import compile_scene
from geoforge.registry import create_full_registry
from geoforge.spec import decode_scene_spec
from tests.blender.support import cleanup_generated, simple_scene, staging_collections, temporary_directory


class BrokenLadderBuilder(ClimbableLadderBuilder):
    version = "broken-adapter-1"

    def build(self, plan, context):
        product = super().build(plan, context)
        artifact = product.artifacts[0]
        broken = replace(
            artifact,
            draft=replace(artifact.draft, faces=artifact.draft.faces[:-1], semantic_regions=()),
        )
        return BuildProduct((broken, *product.artifacts[1:]), product.contacts)


def _entity(kind: str, entity_id: str, params: dict) -> dict:
    return {"id": entity_id, "kind": kind, "params": params}


class AdapterPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        cleanup_generated()

    def tearDown(self) -> None:
        cleanup_generated()

    def _compile(self, entities: list[dict], *, registry=None):
        temporary = temporary_directory()
        self.addCleanup(temporary.cleanup)
        spec = decode_scene_spec(simple_scene(entities, scene_id="adapter_qa"))
        result = compile_scene(spec, output_root=temporary.name, registry=registry)
        return result

    def test_climbable_ladder_passes_qa(self) -> None:
        result = self._compile(
            [_entity("climbable_ladder", "ladder.main", {"height": 3.0, "width": 0.45, "lean_deg": 12.0})]
        )
        self.assertTrue(result.ok, result.report.full_dict())
        self.assertGreaterEqual(len(result.report.committed_objects), 4)
        self.assertFalse(staging_collections())

    def test_railing_balcony_road_desk_pass_qa(self) -> None:
        cases = [
            [_entity("railing", "rail.main", {"length": 2.2, "height": 1.0, "fill": "posts"})],
            [_entity("railing", "rail.rails", {"length": 2.2, "height": 1.0, "fill": "rails"})],
            [_entity("balcony", "balc.main", {"width": 2.4, "depth": 1.2})],
            [_entity("road", "road.main", {"length": 10.0, "width": 6.0})],
            [_entity("road", "road.walk", {"length": 8.0, "width": 6.0, "sidewalks": True, "shoulders": True})],
            [_entity("desk", "desk.main", {"width": 1.4, "depth": 0.7, "height": 0.75})],
        ]
        for entities in cases:
            with self.subTest(kind=entities[0]["kind"], id=entities[0]["id"]):
                cleanup_generated()
                result = self._compile(entities)
                self.assertTrue(result.ok, result.report.full_dict())
                self.assertTrue(all(item.published for item in result.manifest.artifacts))
                self.assertFalse(staging_collections())

    def test_failed_adapter_rolls_back_and_publishes_nothing(self) -> None:
        good = self._compile([_entity("desk", "desk.main", {"width": 1.2, "depth": 0.6, "height": 0.74})])
        self.assertTrue(good.ok)
        final = bpy.data.collections["GF_FINAL"]
        before = len(final.objects)
        registry = create_full_registry()
        registry.register(BrokenLadderBuilder(), replace=True)
        failed = self._compile(
            [_entity("climbable_ladder", "ladder.bad", {"height": 2.8, "width": 0.4})],
            registry=registry,
        )
        self.assertFalse(failed.ok)
        self.assertEqual(len(final.objects), before)
        self.assertTrue(all(not item.published for item in failed.manifest.artifacts))
        self.assertFalse(staging_collections())


if __name__ == "__main__":
    unittest.main()

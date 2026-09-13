from __future__ import annotations

import unittest

import bpy

from geoforge.geometry.blender import capability_probe, evaluated_mesh_copy
from geoforge.operations.transaction import StagingTransaction
from geoforge.pipeline import compile_drafts
from geoforge.spec import decode_scene_spec
from tests.blender.support import box_entity, cleanup_generated, simple_scene


class CapabilityTests(unittest.TestCase):
    def tearDown(self) -> None:
        cleanup_generated()

    def test_required_blender_capabilities_exist(self) -> None:
        capabilities = capability_probe()
        self.assertTrue(capabilities["background"])
        self.assertTrue(capabilities["evaluated_mesh"])
        self.assertTrue(capabilities["mesh_from_pydata"])
        self.assertTrue(capabilities["mesh_validate"])
        self.assertTrue(all(capabilities["bmesh_predicates"].values()))

    def test_evaluated_mesh_copy_signature_works(self) -> None:
        artifact = compile_drafts(decode_scene_spec(simple_scene([box_entity()]))).artifacts[0]
        transaction = StagingTransaction()
        evaluated = None
        try:
            item = transaction.materialize(artifact)
            evaluated = evaluated_mesh_copy(item.object)
            self.assertEqual(len(evaluated.vertices), len(artifact.draft.vertices))
            self.assertEqual(len(evaluated.polygons), len(artifact.draft.faces))
        finally:
            if evaluated is not None and evaluated.users == 0:
                bpy.data.meshes.remove(evaluated)
            transaction.rollback()


if __name__ == "__main__":
    unittest.main()

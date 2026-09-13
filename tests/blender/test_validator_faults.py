from __future__ import annotations

import json
import math
import unittest
from dataclasses import replace

import bpy

from geoforge.geometry.model import BoundaryContract, GeometryContract, MeshDraft, TopologyIntent
from geoforge.geometry.primitives import box, merge_drafts, plane
from geoforge.operations.transaction import StagingTransaction
from geoforge.pipeline import compile_drafts
from geoforge.quality.mesh import validate_materialized
from geoforge.spec import decode_scene_spec
from tests.blender.support import box_entity, cleanup_generated, simple_scene


class ValidatorFaultTests(unittest.TestCase):
    def setUp(self) -> None:
        cleanup_generated()
        spec = decode_scene_spec(simple_scene([box_entity()]))
        self.base = compile_drafts(spec).artifacts[0]
        self.transaction = StagingTransaction()

    def tearDown(self) -> None:
        self.transaction.rollback()
        cleanup_generated()

    def _report(self, draft: MeshDraft):
        artifact = replace(self.base, draft=draft)
        return validate_materialized(self.transaction.materialize(artifact))

    def test_missing_face_is_detected(self) -> None:
        report = self._report(replace(self.base.draft, faces=self.base.draft.faces[:-1]))
        self.assertIn("TOPO.BOUNDARY_EDGE", report.issue_counts)

    def test_flipped_face_is_detected(self) -> None:
        faces = list(self.base.draft.faces)
        faces[0] = tuple(reversed(faces[0]))
        report = self._report(replace(self.base.draft, faces=tuple(faces)))
        self.assertIn("TOPO.INCONSISTENT_WINDING", report.issue_counts)

    def test_duplicate_vertex_is_detected(self) -> None:
        draft = replace(self.base.draft, vertices=self.base.draft.vertices + (self.base.draft.vertices[0],))
        report = self._report(draft)
        self.assertIn("GEOM.DUPLICATE_VERTEX", report.issue_counts)

    def test_zero_area_face_is_detected(self) -> None:
        start = len(self.base.draft.vertices)
        vertices = self.base.draft.vertices + ((0.0, 0.0, 5.0), (1.0, 0.0, 5.0), (2.0, 0.0, 5.0))
        faces = self.base.draft.faces + ((start, start + 1, start + 2),)
        report = self._report(replace(self.base.draft, vertices=vertices, faces=faces))
        self.assertIn("GEOM.ZERO_AREA_FACE", report.issue_counts)

    def test_zero_length_edge_is_detected(self) -> None:
        vertices = list(self.base.draft.vertices)
        vertices[1] = vertices[0]
        report = self._report(replace(self.base.draft, vertices=tuple(vertices)))
        self.assertIn("GEOM.ZERO_LENGTH_EDGE", report.issue_counts)

    def test_wire_edge_is_detected(self) -> None:
        start = len(self.base.draft.vertices)
        draft = replace(
            self.base.draft,
            vertices=self.base.draft.vertices + ((5.0, 5.0, 5.0), (6.0, 5.0, 5.0)),
            edges=((start, start + 1),),
        )
        report = self._report(draft)
        self.assertIn("TOPO.WIRE_EDGE", report.issue_counts)

    def test_duplicate_face_is_detected(self) -> None:
        draft = replace(self.base.draft, faces=self.base.draft.faces + (self.base.draft.faces[0],))
        report = self._report(draft)
        self.assertIn("TOPO.DUPLICATE_FACE", report.issue_counts)

    def test_disconnected_component_is_detected(self) -> None:
        draft = merge_drafts((box(1.0, 1.0, 1.0), box(1.0, 1.0, 1.0, origin=(3.0, 0.0, 0.0))))
        report = self._report(draft)
        self.assertIn("TOPO.COMPONENT_COUNT", report.issue_counts)

    def test_feature_below_contract_minimum_is_detected(self) -> None:
        spec_data = simple_scene([box_entity()])
        spec_data["entities"][0]["params"]["width"] = 0.005
        artifact = compile_drafts(decode_scene_spec(spec_data)).artifacts[0]
        report = self._report(artifact.draft)
        self.assertIn("GEOM.FEATURE_TOO_SMALL", report.issue_counts)

    def test_loose_vertex_is_detected(self) -> None:
        draft = replace(self.base.draft, vertices=self.base.draft.vertices + ((10.0, 10.0, 10.0),))
        report = self._report(draft)
        self.assertIn("TOPO.LOOSE_VERTEX", report.issue_counts)

    def test_non_manifold_edge_is_detected(self) -> None:
        start = len(self.base.draft.vertices)
        vertices = self.base.draft.vertices + ((1.0, -1.0, 1.0),)
        faces = self.base.draft.faces + ((0, 1, start),)
        report = self._report(replace(self.base.draft, vertices=vertices, faces=faces))
        self.assertIn("TOPO.EDGE_GT_TWO_FACES", report.issue_counts)

    def test_non_unit_scale_is_detected(self) -> None:
        item = self.transaction.materialize(self.base)
        item.object.scale = (2.0, 1.0, 1.0)
        report = validate_materialized(item)
        self.assertIn("TRANSFORM.NON_UNIT_SCALE", report.issue_counts)

    def test_non_finite_scale_is_detected_and_serializable(self) -> None:
        item = self.transaction.materialize(self.base)
        item.object.scale.x = math.nan
        report = validate_materialized(item)
        self.assertIn("TRANSFORM.NON_FINITE_SCALE", report.issue_counts)
        json.dumps(report.compact_dict(), allow_nan=False)

    def test_non_finite_coordinate_is_detected_without_validator_crash(self) -> None:
        item = self.transaction.materialize(self.base)
        item.mesh.vertices[0].co.x = math.nan
        report = validate_materialized(item)
        self.assertIn("GEOM.NON_FINITE_VERTEX", report.issue_counts)
        json.dumps(report.compact_dict(), allow_nan=False)

    def test_open_surface_with_matching_boundary_contract_passes(self) -> None:
        draft = plane(2.0, 3.0, name="surface")
        contract = GeometryContract(
            TopologyIntent.OPEN_SURFACE,
            1,
            draft.bounds,
            draft.bounds.dimensions,
            allowed_boundaries=BoundaryContract(1, 4),
            minimum_feature_size=0.01,
        )
        artifact = replace(self.base, draft=draft, contract=contract, artifact_id="surface/body")
        report = validate_materialized(self.transaction.materialize(artifact))
        self.assertEqual(report.status, "PASS", report.compact_dict())


if __name__ == "__main__":
    unittest.main()

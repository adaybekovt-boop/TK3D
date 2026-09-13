from __future__ import annotations

import math
import unittest

from geoforge.geometry.model import MeshDraft, SemanticRegion
from geoforge.geometry.primitives import box, extrude_profile, merge_drafts, plane


class PrimitiveTests(unittest.TestCase):
    def test_box_counts_and_winding(self) -> None:
        draft = box(2.0, 3.0, 4.0)
        self.assertEqual(len(draft.vertices), 8)
        self.assertEqual(len(draft.faces), 6)
        self.assertAlmostEqual(draft.signed_volume(), 24.0)
        self.assertEqual(draft.check(), ())

    def test_plane_is_open_quad(self) -> None:
        draft = plane(2.0, 3.0)
        self.assertEqual((len(draft.vertices), len(draft.faces)), (4, 1))
        self.assertAlmostEqual(draft.bounds.dimensions[0], 2.0)

    def test_extruded_concave_profile_is_closed_and_outward(self) -> None:
        profile = ((0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (1.0, 2.0), (1.0, 1.0), (0.0, 1.0))
        draft = extrude_profile(profile, 1.5, axis="Y")
        self.assertEqual(len(draft.vertices), 12)
        self.assertGreater(draft.signed_volume(), 0.0)
        self.assertEqual(draft.check(), ())

    def test_extrusion_is_outward_on_all_supported_axes(self) -> None:
        for axis in ("X", "Y", "Z"):
            with self.subTest(axis=axis):
                draft = extrude_profile(((0, 0), (2, 0), (2, 3), (0, 3)), 4.0, axis=axis)
                self.assertAlmostEqual(draft.signed_volume(), 24.0)
                self.assertEqual(draft.check(), ())

    def test_merge_offsets_indices(self) -> None:
        merged = merge_drafts((box(1, 1, 1), box(2, 1, 1, origin=(3, 0, 0))), name="two")
        self.assertEqual(len(merged.vertices), 16)
        self.assertEqual(len(merged.faces), 12)
        self.assertEqual(merged.check(), ())

    def test_fingerprint_is_face_order_independent(self) -> None:
        original = box(1, 2, 3)
        reverse_map = {old: len(original.faces) - 1 - old for old in range(len(original.faces))}
        reordered = MeshDraft(
            original.name,
            original.vertices,
            original.edges,
            tuple(reversed(original.faces)),
            tuple(
                SemanticRegion(region.name, tuple(reverse_map[index] for index in region.face_indices))
                for region in original.semantic_regions
            ),
        )
        self.assertEqual(original.fingerprint(), reordered.fingerprint())

    def test_draft_detects_repeated_face_index(self) -> None:
        invalid = MeshDraft("bad", ((0, 0, 0), (1, 0, 0), (0, 1, 0)), faces=((0, 1, 1),))
        self.assertIn("TOPO.REPEATED_FACE_INDEX", {issue.code for issue in invalid.check()})

    def test_draft_detects_invalid_references_and_can_still_be_fingerprinted(self) -> None:
        invalid = MeshDraft(
            "bad.references",
            ((0, 0, 0), (1, 0, 0), (0, 1, 0)),
            edges=((0, 9),),
            faces=((0, 1, 7),),
        )
        codes = {issue.code for issue in invalid.check()}
        self.assertIn("TOPO.INVALID_EDGE_INDEX", codes)
        self.assertIn("TOPO.INVALID_FACE_INDEX", codes)
        self.assertEqual(len(invalid.fingerprint()), 64)

        non_finite = MeshDraft("bad.nan", ((math.nan, 0, 0), (1, 0, 0), (0, 1, 0)), faces=((0, 1, 2),))
        self.assertIn("GEOM.NON_FINITE_VERTEX", {issue.code for issue in non_finite.check()})
        self.assertEqual(non_finite.fingerprint(), non_finite.fingerprint())


if __name__ == "__main__":
    unittest.main()

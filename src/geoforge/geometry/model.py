from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Sequence, TypeAlias

from ..errors import GeometryError


Vec2: TypeAlias = tuple[float, float]
Vec3: TypeAlias = tuple[float, float, float]
Edge: TypeAlias = tuple[int, int]
Face: TypeAlias = tuple[int, ...]


class TopologyIntent(str, Enum):
    SOLID = "SOLID"
    OPEN_SURFACE = "OPEN_SURFACE"
    ASSEMBLY = "ASSEMBLY"


@dataclass(frozen=True)
class Bounds3:
    minimum: Vec3
    maximum: Vec3

    @classmethod
    def from_vertices(cls, vertices: Sequence[Vec3]) -> "Bounds3":
        if not vertices:
            raise GeometryError("Cannot calculate bounds of an empty mesh", code="GEOMETRY.EMPTY_DRAFT")
        return cls(
            tuple(min(vertex[axis] for vertex in vertices) for axis in range(3)),
            tuple(max(vertex[axis] for vertex in vertices) for axis in range(3)),
        )

    @property
    def dimensions(self) -> Vec3:
        return tuple(self.maximum[axis] - self.minimum[axis] for axis in range(3))

    def to_dict(self) -> dict[str, list[float]]:
        return {"minimum": list(self.minimum), "maximum": list(self.maximum)}


@dataclass(frozen=True)
class Anchor:
    name: str
    position: Vec3


@dataclass(frozen=True)
class SemanticRegion:
    name: str
    face_indices: tuple[int, ...]


@dataclass(frozen=True)
class BoundaryContract:
    expected_loop_count: int
    expected_edge_count: int | None = None
    labels: tuple[str, ...] = ()


@dataclass(frozen=True)
class RepairLimits:
    weld_distance: float
    max_bounds_delta: float
    max_dimension_delta: float
    allow_weld: bool = True


@dataclass(frozen=True)
class GeometryContract:
    topology_intent: TopologyIntent
    expected_component_count: int
    local_bounds: Bounds3
    dimensions: Vec3
    allowed_boundaries: BoundaryContract | None = None
    named_anchors: tuple[Anchor, ...] = ()
    minimum_feature_size: float = 0.01
    repair_limits: RepairLimits | None = None


@dataclass(frozen=True)
class DraftIssue:
    code: str
    message: str


@dataclass(frozen=True)
class MeshDraft:
    name: str
    vertices: tuple[Vec3, ...]
    edges: tuple[Edge, ...] = ()
    faces: tuple[Face, ...] = ()
    semantic_regions: tuple[SemanticRegion, ...] = ()

    @property
    def bounds(self) -> Bounds3:
        return Bounds3.from_vertices(self.vertices)

    def check(self) -> tuple[DraftIssue, ...]:
        issues: list[DraftIssue] = []
        vertex_count = len(self.vertices)
        for index, vertex in enumerate(self.vertices):
            if len(vertex) != 3 or not all(math.isfinite(float(value)) for value in vertex):
                issues.append(DraftIssue("GEOM.NON_FINITE_VERTEX", f"vertex {index} is not finite"))
        for index, edge in enumerate(self.edges):
            if len(edge) != 2 or any(item < 0 or item >= vertex_count for item in edge):
                issues.append(DraftIssue("TOPO.INVALID_EDGE_INDEX", f"edge {index} contains an invalid index"))
            elif edge[0] == edge[1]:
                issues.append(DraftIssue("TOPO.REPEATED_EDGE_INDEX", f"edge {index} repeats a vertex index"))
        for index, face in enumerate(self.faces):
            if any(item < 0 or item >= vertex_count for item in face):
                issues.append(DraftIssue("TOPO.INVALID_FACE_INDEX", f"face {index} contains an invalid index"))
                continue
            if len(face) < 3 or len(set(face)) < 3:
                issues.append(DraftIssue("TOPO.REPEATED_FACE_INDEX", f"face {index} has fewer than 3 unique vertices"))
        for region in self.semantic_regions:
            for face_index in region.face_indices:
                if face_index < 0 or face_index >= len(self.faces):
                    issues.append(
                        DraftIssue(
                            "SEMANTIC.INVALID_FACE_INDEX",
                            f"semantic region {region.name!r} references face {face_index}",
                        )
                    )
        if not self.vertices or not self.faces:
            issues.append(DraftIssue("GEOMETRY.EMPTY_DRAFT", "draft must contain vertices and faces"))
        return tuple(issues)

    def validate_or_raise(self) -> None:
        issues = self.check()
        if issues:
            first = issues[0]
            raise GeometryError(first.message, code=first.code, context={"issue_count": len(issues)})

    def fingerprint(self, precision: int = 9) -> str:
        """Order-insensitive deterministic topology fingerprint preserving face winding.

        Failed builder output is fingerprinted by the regeneration guard, so
        invalid references must be encoded deterministically instead of raising.
        """
        rounded = [tuple(_fingerprint_number(value, precision) for value in vertex) for vertex in self.vertices]
        ordered = sorted(enumerate(rounded), key=lambda item: (_coordinate_sort_key(item[1]), item[0]))
        remap = {old_index: new_index for new_index, (old_index, _) in enumerate(ordered)}
        canonical_vertices = [coords for _, coords in ordered]

        def reference(index: object) -> tuple[int, object]:
            if isinstance(index, int) and index in remap:
                return (0, remap[index])
            return (1, repr(index))

        canonical_edges = sorted(tuple(sorted(reference(index) for index in edge)) for edge in self.edges)
        face_keys = [_canonical_cycle(tuple(reference(index) for index in face)) for face in self.faces]
        canonical_faces = sorted(face_keys)
        canonical_regions = []
        for region in self.semantic_regions:
            valid = tuple(sorted(face_keys[index] for index in region.face_indices if 0 <= index < len(face_keys)))
            invalid = tuple(sorted(index for index in region.face_indices if index < 0 or index >= len(face_keys)))
            canonical_regions.append((region.name, valid, invalid))
        canonical_regions.sort()
        payload = {
            "vertices": canonical_vertices,
            "edges": canonical_edges,
            "faces": canonical_faces,
            "regions": canonical_regions,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def signed_volume(self) -> float:
        volume = 0.0
        for face in self.faces:
            if len(face) < 3:
                continue
            a = self.vertices[face[0]]
            for index in range(1, len(face) - 1):
                b = self.vertices[face[index]]
                c = self.vertices[face[index + 1]]
                volume += _dot(a, _cross(b, c)) / 6.0
        return volume


def _canonical_cycle(values: tuple[object, ...]) -> tuple[object, ...]:
    if not values:
        return values
    return min(values[index:] + values[:index] for index in range(len(values)))


def _fingerprint_number(value: object, precision: int) -> float | str:
    number = float(value)
    if math.isnan(number):
        return "NaN"
    if math.isinf(number):
        return "+Infinity" if number > 0.0 else "-Infinity"
    return round(number, precision)


def _coordinate_sort_key(values: tuple[float | str, ...]) -> tuple[tuple[int, object], ...]:
    return tuple((0, value) if isinstance(value, float) else (1, value) for value in values)


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def combine_bounds(bounds: Iterable[Bounds3]) -> Bounds3:
    items = tuple(bounds)
    if not items:
        raise GeometryError("Cannot combine an empty bounds sequence")
    return Bounds3(
        tuple(min(item.minimum[axis] for item in items) for axis in range(3)),
        tuple(max(item.maximum[axis] for item in items) for axis in range(3)),
    )

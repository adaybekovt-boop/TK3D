from __future__ import annotations

import itertools
import math
from collections import defaultdict, deque
from typing import Iterable

import bmesh
from mathutils import Vector

from ..builders.base import BuildArtifact, ContactExpectation
from ..geometry.blender import MaterializedArtifact
from ..geometry.model import Bounds3, TopologyIntent
from .model import Issue, Severity, ValidationReport
from .profiles import TolerancePolicy


def validate_materialized(
    materialized: MaterializedArtifact,
    *,
    stage: str = "POST_BUILD",
) -> ValidationReport:
    artifact = materialized.artifact
    obj = materialized.object
    contract = artifact.contract
    tolerance = TolerancePolicy.from_contract(contract)
    report = ValidationReport(
        entity=artifact.entity_id,
        artifact=artifact.artifact_id,
        profile=contract.topology_intent.value,
        stage=stage,
    )
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        bm.verts.index_update()
        bm.edges.index_update()
        bm.faces.index_update()
        bm.normal_update()

        non_finite = [
            vert.index for vert in bm.verts if not all(math.isfinite(float(value)) for value in vert.co)
        ]
        edge_lengths = {edge.index: edge.calc_length() for edge in bm.edges}
        finite_edge_lengths = [length for length in edge_lengths.values() if math.isfinite(length)]
        zero_edges = [index for index, length in edge_lengths.items() if length <= tolerance.length_epsilon]
        short_edges = [
            index
            for index, length in edge_lengths.items()
            if tolerance.length_epsilon < length < contract.minimum_feature_size - tolerance.length_epsilon
        ]
        zero_faces = [face.index for face in bm.faces if face.calc_area() <= tolerance.area_epsilon]
        loose_vertices = [vert.index for vert in bm.verts if not vert.link_edges and not vert.link_faces]
        wire_edges = [edge.index for edge in bm.edges if edge.is_wire]
        boundary_edges = [edge.index for edge in bm.edges if edge.is_boundary]
        overloaded_edges = [edge.index for edge in bm.edges if len(edge.link_faces) > 2]
        inconsistent_edges = [
            edge.index for edge in bm.edges if edge.is_manifold and not edge.is_contiguous
        ]
        duplicate_vertex_pairs = _near_duplicate_pairs(bm, tolerance.duplicate_epsilon)
        duplicate_faces = _duplicate_face_indices(bm)
        component_count = _component_count(bm)
        boundary_loop_count, boundary_is_closed = _boundary_components(bm)
        bounds = _bounds_from_bmesh(bm)
        signed_volume = _signed_volume(bm)

        report.metrics.update(
            {
                "vertices": len(bm.verts),
                "edges": len(bm.edges),
                "faces": len(bm.faces),
                "boundary_edges": len(boundary_edges),
                "boundary_loops": boundary_loop_count,
                "wire_edges": len(wire_edges),
                "edges_gt_2_faces": len(overloaded_edges),
                "degenerate_faces": len(zero_faces),
                "zero_length_edges": len(zero_edges),
                "minimum_edge_length": min(finite_edge_lengths, default=None),
                "loose_vertices": len(loose_vertices),
                "duplicate_vertex_pairs": len(duplicate_vertex_pairs),
                "duplicate_faces": len(duplicate_faces),
                "components": component_count,
                "signed_volume": signed_volume,
                "bounds": bounds.to_dict() if bounds else None,
            }
        )

        _add(report, "GEOM.NON_FINITE_VERTEX", "mesh contains non-finite coordinates", non_finite)
        _add(report, "GEOM.ZERO_LENGTH_EDGE", "mesh contains zero-length edges", zero_edges)
        _add(
            report,
            "GEOM.FEATURE_TOO_SMALL",
            "mesh contains an edge below the contract minimum feature size",
            short_edges,
        )
        _add(report, "GEOM.ZERO_AREA_FACE", "mesh contains zero-area faces", zero_faces)
        _add(report, "TOPO.LOOSE_VERTEX", "mesh contains loose vertices", loose_vertices)
        _add(report, "TOPO.WIRE_EDGE", "mesh contains wire edges", wire_edges)
        _add(report, "TOPO.EDGE_GT_TWO_FACES", "an edge is used by more than two faces", overloaded_edges)
        _add(report, "TOPO.INCONSISTENT_WINDING", "adjacent faces have inconsistent winding", inconsistent_edges)
        _add(
            report,
            "GEOM.DUPLICATE_VERTEX",
            "mesh contains near-duplicate vertex positions",
            duplicate_vertex_pairs,
        )
        _add(report, "TOPO.DUPLICATE_FACE", "mesh contains duplicate faces", duplicate_faces)

        if component_count != contract.expected_component_count:
            report.issues.append(
                Issue(
                    "TOPO.COMPONENT_COUNT",
                    f"expected {contract.expected_component_count} component(s), found {component_count}",
                )
            )

        if contract.topology_intent in {TopologyIntent.SOLID, TopologyIntent.ASSEMBLY}:
            _add(report, "TOPO.BOUNDARY_EDGE", "closed topology has boundary edges", boundary_edges)
            if not boundary_edges and bm.faces and signed_volume is not None and signed_volume < -tolerance.volume_epsilon:
                report.issues.append(
                    Issue("TOPO.INWARD_ORIENTATION", "solid face orientation points inward")
                )
            elif (
                not boundary_edges
                and bm.faces
                and signed_volume is not None
                and abs(signed_volume) <= tolerance.volume_epsilon
            ):
                report.issues.append(
                    Issue("GEOM.ZERO_VOLUME_SOLID", "closed solid has zero or near-zero signed volume")
                )
        elif contract.topology_intent is TopologyIntent.OPEN_SURFACE:
            expected = contract.allowed_boundaries
            if expected is None and boundary_edges:
                _add(report, "TOPO.UNEXPECTED_BOUNDARY", "open surface has no boundary contract", boundary_edges)
            elif expected is not None:
                if boundary_loop_count != expected.expected_loop_count or not boundary_is_closed:
                    report.issues.append(
                        Issue(
                            "TOPO.BOUNDARY_CONTRACT",
                            f"expected {expected.expected_loop_count} closed boundary loop(s), found {boundary_loop_count}",
                        )
                    )
                if expected.expected_edge_count is not None and len(boundary_edges) != expected.expected_edge_count:
                    report.issues.append(
                        Issue(
                            "TOPO.BOUNDARY_EDGE_COUNT",
                            f"expected {expected.expected_edge_count} boundary edges, found {len(boundary_edges)}",
                        )
                    )

        scale = tuple(float(value) for value in obj.scale)
        scale_is_finite = all(math.isfinite(value) for value in scale)
        report.metrics["object_scale"] = [value if math.isfinite(value) else None for value in scale]
        if not scale_is_finite:
            report.issues.append(Issue("TRANSFORM.NON_FINITE_SCALE", "generated object scale must be finite"))
        elif any(abs(value - 1.0) > tolerance.scale_epsilon for value in scale):
            report.issues.append(Issue("TRANSFORM.NON_UNIT_SCALE", "generated object scale must be (1, 1, 1)"))

        if bounds is None:
            report.issues.append(Issue("GEOMETRY.EMPTY", "mesh contains no vertices"))
        else:
            _compare_bounds(
                report,
                bounds,
                contract.local_bounds,
                tolerance.length_epsilon,
                tolerance.relative_length_epsilon,
            )
            _compare_dimensions(
                report,
                bounds.dimensions,
                contract.dimensions,
                tolerance.length_epsilon,
                tolerance.relative_length_epsilon,
                max(abs(value) for value in contract.local_bounds.minimum + contract.local_bounds.maximum),
            )
    finally:
        bm.free()
    return report


def validate_contacts(
    materialized: Iterable[MaterializedArtifact],
    contacts: Iterable[ContactExpectation],
) -> ValidationReport:
    items = {item.artifact.artifact_id: item for item in materialized}
    report = ValidationReport("__scene__", "__contacts__", "ASSEMBLY", "SCENE_CONTACTS")
    tested = 0
    for contact in contacts:
        tested += 1
        first = items.get(contact.first_artifact_id)
        second = items.get(contact.second_artifact_id)
        if first is None or second is None:
            report.issues.append(
                Issue(
                    "SCENE.CONTACT_TARGET_MISSING",
                    "expected contact references a missing artifact",
                    samples=((contact.first_artifact_id, contact.second_artifact_id),),
                )
            )
            continue
        distance = _world_aabb_distance(first, second)
        if distance > contact.tolerance:
            report.issues.append(
                Issue(
                    "SCENE.EXPECTED_CONTACT_MISSING",
                    f"expected artifacts to touch within {contact.tolerance:.6g}m; gap is {distance:.6g}m",
                    samples=((contact.first_artifact_id, contact.second_artifact_id),),
                )
            )
    report.metrics["contacts_tested"] = tested
    return report


def _add(
    report: ValidationReport,
    code: str,
    message: str,
    samples: Iterable[object],
    severity: Severity = Severity.ERROR,
) -> None:
    values = tuple(samples)
    if values:
        report.issues.append(Issue(code, message, severity, len(values), values[:8]))


def _near_duplicate_pairs(bm: bmesh.types.BMesh, epsilon: float) -> tuple[tuple[int, int], ...]:
    if epsilon <= 0.0:
        return ()
    buckets: dict[tuple[int, int, int], list[bmesh.types.BMVert]] = defaultdict(list)
    result: list[tuple[int, int]] = []
    epsilon_squared = epsilon * epsilon
    for vert in bm.verts:
        if not all(math.isfinite(float(value)) for value in vert.co):
            continue
        key = tuple(math.floor(float(value) / epsilon) for value in vert.co)
        for delta in itertools.product((-1, 0, 1), repeat=3):
            neighbor = tuple(key[axis] + delta[axis] for axis in range(3))
            for other in buckets.get(neighbor, ()):  # only previously visited vertices
                if (vert.co - other.co).length_squared <= epsilon_squared:
                    result.append((other.index, vert.index))
        buckets[key].append(vert)
    return tuple(result)


def _duplicate_face_indices(bm: bmesh.types.BMesh) -> tuple[tuple[int, int], ...]:
    seen: dict[tuple[int, ...], int] = {}
    duplicates: list[tuple[int, int]] = []
    for face in bm.faces:
        key = tuple(sorted(vert.index for vert in face.verts))
        if key in seen:
            duplicates.append((seen[key], face.index))
        else:
            seen[key] = face.index
    return tuple(duplicates)


def _component_count(bm: bmesh.types.BMesh) -> int:
    unseen = set(bm.verts)
    components = 0
    while unseen:
        components += 1
        start = unseen.pop()
        queue = [start]
        while queue:
            vert = queue.pop()
            for edge in vert.link_edges:
                other = edge.other_vert(vert)
                if other in unseen:
                    unseen.remove(other)
                    queue.append(other)
    return components


def _boundary_components(bm: bmesh.types.BMesh) -> tuple[int, bool]:
    edges = [edge for edge in bm.edges if edge.is_boundary]
    if not edges:
        return 0, True
    adjacency: dict[bmesh.types.BMVert, list[bmesh.types.BMEdge]] = defaultdict(list)
    for edge in edges:
        for vert in edge.verts:
            adjacency[vert].append(edge)
    unseen = set(edges)
    components = 0
    while unseen:
        components += 1
        start = unseen.pop()
        queue = deque([start])
        while queue:
            edge = queue.popleft()
            for vert in edge.verts:
                for neighbor in adjacency[vert]:
                    if neighbor in unseen:
                        unseen.remove(neighbor)
                        queue.append(neighbor)
    closed = all(len(linked) == 2 for linked in adjacency.values())
    return components, closed


def _bounds_from_bmesh(bm: bmesh.types.BMesh) -> Bounds3 | None:
    if not bm.verts:
        return None
    vertices = [
        tuple(float(value) for value in vert.co)
        for vert in bm.verts
        if all(math.isfinite(float(value)) for value in vert.co)
    ]
    if not vertices:
        return None
    return Bounds3.from_vertices(vertices)


def _signed_volume(bm: bmesh.types.BMesh) -> float | None:
    volume = 0.0
    for face in bm.faces:
        coordinates = [vert.co for vert in face.verts]
        if any(not all(math.isfinite(float(value)) for value in coordinate) for coordinate in coordinates):
            return None
        if len(coordinates) < 3:
            continue
        a = coordinates[0]
        for index in range(1, len(coordinates) - 1):
            b = coordinates[index]
            c = coordinates[index + 1]
            volume += float(a.dot(b.cross(c))) / 6.0
    return volume


def _within_length_tolerance(
    actual: float,
    expected: float,
    absolute: float,
    relative: float,
    reference_scale: float = 0.0,
) -> bool:
    allowed = max(absolute, relative * max(1.0, abs(actual), abs(expected), reference_scale))
    return abs(actual - expected) <= allowed


def _compare_bounds(
    report: ValidationReport,
    actual: Bounds3,
    expected: Bounds3,
    absolute: float,
    relative: float,
) -> None:
    values = tuple(zip(actual.minimum + actual.maximum, expected.minimum + expected.maximum))
    if any(not _within_length_tolerance(left, right, absolute, relative) for left, right in values):
        report.issues.append(Issue("GEOM.BOUNDS_MISMATCH", "mesh bounds do not match the geometry contract"))


def _compare_dimensions(
    report: ValidationReport,
    actual: tuple[float, float, float],
    expected: tuple[float, float, float],
    absolute: float,
    relative: float,
    coordinate_scale: float,
) -> None:
    if any(
        not _within_length_tolerance(actual[axis], expected[axis], absolute, relative, coordinate_scale)
        for axis in range(3)
    ):
        report.issues.append(Issue("GEOM.DIMENSIONS_MISMATCH", "mesh dimensions do not match the geometry contract"))


def _world_aabb_distance(first: MaterializedArtifact, second: MaterializedArtifact) -> float:
    def bounds(item: MaterializedArtifact) -> tuple[Vector, Vector]:
        points = [item.object.matrix_world @ Vector(corner) for corner in item.object.bound_box]
        minimum = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
        maximum = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
        return minimum, maximum

    first_min, first_max = bounds(first)
    second_min, second_max = bounds(second)
    gaps = [max(first_min[axis] - second_max[axis], second_min[axis] - first_max[axis], 0.0) for axis in range(3)]
    return math.sqrt(sum(value * value for value in gaps))

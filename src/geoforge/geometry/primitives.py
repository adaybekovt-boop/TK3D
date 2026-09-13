from __future__ import annotations

import math
from typing import Iterable, Sequence

from ..errors import GeometryError
from .model import MeshDraft, SemanticRegion, Vec2, Vec3


def rectangular_prism(
    minimum: Vec3,
    maximum: Vec3,
    *,
    name: str = "rectangular_prism",
) -> MeshDraft:
    if not all(math.isfinite(value) for value in (*minimum, *maximum)):
        raise GeometryError("Prism bounds must be finite", code="GEOM.NON_FINITE_VERTEX")
    if any(maximum[axis] <= minimum[axis] for axis in range(3)):
        raise GeometryError("Prism maximum must be greater than minimum on every axis")
    x0, y0, z0 = minimum
    x1, y1, z1 = maximum
    vertices = (
        (x0, y0, z0),
        (x1, y0, z0),
        (x1, y1, z0),
        (x0, y1, z0),
        (x0, y0, z1),
        (x1, y0, z1),
        (x1, y1, z1),
        (x0, y1, z1),
    )
    faces = (
        (0, 3, 2, 1),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (1, 2, 6, 5),
        (2, 3, 7, 6),
        (3, 0, 4, 7),
    )
    regions = (
        SemanticRegion("bottom", (0,)),
        SemanticRegion("top", (1,)),
        SemanticRegion("sides", (2, 3, 4, 5)),
    )
    return MeshDraft(name=name, vertices=vertices, faces=faces, semantic_regions=regions)


def box(
    width: float,
    depth: float,
    height: float,
    *,
    origin: Vec3 = (0.0, 0.0, 0.0),
    name: str = "box",
) -> MeshDraft:
    if min(width, depth, height) <= 0.0:
        raise GeometryError("Box dimensions must be > 0")
    return rectangular_prism(
        origin,
        (origin[0] + width, origin[1] + depth, origin[2] + height),
        name=name,
    )


def plane(
    width: float,
    depth: float,
    *,
    origin: Vec3 = (0.0, 0.0, 0.0),
    name: str = "plane",
) -> MeshDraft:
    if width <= 0.0 or depth <= 0.0:
        raise GeometryError("Plane dimensions must be > 0")
    x0, y0, z = origin
    vertices = (
        (x0, y0, z),
        (x0 + width, y0, z),
        (x0 + width, y0 + depth, z),
        (x0, y0 + depth, z),
    )
    return MeshDraft(
        name=name,
        vertices=vertices,
        faces=((0, 1, 2, 3),),
        semantic_regions=(SemanticRegion("surface", (0,)),),
    )


def extrude_profile(
    profile: Sequence[Vec2],
    depth: float,
    *,
    axis: str = "Z",
    name: str = "extruded_profile",
) -> MeshDraft:
    if depth <= 0.0 or not math.isfinite(depth):
        raise GeometryError("Extrusion depth must be finite and > 0")
    points = [tuple(map(float, point)) for point in profile]
    if len(points) >= 2 and points[0] == points[-1]:
        points.pop()
    if len(points) < 3 or len(set(points)) < 3:
        raise GeometryError("Profile must contain at least three unique points")
    if not all(math.isfinite(value) for point in points for value in point):
        raise GeometryError("Profile coordinates must be finite", code="GEOM.NON_FINITE_VERTEX")
    area = _signed_area(points)
    if math.isclose(area, 0.0, abs_tol=1e-15):
        raise GeometryError("Profile area must be non-zero")
    if area < 0.0:
        points.reverse()

    axis = axis.upper()
    if axis not in {"X", "Y", "Z"}:
        raise GeometryError("Extrusion axis must be X, Y, or Z")

    orientation = -1 if axis == "Y" else 1
    base = [_embed(u, v, 0.0, axis) for u, v in points]
    top = [_embed(u, v, depth, axis) for u, v in points]
    vertices = tuple(base + top)
    count = len(points)
    if orientation > 0:
        bottom_face = tuple(reversed(range(count)))
        top_face = tuple(range(count, count * 2))
    else:
        bottom_face = tuple(range(count))
        top_face = tuple(reversed(range(count, count * 2)))

    side_faces: list[tuple[int, int, int, int]] = []
    for index in range(count):
        following = (index + 1) % count
        if orientation > 0:
            side_faces.append((index, following, count + following, count + index))
        else:
            side_faces.append((index, count + index, count + following, following))
    faces = (bottom_face, top_face, *side_faces)
    regions = (
        SemanticRegion("cap_start", (0,)),
        SemanticRegion("cap_end", (1,)),
        SemanticRegion("sides", tuple(range(2, len(faces)))),
    )
    return MeshDraft(name=name, vertices=vertices, faces=tuple(faces), semantic_regions=regions)


def merge_drafts(drafts: Iterable[MeshDraft], *, name: str = "merged") -> MeshDraft:
    items = tuple(drafts)
    if not items:
        raise GeometryError("At least one draft is required")
    vertices: list[Vec3] = []
    edges: list[tuple[int, int]] = []
    faces: list[tuple[int, ...]] = []
    regions: list[SemanticRegion] = []
    vertex_offset = 0
    face_offset = 0
    for draft in items:
        draft.validate_or_raise()
        vertices.extend(draft.vertices)
        edges.extend((a + vertex_offset, b + vertex_offset) for a, b in draft.edges)
        faces.extend(tuple(index + vertex_offset for index in face) for face in draft.faces)
        regions.extend(
            SemanticRegion(
                f"{draft.name}.{region.name}",
                tuple(index + face_offset for index in region.face_indices),
            )
            for region in draft.semantic_regions
        )
        vertex_offset += len(draft.vertices)
        face_offset += len(draft.faces)
    return MeshDraft(name, tuple(vertices), tuple(edges), tuple(faces), tuple(regions))


def _signed_area(points: Sequence[Vec2]) -> float:
    return 0.5 * sum(
        points[index][0] * points[(index + 1) % len(points)][1]
        - points[(index + 1) % len(points)][0] * points[index][1]
        for index in range(len(points))
    )


def _embed(u: float, v: float, w: float, axis: str) -> Vec3:
    if axis == "Z":
        return (u, v, w)
    if axis == "Y":
        return (u, w, v)
    return (w, u, v)


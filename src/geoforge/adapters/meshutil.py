from __future__ import annotations

import math

from ..geometry.model import MeshDraft, Vec3
from ..geometry.primitives import rectangular_prism


def translate_draft(draft: MeshDraft, offset: Vec3, *, name: str | None = None) -> MeshDraft:
    dx, dy, dz = offset
    return MeshDraft(
        name=name or draft.name,
        vertices=tuple((x + dx, y + dy, z + dz) for x, y, z in draft.vertices),
        edges=draft.edges,
        faces=draft.faces,
        semantic_regions=draft.semantic_regions,
    )


def rotate_draft_x(draft: MeshDraft, radians: float, *, name: str | None = None) -> MeshDraft:
    cosine = math.cos(radians)
    sine = math.sin(radians)
    return MeshDraft(
        name=name or draft.name,
        vertices=tuple((x, y * cosine - z * sine, y * sine + z * cosine) for x, y, z in draft.vertices),
        edges=draft.edges,
        faces=draft.faces,
        semantic_regions=draft.semantic_regions,
    )


def box_at(minimum: Vec3, maximum: Vec3, *, name: str) -> MeshDraft:
    return rectangular_prism(minimum, maximum, name=name)

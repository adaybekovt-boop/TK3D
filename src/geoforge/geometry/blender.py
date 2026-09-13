from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any

import bmesh
import bpy

from ..builders.base import BuildArtifact


@dataclass(frozen=True)
class MaterializedArtifact:
    artifact: BuildArtifact
    object: bpy.types.Object
    mesh: bpy.types.Mesh


def materialize_artifact(
    artifact: BuildArtifact,
    collection: bpy.types.Collection,
) -> MaterializedArtifact:
    mesh = bpy.data.meshes.new(f"{artifact.object_name}__Mesh")
    mesh.from_pydata(artifact.draft.vertices, artifact.draft.edges, artifact.draft.faces)
    mesh.update(calc_edges=True, calc_edges_loose=True)
    obj = bpy.data.objects.new(artifact.object_name, mesh)
    collection.objects.link(obj)
    obj.location = artifact.transform.position
    obj.rotation_euler = (0.0, 0.0, math.radians(artifact.transform.yaw_deg))
    obj.scale = (1.0, 1.0, 1.0)
    obj["gf_entity_id"] = artifact.entity_id
    obj["gf_artifact_id"] = artifact.artifact_id
    obj["gf_builder_id"] = artifact.builder_id
    obj["gf_builder_version"] = artifact.builder_version
    obj["gf_entity_seed"] = str(artifact.entity_seed)
    obj["gf_entity_spec_hash"] = artifact.entity_spec_hash
    obj["gf_spec_hash"] = artifact.scene_spec_hash
    obj["gf_mesh_fingerprint"] = artifact.draft.fingerprint()
    obj["gf_topology_intent"] = artifact.contract.topology_intent.value
    obj["gf_contract"] = json.dumps(
        {
            "bounds": artifact.contract.local_bounds.to_dict(),
            "dimensions": list(artifact.contract.dimensions),
            "expected_component_count": artifact.contract.expected_component_count,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    obj["gf_target_name"] = artifact.object_name
    return MaterializedArtifact(artifact, obj, mesh)


def evaluated_mesh_copy(
    obj: bpy.types.Object,
    *,
    preserve_all_data_layers: bool = True,
) -> bpy.types.Mesh:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    return bpy.data.meshes.new_from_object(
        evaluated,
        preserve_all_data_layers=preserve_all_data_layers,
        depsgraph=depsgraph,
    )


def save_blend_file(filepath: str) -> bool:
    """Save the current file while avoiding out-of-workspace thumbnail caches.

    ``file_preview_type`` is available in current Blender, but the guarded
    access keeps this compatibility detail out of the orchestration layer.
    """
    filepaths = bpy.context.preferences.filepaths
    previous_preview = getattr(filepaths, "file_preview_type", None)
    previous_save_version = getattr(filepaths, "save_version", None)
    try:
        if previous_preview is not None:
            filepaths.file_preview_type = "NONE"
        if previous_save_version is not None:
            filepaths.save_version = 0
        result = bpy.ops.wm.save_as_mainfile(filepath=filepath, check_existing=False)
    finally:
        if previous_preview is not None:
            filepaths.file_preview_type = previous_preview
        if previous_save_version is not None:
            filepaths.save_version = previous_save_version
    return "FINISHED" in result


def capability_probe() -> dict[str, Any]:
    edge_type = bmesh.types.BMEdge
    probe_mesh = bpy.data.meshes.new("GF__CapabilityProbe")
    try:
        return {
            "blender_version": bpy.app.version_string,
            "blender_version_tuple": list(bpy.app.version),
            "background": bool(bpy.app.background),
            "bmesh_predicates": {
                name: hasattr(edge_type, name)
                for name in ("is_boundary", "is_manifold", "is_wire", "is_contiguous")
            },
            "evaluated_mesh": hasattr(bpy.data.meshes, "new_from_object"),
            "mesh_validate": hasattr(probe_mesh, "validate"),
            "mesh_from_pydata": hasattr(probe_mesh, "from_pydata"),
            "file_preview_control": hasattr(bpy.context.preferences.filepaths, "file_preview_type"),
            "save_version_control": hasattr(bpy.context.preferences.filepaths, "save_version"),
        }
    finally:
        bpy.data.meshes.remove(probe_mesh)

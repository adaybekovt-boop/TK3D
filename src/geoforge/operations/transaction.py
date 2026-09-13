from __future__ import annotations

import uuid

import bpy

from ..builders.base import BuildArtifact
from ..geometry.blender import MaterializedArtifact, materialize_artifact
from ..scene import get_or_create_collection, remove_object_and_data


class StagingTransaction:
    def __init__(self, *, final_collection_name: str = "GF_FINAL") -> None:
        self.final_collection_name = final_collection_name
        self.staging_name = f"GF_STAGING_{uuid.uuid4().hex[:12]}"
        self.staging_collection = bpy.data.collections.new(self.staging_name)
        bpy.context.scene.collection.children.link(self.staging_collection)
        self.items: list[MaterializedArtifact] = []
        self.state = "OPEN"

    def materialize(self, artifact: BuildArtifact) -> MaterializedArtifact:
        if self.state != "OPEN":
            raise RuntimeError("transaction is not open")
        item = materialize_artifact(artifact, self.staging_collection)
        self.items.append(item)
        return item

    def commit(self) -> list[str]:
        if self.state != "OPEN":
            raise RuntimeError("transaction is not open")
        final = get_or_create_collection(self.final_collection_name)
        entity_ids = {item.artifact.entity_id for item in self.items}
        new_objects = {item.object for item in self.items}
        old_objects = [
            obj
            for obj in list(final.objects)
            if obj not in new_objects and obj.get("gf_entity_id") in entity_ids
        ]

        for item in self.items:
            if final.objects.get(item.object.name) is None:
                final.objects.link(item.object)
        for obj in old_objects:
            remove_object_and_data(obj)
        for item in self.items:
            if self.staging_collection.objects.get(item.object.name) is not None:
                self.staging_collection.objects.unlink(item.object)
            target_name = item.object.get("gf_target_name", item.artifact.object_name)
            item.object.name = target_name
            item.object.data.name = f"{target_name}__Mesh"

        bpy.data.collections.remove(self.staging_collection)
        self.state = "COMMITTED"
        return [item.object.name for item in self.items]

    def rollback(self) -> None:
        if self.state != "OPEN":
            return
        for item in reversed(self.items):
            try:
                object_name = item.object.name
            except ReferenceError:
                continue
            if bpy.data.objects.get(object_name) is not None:
                remove_object_and_data(item.object)
        if bpy.data.collections.get(self.staging_name) is not None:
            bpy.data.collections.remove(self.staging_collection)
        self.state = "ROLLED_BACK"

    def __enter__(self) -> "StagingTransaction":
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        if self.state == "OPEN":
            self.rollback()
        return False

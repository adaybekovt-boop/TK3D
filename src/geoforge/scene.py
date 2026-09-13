from __future__ import annotations

import bpy


def get_or_create_collection(name: str) -> bpy.types.Collection:
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
    if collection.name not in {item.name for item in bpy.context.scene.collection.children}:
        bpy.context.scene.collection.children.link(collection)
    return collection


def remove_object_and_data(obj: bpy.types.Object) -> None:
    data = obj.data if obj.type == "MESH" else None
    bpy.data.objects.remove(obj, do_unlink=True)
    if data is not None and data.users == 0:
        bpy.data.meshes.remove(data)


def remove_collection_if_present(name: str) -> None:
    collection = bpy.data.collections.get(name)
    if collection is None:
        return
    for obj in list(collection.objects):
        remove_object_and_data(obj)
    bpy.data.collections.remove(collection)


from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


FRAMEWORK_VERSION = "0.1.0"


@dataclass(frozen=True)
class ArtifactRecord:
    artifact_id: str
    entity_id: str
    object_name: str
    builder_id: str
    builder_version: str
    entity_seed: int
    entity_spec_hash: str
    mesh_fingerprint: str
    topology_intent: str
    published: bool

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass
class BuildManifest:
    scene_id: str
    spec_hash: str
    global_seed: int
    blender_version: str
    status: str = "FAIL"
    framework_version: str = FRAMEWORK_VERSION
    artifacts: list[ArtifactRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "framework_version": self.framework_version,
            "blender_version": self.blender_version,
            "scene_id": self.scene_id,
            "spec_hash": self.spec_hash,
            "global_seed": self.global_seed,
            "artifacts": [item.to_dict() for item in self.artifacts],
        }


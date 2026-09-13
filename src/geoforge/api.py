from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from .pipeline import DraftCompilation, PipelineResult, RegenerationGuard, compile_drafts
from .registry import BuilderRegistry, create_default_registry, create_full_registry, describe_builder
from .spec import SceneSpec, decode_scene_spec, load_scene_spec, validate_scene_spec


def compile_scene(
    spec: SceneSpec,
    *,
    output_root: str | Path = ".",
    registry: BuilderRegistry | None = None,
) -> PipelineResult:
    from .pipeline import compile_scene as run_pipeline

    return run_pipeline(spec, output_root=output_root, registry=registry)


def regenerate_entity(
    spec: SceneSpec,
    entity_id: str,
    *,
    output_root: str | Path = ".",
    registry: BuilderRegistry | None = None,
    guard: RegenerationGuard | None = None,
) -> PipelineResult:
    from .pipeline import compile_scene as run_pipeline

    return run_pipeline(
        spec,
        output_root=output_root,
        registry=registry,
        entity_ids={entity_id},
        regeneration_guard=guard,
    )


__all__ = [
    "BuilderRegistry",
    "DraftCompilation",
    "PipelineResult",
    "RegenerationGuard",
    "SceneSpec",
    "compile_drafts",
    "compile_scene",
    "create_default_registry",
    "create_full_registry",
    "decode_scene_spec",
    "describe_builder",
    "load_scene_spec",
    "regenerate_entity",
    "validate_scene_spec",
]


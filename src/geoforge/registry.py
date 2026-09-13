from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .errors import SpecError


@dataclass(frozen=True)
class BuilderDescriptor:
    kind: str
    version: str
    class_name: str
    required_params: tuple[str, ...]
    optional_params: tuple[str, ...]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "version": self.version,
            "required_params": list(self.required_params),
            "optional_params": list(self.optional_params),
            "summary": self.summary,
        }


class BuilderRegistry:
    def __init__(self) -> None:
        self._builders: dict[str, Any] = {}

    def register(self, builder: Any, *, replace: bool = False) -> None:
        kind = getattr(builder, "kind", None)
        version = getattr(builder, "version", None)
        if not isinstance(kind, str) or not isinstance(version, str):
            raise TypeError("builder must expose string kind and version")
        if kind in self._builders and not replace:
            raise ValueError(f"Builder {kind!r} is already registered")
        self._builders[kind] = builder

    def get(self, kind: str) -> Any:
        try:
            return self._builders[kind]
        except KeyError as exc:
            raise SpecError(
                f"No builder registered for {kind!r}",
                code="SPEC.UNSUPPORTED_FEATURE",
                path="/entities/kind",
            ) from exc

    def describe(self, kind: str | None = None) -> tuple[BuilderDescriptor, ...]:
        keys = [kind] if kind is not None else sorted(self._builders)
        result = []
        for key in keys:
            builder = self.get(key)
            result.append(
                BuilderDescriptor(
                    key,
                    builder.version,
                    type(builder).__name__,
                    tuple(getattr(builder, "required_params", ())),
                    tuple(getattr(builder, "optional_params", ())),
                    str(getattr(builder, "summary", "")),
                )
            )
        return tuple(result)


def create_full_registry() -> BuilderRegistry:
    """V1 builders plus registered donor adapters."""
    registry = create_default_registry()
    from .adapters import register_adapters

    register_adapters(registry)
    return registry


def create_default_registry() -> BuilderRegistry:
    from .builders.architecture import (
        BeamBuilder,
        BoxBuilder,
        CeilingBuilder,
        ColumnBuilder,
        FloorBuilder,
        RoomBuilder,
        WallBuilder,
    )
    from .builders.circulation import StraightStairsBuilder

    registry = BuilderRegistry()
    for builder_type in (
        BoxBuilder,
        WallBuilder,
        RoomBuilder,
        FloorBuilder,
        CeilingBuilder,
        StraightStairsBuilder,
        BeamBuilder,
        ColumnBuilder,
    ):
        registry.register(builder_type())
    return registry


def describe_builder(kind: str | None = None) -> list[dict[str, Any]]:
    return [descriptor.to_dict() for descriptor in create_default_registry().describe(kind)]

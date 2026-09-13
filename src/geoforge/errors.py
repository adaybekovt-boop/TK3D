from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ErrorDetail:
    code: str
    message: str
    path: str = ""
    context: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.path:
            result["path"] = self.path
        if self.context:
            result["context"] = dict(self.context)
        return result


class GeoForgeError(Exception):
    """Base error with a stable machine-readable code."""

    default_code = "GEOFORGE.ERROR"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        path: str = "",
        context: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.detail = ErrorDetail(code or self.default_code, message, path, context)

    @property
    def code(self) -> str:
        return self.detail.code

    def to_dict(self) -> dict[str, Any]:
        return self.detail.to_dict()


class SpecError(GeoForgeError):
    default_code = "SPEC.INVALID"


class UnsupportedFeatureError(SpecError):
    default_code = "SPEC.UNSUPPORTED_FEATURE"


class GeometryError(GeoForgeError):
    default_code = "GEOMETRY.INVALID_DRAFT"


class BuildError(GeoForgeError):
    default_code = "BUILD.FAILED"


class QualityGateError(BuildError):
    default_code = "QUALITY_GATE.FAILED"


class BlenderUnavailableError(BuildError):
    default_code = "BLENDER.UNAVAILABLE"


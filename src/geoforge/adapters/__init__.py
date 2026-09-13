from __future__ import annotations

from .balcony import BalconyBuilder
from .base import GeneratorAdapter
from .desk import SimpleDeskBuilder
from .ladder import ClimbableLadderBuilder
from .railing import RailingBuilder
from .road import RoadBuilder
from .schema import SCHEMAS, is_adapter_kind, public_param_schema, public_param_schema_for_generator

ADAPTER_BUILDERS = (
    ClimbableLadderBuilder,
    RailingBuilder,
    BalconyBuilder,
    RoadBuilder,
    SimpleDeskBuilder,
)


def register_adapters(registry) -> None:
    for builder_type in ADAPTER_BUILDERS:
        registry.register(builder_type())


__all__ = [
    "ADAPTER_BUILDERS",
    "BalconyBuilder",
    "ClimbableLadderBuilder",
    "GeneratorAdapter",
    "RailingBuilder",
    "RoadBuilder",
    "SCHEMAS",
    "SimpleDeskBuilder",
    "is_adapter_kind",
    "public_param_schema",
    "public_param_schema_for_generator",
    "register_adapters",
]

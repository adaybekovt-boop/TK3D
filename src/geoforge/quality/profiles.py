from __future__ import annotations

from dataclasses import dataclass

from ..geometry.model import GeometryContract


@dataclass(frozen=True)
class TolerancePolicy:
    length_epsilon: float
    relative_length_epsilon: float
    area_epsilon: float
    volume_epsilon: float
    duplicate_epsilon: float
    scale_epsilon: float

    @classmethod
    def from_contract(cls, contract: GeometryContract) -> "TolerancePolicy":
        feature = contract.minimum_feature_size
        length = max(1e-8, feature * 1e-5)
        return cls(
            length_epsilon=length,
            # Blender Mesh coordinates are IEEE-754 single precision.  Bounds
            # comparisons therefore need a small magnitude-scaled allowance in
            # addition to the contract's absolute modelling tolerance.
            relative_length_epsilon=2.0e-7,
            area_epsilon=length * length,
            volume_epsilon=length * length * length,
            duplicate_epsilon=length,
            scale_epsilon=1e-7,
        )

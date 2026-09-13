from __future__ import annotations

from dataclasses import dataclass

from ..quality.model import Severity, ValidationReport


TIER1_CODES = frozenset(
    {
        "GEOM.DUPLICATE_VERTEX",
        "GEOM.ZERO_LENGTH_EDGE",
        "GEOM.ZERO_AREA_FACE",
        "TOPO.LOOSE_VERTEX",
        "TOPO.WIRE_EDGE",
        "TOPO.INCONSISTENT_WINDING",
        "TOPO.INWARD_ORIENTATION",
    }
)


@dataclass(frozen=True)
class RepairDecision:
    allowed: bool
    tier: int | None
    reason: str


def decide_tier1(report: ValidationReport) -> RepairDecision:
    error_codes = {issue.code for issue in report.issues if issue.severity is Severity.ERROR}
    if not error_codes:
        return RepairDecision(False, None, "NO_ERRORS")
    allowed_codes = set(TIER1_CODES)
    if "TOPO.COMPONENT_COUNT" in error_codes and error_codes & {"TOPO.LOOSE_VERTEX", "TOPO.WIRE_EDGE"}:
        allowed_codes.add("TOPO.COMPONENT_COUNT")
    unsupported = error_codes - allowed_codes
    if unsupported:
        return RepairDecision(False, None, f"NON_REPAIRABLE:{','.join(sorted(unsupported))}")
    return RepairDecision(True, 1, "ALL_ERRORS_ARE_TIER1")

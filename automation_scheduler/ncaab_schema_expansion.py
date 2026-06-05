from __future__ import annotations

from typing import Any

from .basketball_free_vs_paid_readiness import build_sport_schema_expansion_report


def build_ncaab_schema_expansion_report(*, sample_verification_results: dict[str, Any] | None = None) -> dict[str, Any]:
    return build_sport_schema_expansion_report("basketball_ncaab", sample_verification_results=sample_verification_results)

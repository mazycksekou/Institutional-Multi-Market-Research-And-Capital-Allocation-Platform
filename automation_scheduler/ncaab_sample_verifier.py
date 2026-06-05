from __future__ import annotations

from typing import Any

from .basketball_free_vs_paid_readiness import build_sport_sample_report, write_sport_sample_report


def build_ncaab_sample_verification_report(*, run_live_samples: bool = False) -> dict[str, Any]:
    return build_sport_sample_report("basketball_ncaab", run_live_samples=run_live_samples)


def write_ncaab_sample_verification_report(report: dict[str, Any]) -> dict[str, str]:
    return write_sport_sample_report(report)

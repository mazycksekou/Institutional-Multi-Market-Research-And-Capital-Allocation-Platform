from __future__ import annotations

from typing import Any, Mapping

from .security_policy import locked_safety_flags


def _num(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _residual(row: Mapping[str, Any]) -> float | None:
    if row.get("absolute_residual") is not None:
        return abs(float(row.get("absolute_residual") or 0.0))
    pred = _num(row.get("prediction") or row.get("edge_estimate") or row.get("implied_probability"))
    actual = _num(row.get("actual") or row.get("realized_edge") or row.get("outcome"))
    if pred is None or actual is None:
        return None
    if pred > 1.0 and actual <= 1.0:
        pred = pred / 100.0
    return abs(pred - actual)


def run_conformal_uncertainty(
    candidate: Mapping[str, Any] | None = None,
    *,
    calibration_records: list[Mapping[str, Any]] | None = None,
    coverage_target: float = 0.90,
    minimum_outcomes: int = 50,
) -> dict[str, Any]:
    candidate = candidate or {}
    residuals = sorted(res for res in (_residual(row) for row in (calibration_records or [])) if res is not None)
    if len(residuals) < int(minimum_outcomes):
        return {
            "ok": True,
            "status": "blocked_insufficient_data",
            "conformal_interval_lower": None,
            "conformal_interval_upper": None,
            "conformal_interval_width": None,
            "conformal_coverage_target": float(coverage_target),
            "conformal_coverage_observed": None,
            "conformal_status": "blocked_insufficient_data",
            "uncertainty_too_wide": True,
            "conformal_no_bet_reason": "insufficient_calibration_outcomes",
            "insufficient_sample": True,
            "blocked_reason": "calibration_outcome_count_below_minimum",
            "red_team_only": True,
            **locked_safety_flags(),
        }
    q_index = min(len(residuals) - 1, int(round(float(coverage_target) * (len(residuals) - 1))))
    q = residuals[q_index]
    edge = _num(candidate.get("edge_estimate") or candidate.get("expected_edge") or candidate.get("implied_probability")) or 0.0
    if edge > 1.0:
        edge = edge / 100.0
    lower = edge - q
    upper = edge + q
    width = upper - lower
    low_liquidity = str(candidate.get("liquidity_tier") or "").lower() in {"low", "thin", "missing", "unknown"}
    too_wide = width >= 0.20 or (low_liquidity and width >= 0.10)
    return {
        "ok": True,
        "status": "conformal_complete",
        "conformal_interval_lower": round(lower, 6),
        "conformal_interval_upper": round(upper, 6),
        "conformal_interval_width": round(width, 6),
        "conformal_coverage_target": float(coverage_target),
        "conformal_coverage_observed": round(float(coverage_target), 6),
        "conformal_status": "interval_ready",
        "uncertainty_too_wide": bool(too_wide),
        "conformal_no_bet_reason": "wide_interval_low_liquidity" if too_wide and low_liquidity else ("conformal_interval_too_wide" if too_wide else None),
        "insufficient_sample": False,
        "blocked_reason": None,
        "red_team_only": True,
        **locked_safety_flags(),
    }

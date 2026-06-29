from __future__ import annotations

import math
from typing import Any, Mapping

from .security_policy import locked_safety_flags


def _num(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def run_bayesian_structural_baseline(
    candidate: Mapping[str, Any] | None = None,
    *,
    baseline_records: list[Mapping[str, Any]] | None = None,
    minimum_baseline_records: int = 30,
) -> dict[str, Any]:
    candidate = candidate or {}
    values = []
    for row in baseline_records or []:
        if not isinstance(row, Mapping):
            continue
        value = _num(row.get("outcome_value") or row.get("actual") or row.get("return") or row.get("delta"))
        if value is not None:
            values.append(value)
    if len(values) < int(minimum_baseline_records):
        return {
            "ok": True,
            "status": "blocked_insufficient_data",
            "counterfactual_estimate": None,
            "observed_vs_counterfactual_delta": None,
            "credible_interval_lower": None,
            "credible_interval_upper": None,
            "counterfactual_significance": "data_insufficient",
            "bayesian_baseline_status": "blocked_insufficient_data",
            "counterfactual_no_edge_warning": True,
            "insufficient_sample": True,
            "blocked_reason": "baseline_record_count_below_minimum",
            "red_team_only": True,
            **locked_safety_flags(),
        }
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / max(1, len(values) - 1)
    stderr = math.sqrt(variance) / math.sqrt(len(values))
    lower = mean - 1.96 * stderr
    upper = mean + 1.96 * stderr
    observed = _num(candidate.get("observed_outcome") or candidate.get("observed_value") or candidate.get("edge_estimate")) or mean
    delta = observed - mean
    crosses_no_edge = lower <= 0.0 <= upper
    return {
        "ok": True,
        "status": "bayesian_baseline_complete",
        "counterfactual_estimate": round(mean, 6),
        "observed_vs_counterfactual_delta": round(delta, 6),
        "credible_interval_lower": round(lower, 6),
        "credible_interval_upper": round(upper, 6),
        "counterfactual_significance": "not_significant" if crosses_no_edge else ("positive" if delta > 0 else "negative"),
        "bayesian_baseline_status": "deterministic_normal_baseline_fallback",
        "counterfactual_no_edge_warning": bool(crosses_no_edge),
        "insufficient_sample": False,
        "blocked_reason": None,
        "red_team_only": True,
        **locked_safety_flags(),
    }

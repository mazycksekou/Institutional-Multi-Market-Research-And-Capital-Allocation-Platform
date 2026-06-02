from __future__ import annotations

import math
from typing import Any

from .security_policy import locked_safety_flags


MIN_BASELINE_SAMPLE_SIZE = 30


def _num(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed) or math.isinf(parsed):
        return None
    return parsed


def _baseline_values(candidate: dict[str, Any], explicit_values: list[Any] | None = None) -> list[float]:
    raw = explicit_values
    if raw is None:
        for key in (
            "baseline_values",
            "historical_null_distribution",
            "random_baseline_values",
            "provider_null_distribution",
            "asset_null_distribution",
            "regime_null_distribution",
        ):
            value = candidate.get(key)
            if isinstance(value, list):
                raw = value
                break
    values = [_num(value) for value in (raw or [])]
    return [value for value in values if value is not None]


def _observed_signal(candidate: dict[str, Any], observed_signal: Any = None) -> float | None:
    if observed_signal is not None:
        return _num(observed_signal)
    for key in (
        "observed_signal",
        "estimated_edge",
        "edge_z_score",
        "price_move",
        "odds_move",
        "line_move",
        "volume_spike",
        "relative_volume",
    ):
        value = _num(candidate.get(key))
        if value is not None:
            return value
    return None


def _percentile(observed: float, values: list[float]) -> float:
    if not values:
        return 0.0
    below_or_equal = sum(1 for value in values if value <= observed)
    return round(below_or_equal / len(values), 6)


def compare_to_random_baseline(
    candidate: dict[str, Any] | None = None,
    *,
    baseline_values: list[Any] | None = None,
    observed_signal: Any = None,
    baseline_method: str | None = None,
    minimum_sample_size: int = MIN_BASELINE_SAMPLE_SIZE,
) -> dict[str, Any]:
    row = dict(candidate or {})
    values = _baseline_values(row, explicit_values=baseline_values)
    observed = _observed_signal(row, observed_signal=observed_signal)
    method = str(baseline_method or row.get("baseline_method") or "historical_null_distribution")
    support_status = "ready"
    blocked_reason = None
    if observed is None:
        support_status = "blocked_insufficient_data"
        blocked_reason = "missing_observed_signal"
    elif len(values) < int(minimum_sample_size or MIN_BASELINE_SAMPLE_SIZE):
        support_status = "blocked_insufficient_data"
        blocked_reason = "baseline_sample_too_small"

    if support_status != "ready":
        payload = {
            "baseline_method": method,
            "baseline_sample_size": len(values),
            "observed_signal": observed,
            "baseline_mean": None,
            "baseline_std": None,
            "observed_vs_baseline_z_score": None,
            "observed_vs_baseline_percentile": None,
            "baseline_support_status": support_status,
            "edge_survives_random_baseline": False,
            "random_baseline_warning": "do_not_trust_large_signal_without_random_baseline",
            "edge_quality_score_adjustment": -20.0,
            "blocked_reason": blocked_reason,
        }
        payload.update(locked_safety_flags())
        payload["provider_write"] = False
        payload["execution_allowed"] = False
        payload["live_execution_enabled"] = False
        return payload

    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / max(1, len(values) - 1)
    std = math.sqrt(variance)
    z_score = None if std <= 0 else round((float(observed) - mean) / std, 6)
    pct = _percentile(float(observed), values)
    survives = bool(pct >= 0.95 and (z_score is None or z_score >= 1.64))
    warning = "edge_survives_random_baseline" if survives else "observed_signal_does_not_clear_random_baseline"
    payload = {
        "baseline_method": method,
        "baseline_sample_size": len(values),
        "observed_signal": round(float(observed), 6),
        "baseline_mean": round(mean, 6),
        "baseline_std": round(std, 6),
        "observed_vs_baseline_z_score": z_score,
        "observed_vs_baseline_percentile": pct,
        "baseline_support_status": "ready",
        "edge_survives_random_baseline": survives,
        "random_baseline_warning": warning,
        "edge_quality_score_adjustment": 0.0 if survives else -12.0,
        "blocked_reason": None,
    }
    payload.update(locked_safety_flags())
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
    return payload


def build_surrogate_baseline_summary(
    candidate: dict[str, Any] | None = None,
    *,
    baseline_values: list[Any] | None = None,
) -> dict[str, Any]:
    row = dict(candidate or {})
    method = str(row.get("baseline_method") or "bootstrap_baseline")
    result = compare_to_random_baseline(row, baseline_values=baseline_values, baseline_method=method)
    return {
        "baseline_method": result["baseline_method"],
        "baseline_sample_size": result["baseline_sample_size"],
        "observed_signal": result["observed_signal"],
        "baseline_mean": result["baseline_mean"],
        "baseline_std": result["baseline_std"],
        "observed_vs_baseline_z_score": result["observed_vs_baseline_z_score"],
        "observed_vs_baseline_percentile": result["observed_vs_baseline_percentile"],
        "baseline_support_status": result["baseline_support_status"],
        "edge_survives_random_baseline": result["edge_survives_random_baseline"],
        "random_baseline_warning": result["random_baseline_warning"],
        "surrogate_methods_available": [
            "shuffled_labels",
            "shuffled_time_windows",
            "bootstrap_baseline",
            "historical_null_distribution",
            "provider_specific_null_baseline",
            "asset_specific_null_baseline",
            "regime_specific_null_baseline",
        ],
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
    }

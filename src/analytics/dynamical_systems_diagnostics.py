from __future__ import annotations

import math
from typing import Any

from src.security.policy import locked_safety_flags


def _clean(values: list[Any] | None) -> list[float]:
    out = []
    for item in values or []:
        try:
            value = float(item)
        except (TypeError, ValueError):
            continue
        if math.isfinite(value):
            out.append(value)
    return out


def _corr(left: list[float], right: list[float]) -> float:
    n = min(len(left), len(right))
    if n < 3:
        return 0.0
    a = left[:n]
    b = right[:n]
    ma = sum(a) / n
    mb = sum(b) / n
    num = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    den_a = math.sqrt(sum((x - ma) ** 2 for x in a))
    den_b = math.sqrt(sum((x - mb) ** 2 for x in b))
    if den_a <= 0 or den_b <= 0:
        return 0.0
    return max(-1.0, min(1.0, num / (den_a * den_b)))


def run_sliding_window_topology(sequence: list[Any] | None, *, window_size: int = 5) -> dict[str, Any]:
    values = _clean(sequence)
    if len(values) < max(4, window_size * 2):
        return {
            "ok": True,
            "status": "insufficient_sequence_length",
            "regime_stable": False,
            "regime_unseen": True,
            "sliding_window_topology_status": "insufficient_sequence_length",
            "time_series_shape_shift_score": None,
            "novelty_score": None,
            "data_window_count": 0,
            "insufficient_sequence_length": True,
            "insufficient_sample": True,
            "blocked_reason": "sequence_length_below_two_windows",
            "red_team_only": True,
            **locked_safety_flags(),
        }
    windows = [values[i : i + window_size] for i in range(0, len(values) - window_size + 1)]
    means = [sum(window) / len(window) for window in windows]
    diffs = [abs(means[i] - means[i - 1]) for i in range(1, len(means))]
    scale = max(1e-9, max(values) - min(values))
    shift = (sum(diffs) / max(1, len(diffs))) / scale
    novelty = min(1.0, shift * 3.0)
    return {
        "ok": True,
        "status": "sliding_window_shape_complete",
        "regime_stable": novelty < 0.35,
        "regime_unseen": novelty >= 0.70,
        "sliding_window_topology_status": "deterministic_shape_fallback",
        "time_series_shape_shift_score": round(shift, 6),
        "novelty_score": round(novelty, 6),
        "data_window_count": len(windows),
        "insufficient_sequence_length": False,
        "insufficient_sample": False,
        "blocked_reason": None,
        "red_team_only": True,
        **locked_safety_flags(),
    }


def run_dynamical_systems_diagnostics(sequence: list[Any] | None, *, minimum_sequence_length: int = 12) -> dict[str, Any]:
    values = _clean(sequence)
    if len(values) < int(minimum_sequence_length):
        return {
            "ok": True,
            "status": "blocked_insufficient_data",
            "dynamical_predictability": "data_insufficient",
            "forecast_skill_rho": 0.0,
            "surrogate_skill_rho": 0.0,
            "skill_above_surrogate": False,
            "s_map_status": "insufficient_sequence_length",
            "stochastic_warning": True,
            "edge_quality_score_adjustment": 0.0,
            "insufficient_sample": True,
            "blocked_reason": "sequence_length_below_minimum",
            "red_team_only": True,
            **locked_safety_flags(),
        }
    forecast = abs(_corr(values[:-1], values[1:]))
    surrogate = abs(_corr(list(reversed(values[:-1])), values[1:]))
    above = forecast > surrogate + 0.05
    return {
        "ok": True,
        "status": "dynamical_systems_complete",
        "dynamical_predictability": "deterministic" if forecast >= 0.65 and above else ("mixed" if above else "stochastic"),
        "forecast_skill_rho": round(forecast, 6),
        "surrogate_skill_rho": round(surrogate, 6),
        "skill_above_surrogate": bool(above),
        "s_map_status": "deterministic_surrogate_fallback",
        "stochastic_warning": not bool(above),
        "edge_quality_score_adjustment": round(max(0.0, (forecast - surrogate) * 20.0), 6) if above else 0.0,
        "insufficient_sample": False,
        "blocked_reason": None,
        "red_team_only": True,
        **locked_safety_flags(),
    }

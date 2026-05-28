from __future__ import annotations


def evaluate_walk_forward_gate(
    *,
    rolling_window_performance: float,
    expanding_window_performance: float,
    regime_split_performance: float,
    performance_decay: float,
    sample_size: int,
) -> dict[str, float | bool]:
    sample_component = min(100.0, sample_size / 10.0)
    base = (
        float(rolling_window_performance) * 35.0
        + float(expanding_window_performance) * 30.0
        + float(regime_split_performance) * 25.0
        + sample_component * 0.10
    )
    penalty = max(0.0, float(performance_decay)) * 40.0
    walk_forward_score = round(max(0.0, min(100.0, base - penalty)), 2)
    return {
        "rolling_window_performance": float(rolling_window_performance),
        "expanding_window_performance": float(expanding_window_performance),
        "regime_split_performance": float(regime_split_performance),
        "performance_decay": float(performance_decay),
        "sample_size": int(sample_size),
        "walk_forward_score": walk_forward_score,
        "passes_gate": walk_forward_score >= 70,
        "performance_decay_detected": float(performance_decay) > 0.25,
    }


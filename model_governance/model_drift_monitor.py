from __future__ import annotations

from typing import Any


def evaluate_model_drift(*, baseline_metrics: dict[str, float], current_metrics: dict[str, float], threshold: float = 0.15) -> dict[str, Any]:
    drift_components: dict[str, float] = {}
    for key, baseline in baseline_metrics.items():
        current = float(current_metrics.get(key, baseline))
        denominator = max(abs(float(baseline)), 1e-6)
        drift_components[key] = abs(current - float(baseline)) / denominator
    average_drift = sum(drift_components.values()) / max(len(drift_components), 1)
    drift_score = round(max(0.0, min(100.0, 100.0 - average_drift * 100.0)), 2)
    return {
        "drift_components": drift_components,
        "average_drift": round(average_drift, 6),
        "drift_score": drift_score,
        "drift_detected": average_drift > threshold,
        "passes_gate": drift_score >= 70,
    }


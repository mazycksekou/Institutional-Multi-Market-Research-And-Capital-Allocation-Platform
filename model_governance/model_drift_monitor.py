from __future__ import annotations

from typing import Any


def evaluate_model_drift(*, baseline_metrics: dict[str, float], current_metrics: dict[str, float], threshold: float = 0.15) -> dict[str, Any]:
    required_keys = ["input_distribution_shift", "output_probability_shift", "calibration_decay", "CLV_decay", "ROI_decay", "drawdown_increase", "hit_rate_decay", "market_regime_shift", "provider_data_shift", "sportsbook_market_shift", "stock_regime_shift", "prediction_market_liquidity_shift"]
    keys = list(dict.fromkeys(list(baseline_metrics.keys()) + list(current_metrics.keys())))
    if not keys:
        keys = required_keys
    deltas = {k: abs(float(current_metrics.get(k, 0)) - float(baseline_metrics.get(k, 0))) for k in keys}
    avg = sum(deltas.values()) / max(len(deltas), 1)
    drift = avg > threshold
    action = "require_revalidation" if avg > 0.30 else "watch_recheck" if drift else "no_action"
    return {"drift_detected": drift, "drift_score": round(max(0, 100 - avg * 100), 2), "affected_models": current_metrics.get("affected_models", []), "recommended_action": action, **deltas}

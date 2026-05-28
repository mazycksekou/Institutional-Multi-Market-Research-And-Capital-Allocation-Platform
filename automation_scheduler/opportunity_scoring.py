from __future__ import annotations

from typing import Any

_WEIGHTS = {
    "edge_score": 0.14,
    "confidence_score": 0.10,
    "liquidity_score": 0.08,
    "movement_score": 0.07,
    "data_quality_score": 0.10,
    "market_depth_score": 0.06,
    "timing_score": 0.08,
    "model_fit_score": 0.10,
    "risk_score": 0.08,
    "volatility_score": 0.04,
    "source_consensus_score": 0.05,
    "execution_feasibility_score": 0.05,
    "expected_roi_score": 0.05,
}


def calculate_opportunity_score(field_scores: dict[str, Any]) -> float:
    weighted_sum = 0.0
    for key, weight in _WEIGHTS.items():
        value = float(field_scores.get(key, 0))
        weighted_sum += max(0.0, min(10.0, value)) * weight
    return round(weighted_sum * 10, 2)


def classify_opportunity(score: float, thresholds: dict[str, Any]) -> str:
    if score >= float(thresholds["urgent_threshold"]):
        return "urgent_review"
    if score >= float(thresholds["review_threshold"]):
        return "review_required"
    if score >= float(thresholds["watch_threshold"]):
        return "watch_recheck"
    return "no_action"

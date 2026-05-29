from __future__ import annotations

from typing import Any

_WEIGHTS = {
    "edge_score": 0.06,
    "ev_score": 0.12,
    "line_value_score": 0.10,
    "arbitrage_score": 0.10,
    "middle_score": 0.10,
    "middle_width_score": 0.10,
    "confidence_score": 0.06,
    "model_confidence_score": 0.08,
    "match_confidence_score": 0.09,
    "market_identity_score": 0.08,
    "liquidity_score": 0.08,
    "movement_score": 0.04,
    "data_quality_score": 0.05,
    "market_depth_score": 0.03,
    "timing_score": 0.03,
    "model_fit_score": 0.04,
    "risk_score": 0.04,
    "volatility_score": 0.02,
    "source_consensus_score": 0.01,
    "execution_feasibility_score": 0.01,
    "expected_roi_score": 0.01,
    "stale_data_risk_score": 0.01,
    "settlement_risk_score": 0.01,
    "max_loss_score": 0.03,
    "provider_data_quality_score": 0.03,
    "book_disagreement_score": 0.03,
    "stale_data_risk_score": 0.03,
    "liquidity_placeholder_score": 0.03,
    "cross_book_score": 0.04,
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


def governance_adjusted_score(raw_score: float, governance_blocked: bool) -> float:
    if governance_blocked:
        return 0.0
    return max(0.0, min(100.0, float(raw_score)))

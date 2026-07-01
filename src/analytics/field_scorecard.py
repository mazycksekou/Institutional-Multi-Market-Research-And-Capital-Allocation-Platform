from __future__ import annotations

from typing import Any

from src.services.scheduler_config import clamp

_SCORE_KEYS = (
    "edge_score",
    "ev_score",
    "line_value_score",
    "arbitrage_score",
    "middle_width_score",
    "confidence_score",
    "model_confidence_score",
    "match_confidence_score",
    "market_identity_score",
    "liquidity_score",
    "movement_score",
    "data_quality_score",
    "market_depth_score",
    "timing_score",
    "model_fit_score",
    "risk_score",
    "volatility_score",
    "source_consensus_score",
    "execution_feasibility_score",
    "expected_roi_score",
    "stale_data_risk_score",
    "settlement_risk_score",
    "max_loss_score",
)


def _numeric(candidate: dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        value = candidate.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return float(default)


def build_field_scorecard(candidate: dict[str, Any], *, roi_target_percent: float = 10) -> dict[str, float]:
    provided_scores = candidate.get("field_scores")
    if isinstance(provided_scores, dict):
        return {key: round(clamp(provided_scores.get(key, 0), 0, 10), 2) for key in _SCORE_KEYS}

    edge_percent = _numeric(candidate, "edge_percent", "expected_edge_percent", default=0.0)
    confidence = _numeric(candidate, "confidence", default=0.5)
    ev_percent = _numeric(candidate, "ev_percent", default=edge_percent)
    line_value = max(
        abs(_numeric(candidate, "line_spread", default=0.0)),
        abs(_numeric(candidate, "odds_spread", default=0.0)) / 20.0,
    )
    arbitrage_value = max(0.0, (1.0 - _numeric(candidate, "arbitrage_implied_sum", default=1.0)) * 100.0)
    middle_width = _numeric(candidate, "middle_width", default=0.0)
    match_confidence = _numeric(candidate, "line_match_confidence", default=100.0)
    market_identity = _numeric(candidate, "market_identity_confidence", default=match_confidence)
    liquidity = _numeric(candidate, "liquidity", "liquidity_score_hint", default=0.5)
    movement = abs(_numeric(candidate, "movement_strength", "movement_percent", default=0.0))
    data_quality = _numeric(candidate, "data_quality", default=0.7)
    market_depth = _numeric(candidate, "market_depth", default=0.5)
    timing = _numeric(candidate, "timing_signal", default=0.5)
    model_fit = _numeric(candidate, "model_fit", default=0.5)
    risk = _numeric(candidate, "risk_level_numeric", default=0.5)
    volatility = abs(_numeric(candidate, "volatility_percent", default=0.0))
    source_consensus = _numeric(candidate, "source_consensus", default=0.5)
    execution = _numeric(candidate, "execution_feasibility", default=0.5)
    execution_score = _numeric(candidate, "execution_feasibility_score", default=execution * 10)
    expected_roi = _numeric(candidate, "expected_roi_percent", default=0.0)
    stale_risk = _numeric(candidate, "stale_data_risk", default=0.0)
    settlement_risk = _numeric(candidate, "settlement_risk", default=0.0)
    max_loss = _numeric(candidate, "max_loss", default=0.0)

    scorecard = {
        "edge_score": clamp(edge_percent / 2, 0, 10),
        "ev_score": clamp(ev_percent / 1.5, 0, 10),
        "line_value_score": clamp(line_value * 2.5, 0, 10),
        "arbitrage_score": clamp(arbitrage_value * 2.5, 0, 10),
        "middle_width_score": clamp(middle_width * 2.0, 0, 10),
        "confidence_score": clamp(confidence * 10, 0, 10),
        "model_confidence_score": clamp(confidence * 10, 0, 10),
        "match_confidence_score": clamp(match_confidence / 10, 0, 10),
        "market_identity_score": clamp(market_identity / 10, 0, 10),
        "liquidity_score": clamp(liquidity * 10, 0, 10),
        "movement_score": clamp(movement / 3, 0, 10),
        "data_quality_score": clamp(data_quality * 10, 0, 10),
        "market_depth_score": clamp(market_depth * 10, 0, 10),
        "timing_score": clamp(timing * 10, 0, 10),
        "model_fit_score": clamp(model_fit * 10, 0, 10),
        "risk_score": clamp((1 - risk) * 10, 0, 10),
        "volatility_score": clamp(10 - (volatility / 5), 0, 10),
        "source_consensus_score": clamp(source_consensus * 10, 0, 10),
        "execution_feasibility_score": clamp(max(execution * 10, execution_score), 0, 10),
        "expected_roi_score": clamp((expected_roi / max(1.0, roi_target_percent)) * 10, 0, 10),
        "stale_data_risk_score": clamp((1 - stale_risk) * 10, 0, 10),
        "settlement_risk_score": clamp((1 - settlement_risk) * 10, 0, 10),
        "max_loss_score": clamp(10 - (max_loss / 10), 0, 10),
    }
    return {key: round(value, 2) for key, value in scorecard.items()}

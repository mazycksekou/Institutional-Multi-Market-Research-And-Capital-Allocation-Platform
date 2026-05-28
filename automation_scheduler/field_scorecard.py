from __future__ import annotations

from typing import Any

from .scheduler_config import clamp

_SCORE_KEYS = (
    "edge_score",
    "confidence_score",
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
    expected_roi = _numeric(candidate, "expected_roi_percent", default=0.0)

    scorecard = {
        "edge_score": clamp(edge_percent / 2, 0, 10),
        "confidence_score": clamp(confidence * 10, 0, 10),
        "liquidity_score": clamp(liquidity * 10, 0, 10),
        "movement_score": clamp(movement / 3, 0, 10),
        "data_quality_score": clamp(data_quality * 10, 0, 10),
        "market_depth_score": clamp(market_depth * 10, 0, 10),
        "timing_score": clamp(timing * 10, 0, 10),
        "model_fit_score": clamp(model_fit * 10, 0, 10),
        "risk_score": clamp((1 - risk) * 10, 0, 10),
        "volatility_score": clamp(10 - (volatility / 5), 0, 10),
        "source_consensus_score": clamp(source_consensus * 10, 0, 10),
        "execution_feasibility_score": clamp(execution * 10, 0, 10),
        "expected_roi_score": clamp((expected_roi / max(1.0, roi_target_percent)) * 10, 0, 10),
    }
    return {key: round(value, 2) for key, value in scorecard.items()}

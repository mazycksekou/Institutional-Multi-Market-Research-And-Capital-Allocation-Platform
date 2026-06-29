from __future__ import annotations

from typing import Any


THRESHOLDS = {
    "minimum_model_confidence_for_full_kelly": 85,
    "minimum_data_quality_for_full_kelly": 85,
    "minimum_liquidity_score_for_full_kelly": 8,
    "minimum_market_identity_confidence": 90,
    "maximum_stale_data_seconds": 30,
    "minimum_clv_sample_size_for_full_kelly": 100,
    "minimum_positive_clv_rate_for_full_kelly": 55,
}


def evaluate_stake_confidence(inputs: dict[str, Any]) -> dict[str, Any]:
    model_conf = float(inputs.get("model_confidence", 0))
    data_quality = float(inputs.get("data_quality_score", 0))
    market_identity = float(inputs.get("market_identity_confidence", 0))
    liquidity = float(inputs.get("liquidity_score", 0))
    stale_seconds = float(inputs.get("stale_data_risk", 0))
    settlement_risk = float(inputs.get("settlement_risk", 0))
    calibration = float(inputs.get("calibration_score", 0))
    clv_sample = float(inputs.get("CLV_sample_size", 0))
    clv_positive = float(inputs.get("positive_CLV_rate", 0))

    full_pass = (
        model_conf >= THRESHOLDS["minimum_model_confidence_for_full_kelly"]
        and data_quality >= THRESHOLDS["minimum_data_quality_for_full_kelly"]
        and liquidity >= THRESHOLDS["minimum_liquidity_score_for_full_kelly"]
        and market_identity >= THRESHOLDS["minimum_market_identity_confidence"]
        and stale_seconds <= THRESHOLDS["maximum_stale_data_seconds"]
        and settlement_risk <= 30
        and calibration >= 80
        and clv_sample >= THRESHOLDS["minimum_clv_sample_size_for_full_kelly"]
        and clv_positive >= THRESHOLDS["minimum_positive_clv_rate_for_full_kelly"]
    )
    hard_block = stale_seconds > 120 or liquidity < 4 or market_identity < 75 or settlement_risk > 70
    base_score = (
        (model_conf * 0.2)
        + (data_quality * 0.2)
        + (market_identity * 0.15)
        + ((liquidity * 10) * 0.15)
        + (max(0.0, 100.0 - stale_seconds) * 0.05)
        + (max(0.0, 100.0 - settlement_risk) * 0.1)
        + (calibration * 0.1)
        + (min(100.0, clv_sample) * 0.025)
        + (clv_positive * 0.025)
    )
    if hard_block:
        tier = "low"
    elif full_pass:
        tier = "high"
    elif base_score >= 70:
        tier = "medium"
    else:
        tier = "low"
    return {
        "stake_confidence_score": round(max(0.0, min(100.0, base_score)), 2),
        "confidence_tier": tier,
        "full_kelly_pass": full_pass,
        "hard_block": hard_block,
    }

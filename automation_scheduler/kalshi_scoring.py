from __future__ import annotations

from typing import Any


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _spread_from_record(record: dict[str, Any]) -> float | None:
    yes_bid = _to_float(record.get("yes_bid"))
    yes_ask = _to_float(record.get("yes_ask"))
    if yes_bid is not None and yes_ask is not None:
        return max(0.0, yes_ask - yes_bid)
    no_bid = _to_float(record.get("no_bid"))
    no_ask = _to_float(record.get("no_ask"))
    if no_bid is not None and no_ask is not None:
        return max(0.0, no_ask - no_bid)
    return None


def score_kalshi_candidate(record: dict[str, Any]) -> dict[str, Any]:
    implied_probability = _to_float(record.get("implied_probability"))
    estimated_fair_probability = _to_float(record.get("estimated_fair_probability"))
    probability_edge = None
    if implied_probability is not None and estimated_fair_probability is not None:
        probability_edge = round(estimated_fair_probability - implied_probability, 6)

    spread = _spread_from_record(record)
    liquidity_score = _to_float(record.get("liquidity_score"))
    if liquidity_score is None:
        liquidity_score = 0.0 if spread is None else _clamp(1.0 - spread, 0.0, 1.0)
    volume = _to_float(record.get("volume")) or 0.0
    open_interest = _to_float(record.get("open_interest")) or 0.0
    volume_score = _clamp(volume / 5000.0, 0.0, 1.0)
    open_interest_score = _clamp(open_interest / 5000.0, 0.0, 1.0)

    settlement_rule = bool(record.get("settlement_rule"))
    settlement_rule_risk = 0.0 if settlement_rule else 1.0
    status = str(record.get("status") or "").lower()
    status_risk = 0.0 if status in {"open", "active"} else 0.6
    close_time_risk = 0.6 if bool(record.get("close_time_approaching")) else 0.2
    stale_data_risk = 1.0 if bool(record.get("stale_market")) else 0.1

    pricing_quality = str(record.get("pricing_quality") or "missing")
    pricing_quality_score = {"complete": 1.0, "partial": 0.6, "missing": 0.0}.get(pricing_quality, 0.0)

    confidence_score = _clamp(
        (liquidity_score * 0.35) + (volume_score * 0.2) + (open_interest_score * 0.2) + (pricing_quality_score * 0.25),
        0.0,
        1.0,
    )
    risk_score = _clamp(
        (settlement_rule_risk * 0.2) + (status_risk * 0.2) + (close_time_risk * 0.2) + (stale_data_risk * 0.25) + ((1.0 - pricing_quality_score) * 0.15),
        0.0,
        1.0,
    )
    review_priority_score = _clamp((confidence_score * 0.6) + ((1.0 - risk_score) * 0.4), 0.0, 1.0)

    if pricing_quality == "missing":
        classification = "data_insufficient"
    elif risk_score >= 0.75:
        classification = "watch"
    else:
        classification = "review_only"

    return {
        "implied_probability": implied_probability,
        "estimated_fair_probability": estimated_fair_probability,
        "probability_edge": probability_edge,
        "bid_ask_spread": spread,
        "liquidity_score": round(liquidity_score, 6),
        "volume_score": round(volume_score, 6),
        "open_interest_score": round(open_interest_score, 6),
        "settlement_rule_risk": round(settlement_rule_risk, 6),
        "status_risk": round(status_risk, 6),
        "close_time_risk": round(close_time_risk, 6),
        "stale_data_risk": round(stale_data_risk, 6),
        "pricing_quality_score": round(pricing_quality_score, 6),
        "review_priority_score": round(review_priority_score, 6),
        "confidence_score": round(confidence_score, 6),
        "risk_score": round(risk_score, 6),
        "classification": classification,
    }

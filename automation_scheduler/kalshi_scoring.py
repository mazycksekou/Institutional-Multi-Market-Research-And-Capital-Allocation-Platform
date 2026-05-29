from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

KALSHI_LIQUIDITY_POLICY_VERSION = "kalshi_liquidity_policy_v2"
KALSHI_LIQUIDITY_THRESHOLDS = {
    "very_low": 20.0,
    "low": 45.0,
    "moderate": 70.0,
}
KALSHI_ACTIVITY_SCALE = 1000.0


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _score_0_to_100(value: Any) -> float | None:
    parsed = _to_float(value)
    if parsed is None:
        return None
    if 0.0 <= parsed <= 1.0:
        return round(parsed * 100.0, 6)
    return round(_clamp(parsed, 0.0, 100.0), 6)


def _activity_score(value: Any) -> float | None:
    parsed = _to_float(value)
    if parsed is None:
        return None
    return round(_clamp(parsed / KALSHI_ACTIVITY_SCALE, 0.0, 1.0) * 100.0, 6)


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


def _spread_score_from_spread(spread: float | None) -> float:
    if spread is None:
        return 0.0
    return round(_clamp(1.0 - spread, 0.0, 1.0) * 100.0, 6)


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _close_time_score(record: dict[str, Any]) -> float:
    if bool(record.get("close_time_approaching")):
        return 35.0
    close_time = _parse_datetime(record.get("close_time") or record.get("market_close_at"))
    if close_time is None:
        return 70.0
    hours_until_close = (close_time - datetime.now(timezone.utc)).total_seconds() / 3600.0
    if hours_until_close <= 0:
        return 0.0
    if hours_until_close <= 6:
        return 35.0
    if hours_until_close <= 24:
        return 60.0
    return 85.0


def evaluate_kalshi_liquidity_policy(record: dict[str, Any]) -> dict[str, Any]:
    direct_score = _score_0_to_100(record.get("liquidity_score"))
    volume_score = _activity_score(record.get("volume"))
    open_interest_score = _activity_score(record.get("open_interest"))
    has_volume = volume_score is not None
    has_open_interest = open_interest_score is not None

    if has_volume and has_open_interest:
        liquidity_source = "volume_open_interest_proxy"
        activity_score = ((volume_score or 0.0) + (open_interest_score or 0.0)) / 2.0
        liquidity_score = (activity_score * 0.7) + ((direct_score or activity_score) * 0.3)
    elif has_volume:
        liquidity_source = "volume_only_proxy"
        liquidity_score = ((volume_score or 0.0) * 0.75) + ((direct_score or volume_score or 0.0) * 0.25)
    elif has_open_interest:
        liquidity_source = "open_interest_only_proxy"
        liquidity_score = ((open_interest_score or 0.0) * 0.75) + ((direct_score or open_interest_score or 0.0) * 0.25)
    elif direct_score is not None:
        liquidity_source = "direct_liquidity"
        liquidity_score = direct_score
    else:
        liquidity_source = "missing"
        liquidity_score = 0.0

    liquidity_score = round(_clamp(liquidity_score, 0.0, 100.0), 6)
    if liquidity_source == "missing":
        tier = "missing_liquidity"
        reason = "missing_liquidity"
    elif liquidity_score < KALSHI_LIQUIDITY_THRESHOLDS["very_low"]:
        tier = "very_low_liquidity"
        reason = "below_very_low_threshold"
    elif liquidity_score < KALSHI_LIQUIDITY_THRESHOLDS["low"]:
        tier = "low_liquidity"
        reason = "below_low_threshold"
    elif liquidity_score < KALSHI_LIQUIDITY_THRESHOLDS["moderate"]:
        tier = "moderate_liquidity"
        reason = "derived_from_volume_open_interest" if "proxy" in liquidity_source else "moderate"
    else:
        tier = "adequate_liquidity"
        reason = "derived_from_volume_open_interest" if "proxy" in liquidity_source else "direct_liquidity_available"

    return {
        "liquidity_policy_version": KALSHI_LIQUIDITY_POLICY_VERSION,
        "liquidity_source": liquidity_source,
        "liquidity_score": liquidity_score,
        "liquidity_tier": tier,
        "liquidity_reason": reason,
        "low_liquidity_flag": tier in {"very_low_liquidity", "low_liquidity"},
        "missing_liquidity_flag": tier == "missing_liquidity",
        "liquidity_threshold_used": dict(KALSHI_LIQUIDITY_THRESHOLDS),
        "volume_score": 0.0 if volume_score is None else round(volume_score, 6),
        "open_interest_score": 0.0 if open_interest_score is None else round(open_interest_score, 6),
    }


def score_kalshi_candidate(record: dict[str, Any]) -> dict[str, Any]:
    implied_probability = _to_float(record.get("implied_probability"))
    estimated_fair_probability = _to_float(record.get("estimated_fair_probability"))
    probability_edge = None
    if implied_probability is not None and estimated_fair_probability is not None:
        probability_edge = round(estimated_fair_probability - implied_probability, 6)

    spread = _spread_from_record(record)
    spread_score = _spread_score_from_spread(spread)
    liquidity_policy = evaluate_kalshi_liquidity_policy(record)
    liquidity_score = float(liquidity_policy["liquidity_score"])
    volume_score = float(liquidity_policy["volume_score"])
    open_interest_score = float(liquidity_policy["open_interest_score"])

    settlement_rule = bool(record.get("settlement_rule"))
    settlement_rule_risk = 0.0 if settlement_rule else 100.0
    status = str(record.get("status") or "").lower()
    status_risk = 0.0 if status in {"open", "active"} else 60.0
    close_time_score = _close_time_score(record)
    close_time_risk = 100.0 - close_time_score
    stale_data_risk = 100.0 if bool(record.get("stale_market")) else 10.0

    pricing_quality = str(record.get("pricing_quality") or "missing")
    pricing_quality_score = {"complete": 100.0, "partial": 60.0, "missing": 0.0}.get(pricing_quality, 0.0)
    market_structure_score = round((spread_score * 0.7) + (close_time_score * 0.3), 6)

    confidence_score = _clamp(
        (liquidity_score * 0.35) + (spread_score * 0.15) + (volume_score * 0.1) + (open_interest_score * 0.1) + (pricing_quality_score * 0.3),
        0.0,
        100.0,
    )
    risk_score = _clamp(
        (settlement_rule_risk * 0.15) + (status_risk * 0.2) + (close_time_risk * 0.15) + (stale_data_risk * 0.2) + ((100.0 - pricing_quality_score) * 0.15) + ((100.0 - liquidity_score) * 0.15),
        0.0,
        100.0,
    )
    review_priority_score = _clamp((confidence_score * 0.55) + ((100.0 - risk_score) * 0.35) + (market_structure_score * 0.1), 0.0, 100.0)

    if pricing_quality == "missing":
        classification = "data_insufficient"
    elif risk_score >= 75.0:
        classification = "watch"
    else:
        classification = "review_only"

    return {
        **liquidity_policy,
        "implied_probability": implied_probability,
        "estimated_fair_probability": estimated_fair_probability,
        "probability_edge": probability_edge,
        "bid_ask_spread": spread,
        "spread_score": round(spread_score, 6),
        "liquidity_score": round(liquidity_score, 6),
        "volume_score": round(volume_score, 6),
        "open_interest_score": round(open_interest_score, 6),
        "settlement_rule_risk": round(settlement_rule_risk, 6),
        "status_risk": round(status_risk, 6),
        "close_time_risk": round(close_time_risk, 6),
        "close_time_score": round(close_time_score, 6),
        "stale_data_risk": round(stale_data_risk, 6),
        "pricing_quality_score": round(pricing_quality_score, 6),
        "market_structure_score": round(market_structure_score, 6),
        "review_priority_score": round(review_priority_score, 6),
        "confidence_score": round(confidence_score, 6),
        "risk_score": round(risk_score, 6),
        "classification": classification,
    }

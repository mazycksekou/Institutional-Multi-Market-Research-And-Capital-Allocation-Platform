from __future__ import annotations

from typing import Any

from .hockey_impact_common import clamp, compact_list, finalize_hockey_response, normalize_hockey_market, normalize_hockey_sport


def _count_records(value: Any) -> int:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        return len(value)
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _hit_rate(outcomes: Any) -> float | None:
    if not isinstance(outcomes, list) or not outcomes:
        return None
    values = []
    for row in outcomes:
        if not isinstance(row, dict):
            continue
        result = row.get("hit")
        if result is None:
            result = row.get("won")
        if result is None:
            result = row.get("outcome")
        if isinstance(result, bool):
            values.append(1.0 if result else 0.0)
        elif isinstance(result, (int, float)):
            values.append(1.0 if float(result) > 0 else 0.0)
        elif str(result).lower() in {"win", "won", "hit", "true"}:
            values.append(1.0)
        elif str(result).lower() in {"loss", "lost", "miss", "false"}:
            values.append(0.0)
    if not values:
        return None
    return sum(values) / len(values)


def evaluate_hockey_impact_calibration(
    row: dict[str, Any] | None = None,
    *,
    sport: str = "icehockey_nhl",
    market_type: str = "moneyline",
    role: str = "UNKNOWN",
    data_tier: int = 0,
) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    normalized_sport = normalize_hockey_sport(sport)
    market = normalize_hockey_market(market_type)
    historical = _count_records(source.get("historical_predictions"))
    outcomes = source.get("settled_outcomes")
    matched = _count_records(source.get("matched_outcomes_count"))
    if matched <= 0:
        matched = _count_records(outcomes)
    sample_size = max(historical, matched, _count_records(source.get("sample_size")))
    insufficient_sample = sample_size < 80
    if matched <= 0:
        status = "insufficient_data"
    elif sample_size >= 250 and matched >= 100:
        status = "calibration_ready"
    else:
        status = "partial_calibration"
    confidence_cap = 42.0 if status == "insufficient_data" else 62.0 if status == "partial_calibration" else 82.0
    next_required = []
    if matched <= 0:
        next_required.append("settled_hockey_outcomes_by_market_role_context")
    if sample_size < 80:
        next_required.append("larger_hockey_context_bucket_sample")
    if not source.get("closing_prices"):
        next_required.append("closing_prices_for_clv")
    if not source.get("realized_returns"):
        next_required.append("realized_returns_for_roi")
    buckets = {
        "sport": normalized_sport,
        "market_type": market,
        "role": role,
        "data_tier": data_tier,
        "goalie_status_bucket": source.get("goalie_context_bucket") or source.get("goalie_status_bucket") or "unknown_goalie_status",
        "rest_bucket": source.get("rest_travel_bucket") or source.get("rest_bucket") or "unknown_rest",
        "back_to_back_bucket": source.get("back_to_back_bucket") or "unknown_back_to_back",
        "first_period_bucket": source.get("first_period_bucket") or ("first_period" if market.startswith("first_period") else "full_game"),
        "special_teams_bucket": source.get("special_teams_bucket") or "unknown_special_teams",
        "line_stability_bucket": source.get("line_context_bucket") or source.get("line_stability_bucket") or "unknown_line_stability",
        "injury_bucket": source.get("injury_bucket") or "unknown_injury",
        "liquidity_bucket": source.get("liquidity_bucket") or "unknown_liquidity",
    }
    payload: dict[str, Any] = {
        "calibration_status": status,
        "sample_size": sample_size,
        "matched_outcomes_count": matched,
        "insufficient_sample": insufficient_sample,
        "confidence_cap": round(clamp(confidence_cap), 2),
        "next_required_data": compact_list(next_required, limit=20),
        "calibration_buckets": buckets,
        "fabricated_calibration": False,
    }
    rate = _hit_rate(outcomes)
    if rate is not None:
        payload["hit_rate"] = round(rate, 4)
        payload["false_positive_rate"] = round(1.0 - rate, 4)
    if source.get("realized_returns") not in (None, "", []):
        returns = source.get("realized_returns")
        if isinstance(returns, list) and returns:
            payload["roi_proxy"] = round(sum(float(value or 0) for value in returns) / len(returns), 4)
    if source.get("closing_prices") not in (None, "", []) and source.get("entry_prices") not in (None, "", []):
        payload["clv_proxy"] = "available_from_real_open_close_prices"
    if source.get("fills") not in (None, "", []) or source.get("entry_prices") not in (None, "", []):
        payload["slippage_proxy"] = "available_only_if_real_entry_or_fill_data_supplied"
    return finalize_hockey_response(payload, source_payload=source)

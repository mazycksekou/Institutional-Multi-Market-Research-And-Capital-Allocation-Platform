from __future__ import annotations

from typing import Any

from .soccer_impact_common import clamp, compact_list, finalize_soccer_response, normalize_soccer_market, normalize_soccer_sport


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
            result = row.get("won", row.get("outcome"))
        if isinstance(result, bool):
            values.append(1.0 if result else 0.0)
        elif isinstance(result, (int, float)):
            values.append(1.0 if float(result) > 0 else 0.0)
        elif str(result).lower() in {"win", "won", "hit", "true"}:
            values.append(1.0)
        elif str(result).lower() in {"loss", "lost", "miss", "false"}:
            values.append(0.0)
    return sum(values) / len(values) if values else None


def evaluate_soccer_impact_calibration(
    row: dict[str, Any] | None = None,
    *,
    sport: str = "soccer",
    market_type: str = "three_way_moneyline",
    role: str = "UNKNOWN",
    data_tier: int = 0,
) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    market = normalize_soccer_market(market_type)
    historical = _count_records(source.get("historical_predictions"))
    outcomes = source.get("settled_outcomes")
    matched = _count_records(source.get("matched_outcomes_count")) or _count_records(outcomes)
    sample_size = max(historical, matched, _count_records(source.get("sample_size")))
    required = 250 if market == "correct_score" else 80
    ready_required = 800 if market == "correct_score" else 250
    if matched <= 0:
        status = "insufficient_data"
    elif sample_size >= ready_required and matched >= required:
        status = "calibration_ready"
    else:
        status = "partial_calibration"
    insufficient_sample = sample_size < required
    confidence_cap = 32.0 if market == "correct_score" and status != "calibration_ready" else 42.0 if status == "insufficient_data" else 62.0 if status == "partial_calibration" else 82.0
    next_required = []
    if matched <= 0:
        next_required.append("settled_soccer_outcomes_by_market_tactical_context")
    if sample_size < required:
        next_required.append("larger_soccer_context_bucket_sample")
    if market == "correct_score" and status != "calibration_ready":
        next_required.append("correct_score_extra_large_calibration_sample")
    if not source.get("closing_prices"):
        next_required.append("closing_prices_for_clv")
    if not source.get("realized_returns"):
        next_required.append("realized_returns_for_roi")
    buckets = {
        "sport": normalize_soccer_sport(sport),
        "market_type": market,
        "role": role,
        "data_tier": data_tier,
        "lineup_status_bucket": source.get("lineup_context_bucket") or source.get("lineup_status_bucket") or "unknown_lineup",
        "goalkeeper_status_bucket": source.get("goalkeeper_bucket") or source.get("goalkeeper_status_bucket") or "unknown_goalkeeper",
        "tactical_bucket": source.get("tactical_context_bucket") or source.get("tactical_bucket") or "unknown_tactical",
        "possession_value_bucket": source.get("possession_value_bucket") or "unknown_possession_value",
        "pressing_bucket": source.get("pressing_bucket") or "unknown_pressing",
        "transition_bucket": source.get("transition_bucket") or "unknown_transition",
        "set_piece_bucket": source.get("set_piece_bucket") or "unknown_set_piece",
        "referee_bucket": source.get("referee_context_bucket") or source.get("referee_bucket") or "unknown_referee",
        "rest_travel_bucket": source.get("rest_travel_bucket") or "unknown_rest_travel",
        "first_half_bucket": source.get("first_half_bucket") or ("first_half" if market.startswith("first_half") else "full_game"),
        "liquidity_bucket": source.get("liquidity_bucket") or "unknown_liquidity",
    }
    payload: dict[str, Any] = {
        "calibration_status": status,
        "sample_size": sample_size,
        "matched_outcomes_count": matched,
        "insufficient_sample": insufficient_sample,
        "confidence_cap": round(clamp(confidence_cap), 2),
        "next_required_data": compact_list(next_required, limit=25),
        "calibration_buckets": buckets,
        "correct_score_extra_conservative": market == "correct_score",
        "fabricated_calibration": False,
    }
    rate = _hit_rate(outcomes)
    if rate is not None:
        payload["hit_rate"] = round(rate, 4)
        payload["false_positive_rate"] = round(1.0 - rate, 4)
    returns = source.get("realized_returns")
    if isinstance(returns, list) and returns:
        payload["roi_proxy"] = round(sum(float(value or 0) for value in returns) / len(returns), 4)
    if source.get("closing_prices") not in (None, "", []) and source.get("entry_prices") not in (None, "", []):
        payload["clv_proxy"] = "available_from_real_open_close_prices"
    if source.get("fills") not in (None, "", []) or source.get("entry_prices") not in (None, "", []):
        payload["slippage_proxy"] = "available_only_if_real_entry_or_fill_data_supplied"
    return finalize_soccer_response(payload, source_payload=source)

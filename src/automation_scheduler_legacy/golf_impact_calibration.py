from __future__ import annotations

from typing import Any

from .golf_impact_common import compact_list, finalize_golf_response, normalize_golf_market, normalize_golf_skill_group, normalize_golf_sport, safe_float


def _records(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _numbers(value: Any) -> list[float]:
    if not isinstance(value, list):
        return []
    out: list[float] = []
    for item in value:
        number = safe_float(item)
        if number is not None:
            out.append(number)
    return out


def evaluate_golf_impact_calibration(
    row: dict[str, Any] | None = None,
    *,
    sport: str = "golf",
    market_type: str = "top_20",
    skill_group: str = "UNKNOWN",
    data_tier: int = 0,
) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    market = normalize_golf_market(market_type)
    predictions = _records(source.get("historical_predictions"))
    outcomes = _records(source.get("settled_outcomes"))
    explicit = int(safe_float(source.get("matched_outcomes_count"), 0.0) or 0)
    matched = max(explicit, len(outcomes))
    if predictions and outcomes:
        outcome_ids = {str(item.get("prediction_id") or item.get("candidate_id") or item.get("id")) for item in outcomes}
        matched = max(matched, sum(1 for item in predictions if str(item.get("prediction_id") or item.get("candidate_id") or item.get("id")) in outcome_ids))
    sample = max(int(safe_float(source.get("sample_size"), 0.0) or 0), len(predictions), matched)
    if market == "outright_winner":
        min_partial, min_ready = 60, 220
    elif market in {"top_5", "top_10", "top_20", "top_30", "top_40"}:
        min_partial, min_ready = 40, 140
    else:
        min_partial, min_ready = 30, 100
    status = "insufficient_data" if matched < min_partial else "partial_calibration" if matched < min_ready else "calibration_ready"
    hits = 0
    false_pos = 0
    if predictions and outcomes:
        by_id = {str(item.get("prediction_id") or item.get("candidate_id") or item.get("id")): item for item in outcomes}
        for pred in predictions:
            out = by_id.get(str(pred.get("prediction_id") or pred.get("candidate_id") or pred.get("id")))
            if not out:
                continue
            predicted = str(pred.get("prediction") or pred.get("recommended_action") or "").lower() in {"over", "yes", "win", "review", "positive", "1", "true", "make_cut", "top"}
            actual = str(out.get("final_outcome") or out.get("outcome") or "").lower() in {"hit", "win", "over", "yes", "positive", "1", "true", "made_cut", "top"}
            hits += int(predicted and actual)
            false_pos += int(predicted and not actual)
    elif outcomes:
        for out in outcomes:
            actual_value = out.get("hit", out.get("final_outcome", out.get("outcome")))
            actual = str(actual_value).lower() in {"hit", "win", "over", "yes", "positive", "1", "true", "made_cut", "top"}
            hits += int(actual)
            false_pos += int(not actual)
    result = {
        "calibration_status": status,
        "sample_size": sample,
        "matched_outcomes_count": matched,
        "insufficient_sample": matched < min_partial,
        "hit_rate": round(hits / matched, 6) if matched and (predictions or outcomes) else None,
        "false_positive_rate": round(false_pos / matched, 6) if matched and (predictions or outcomes) else None,
        "confidence_cap": 30.0 if status == "insufficient_data" else 62.0 if status == "partial_calibration" else 86.0,
        "outright_extra_conservative": market == "outright_winner",
        "placement_market_bucketed_separately": market in {"top_5", "top_10", "top_20", "top_30", "top_40"},
        "next_required_data": compact_list(
            [
                "real_settled_golf_outcomes_by_market_bucket" if matched < min_partial else None,
                "larger_bucketed_validation_sample" if min_partial <= matched < min_ready else None,
                "open_close_prices_for_clv" if not source.get("closing_prices") and not source.get("entry_prices") else None,
                "realized_returns_for_roi" if not source.get("realized_returns") else None,
            ],
            limit=10,
        ),
        "calibration_buckets": {
            "sport": normalize_golf_sport(sport),
            "market_type": market,
            "data_tier": data_tier,
            "skill_group": normalize_golf_skill_group(skill_group),
            "context_bucket": source.get("context_bucket"),
            "course_fit_bucket": source.get("course_fit_bucket"),
            "weather_wave_bucket": source.get("weather_wave_bucket"),
            "field_strength_bucket": source.get("field_strength_bucket"),
            "cut_rule_bucket": source.get("cut_rule_bucket"),
            "tournament_format_bucket": source.get("tournament_format_bucket"),
            "player_volatility_bucket": source.get("player_volatility_bucket") or source.get("volatility_bucket"),
            "injury_bucket": source.get("injury_bucket"),
            "liquidity_bucket": source.get("liquidity_bucket"),
        },
    }
    returns = _numbers(source.get("realized_returns"))
    if returns:
        result["roi_proxy"] = round(sum(returns) / len(returns), 6)
    entries = _numbers(source.get("entry_prices"))
    closes = _numbers(source.get("closing_prices"))
    pairs = [(a, b) for a, b in zip(entries, closes)]
    if pairs:
        result["clv_proxy"] = round(sum(b - a for a, b in pairs) / len(pairs), 6)
    fills = _numbers(source.get("fill_prices"))
    slip_pairs = [(a, b) for a, b in zip(fills, entries)]
    if slip_pairs:
        result["slippage_proxy"] = round(sum(a - b for a, b in slip_pairs) / len(slip_pairs), 6)
    return finalize_golf_response(result, source_payload=source)

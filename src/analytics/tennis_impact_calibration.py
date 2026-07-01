from __future__ import annotations

from typing import Any

from src.market_intelligence.tennis_impact_common import compact_list, finalize_tennis_response, normalize_tennis_market, normalize_tennis_sport, safe_float


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


def evaluate_tennis_impact_calibration(
    row: dict[str, Any] | None = None,
    *,
    sport: str = "tennis",
    market_type: str = "moneyline",
    tour: str | None = None,
    surface: str | None = None,
    format_bucket: str | None = None,
    data_tier: int = 0,
) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    market = normalize_tennis_market(market_type)
    predictions = _records(source.get("historical_predictions"))
    outcomes = _records(source.get("settled_outcomes"))
    explicit = int(safe_float(source.get("matched_outcomes_count"), 0.0) or 0)
    matched = max(explicit, len(outcomes))
    if predictions and outcomes:
        outcome_ids = {str(item.get("prediction_id") or item.get("candidate_id") or item.get("id")) for item in outcomes}
        matched = max(matched, sum(1 for item in predictions if str(item.get("prediction_id") or item.get("candidate_id") or item.get("id")) in outcome_ids))
    sample = max(int(safe_float(source.get("sample_size"), 0.0) or 0), len(predictions), matched)
    if market in {"correct_score", "first_set_correct_score", "player_to_win_2_0", "player_to_win_2_1", "player_to_win_3_0", "player_to_win_3_1", "player_to_win_3_2"}:
        min_partial, min_ready = 80, 260
        extra = "correct_score"
    elif market in {"match_tiebreak_yes_no", "first_set_tiebreak_yes_no"}:
        min_partial, min_ready = 60, 180
        extra = "tiebreak"
    else:
        min_partial, min_ready = 35, 120
        extra = "standard"
    status = "insufficient_data" if matched < min_partial else "partial_calibration" if matched < min_ready else "calibration_ready"
    hits = 0
    false_pos = 0
    if predictions and outcomes:
        by_id = {str(item.get("prediction_id") or item.get("candidate_id") or item.get("id")): item for item in outcomes}
        for pred in predictions:
            out = by_id.get(str(pred.get("prediction_id") or pred.get("candidate_id") or pred.get("id")))
            if not out:
                continue
            predicted = str(pred.get("prediction") or pred.get("recommended_action") or "").lower() in {"over", "yes", "win", "review", "positive", "1", "true"}
            actual = str(out.get("final_outcome") or out.get("outcome") or out.get("hit")).lower() in {"hit", "win", "over", "yes", "positive", "1", "true"}
            hits += int(predicted and actual)
            false_pos += int(predicted and not actual)
    elif outcomes:
        for out in outcomes:
            actual = str(out.get("hit", out.get("final_outcome", out.get("outcome")))).lower() in {"hit", "win", "over", "yes", "positive", "1", "true"}
            hits += int(actual)
            false_pos += int(not actual)
    result: dict[str, Any] = {
        "calibration_status": status,
        "sample_size": sample,
        "matched_outcomes_count": matched,
        "insufficient_sample": matched < min_partial,
        "hit_rate": round(hits / matched, 6) if matched and (predictions or outcomes) else None,
        "false_positive_rate": round(false_pos / matched, 6) if matched and (predictions or outcomes) else None,
        "confidence_cap": 30.0 if status == "insufficient_data" else 62.0 if status == "partial_calibration" else 86.0,
        "correct_score_extra_conservative": extra == "correct_score",
        "tiebreak_extra_conservative": extra == "tiebreak",
        "next_required_data": compact_list(
            [
                "real_settled_tennis_outcomes_by_market_bucket" if matched < min_partial else None,
                "larger_bucketed_validation_sample" if min_partial <= matched < min_ready else None,
                "open_close_prices_for_clv" if not source.get("closing_prices") and not source.get("entry_prices") else None,
                "realized_returns_for_roi" if not source.get("realized_returns") else None,
            ],
            limit=10,
        ),
        "calibration_buckets": {
            "sport": normalize_tennis_sport(sport),
            "tour": source.get("tour") or tour,
            "market_type": market,
            "data_tier": data_tier,
            "surface": source.get("surface") or surface,
            "best_of": source.get("best_of") or format_bucket,
            "serve_strength_bucket": source.get("serve_bucket") or source.get("serve_strength_bucket"),
            "return_strength_bucket": source.get("return_bucket") or source.get("return_strength_bucket"),
            "tiebreak_bucket": source.get("tiebreak_bucket"),
            "fatigue_bucket": source.get("fatigue_bucket"),
            "injury_retirement_bucket": source.get("injury_bucket") or source.get("injury_retirement_bucket"),
            "player_prop_bucket": source.get("player_prop_bucket"),
            "liquidity_bucket": source.get("market_liquidity_bucket") or source.get("liquidity_bucket"),
            "context_bucket": source.get("context_bucket"),
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
    return finalize_tennis_response(result, source_payload=source)

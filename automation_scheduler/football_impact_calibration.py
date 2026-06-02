from __future__ import annotations

from typing import Any

from .football_impact_schema import clamp, compact_list, finalize_football_response, normalize_football_market, normalize_football_sport, normalize_role, safe_float


def _records(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _matched_records(predictions: list[dict[str, Any]], outcomes: list[dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    by_id = {}
    for outcome in outcomes:
        key = outcome.get("prediction_id") or outcome.get("candidate_id") or outcome.get("event_id") or outcome.get("id")
        if key not in (None, ""):
            by_id[str(key)] = outcome
    matched = []
    for prediction in predictions:
        key = prediction.get("prediction_id") or prediction.get("candidate_id") or prediction.get("event_id") or prediction.get("id")
        if key not in (None, "") and str(key) in by_id:
            matched.append((prediction, by_id[str(key)]))
    return matched


def evaluate_football_impact_calibration(
    row: dict[str, Any] | None = None,
    *,
    sport: str = "americanfootball_nfl",
    market_type: str = "spread",
    role: str = "unknown",
    data_tier: int = 0,
) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    normalized_sport = normalize_football_sport(sport)
    market = normalize_football_market(market_type)
    normalized_role = normalize_role(role)
    predictions = _records(source.get("historical_predictions"))
    outcomes = _records(source.get("settled_outcomes"))
    matched_pairs = _matched_records(predictions, outcomes)
    explicit_matched = int(safe_float(source.get("matched_outcomes_count"), 0.0) or 0)
    matched_count = max(explicit_matched, len(matched_pairs))
    sample_size = max(int(safe_float(source.get("sample_size"), 0.0) or 0), len(predictions), matched_count)
    if matched_count <= 0 and not outcomes:
        status = "insufficient_data"
    elif matched_count < 30:
        status = "insufficient_data"
    elif matched_count < 100:
        status = "partial_calibration"
    else:
        status = "calibration_ready"

    hits = 0
    false_positives = 0
    for prediction, outcome in matched_pairs:
        predicted_positive = str(prediction.get("recommended_action") or prediction.get("prediction") or "").strip().lower() in {"review", "watchlist", "over", "yes", "win", "positive", "1", "true"}
        actual_positive = str(outcome.get("final_outcome") or outcome.get("outcome") or "").strip().lower() in {"win", "hit", "yes", "over", "positive", "1", "true"}
        if predicted_positive and actual_positive:
            hits += 1
        if predicted_positive and not actual_positive:
            false_positives += 1
    hit_rate = round(hits / matched_count, 6) if matched_count else None
    false_positive_rate = round(false_positives / matched_count, 6) if matched_count else None
    confidence_cap = 35.0 if status == "insufficient_data" else 68.0 if status == "partial_calibration" else 88.0
    context_bucket = source.get("context_bucket") or f"{normalized_sport}.{market}.{normalized_role}.tier_{data_tier}"
    bucket_payload = {
        "sport": normalized_sport,
        "market_type": market,
        "role": normalized_role,
        "data_tier": data_tier,
        "context_bucket": context_bucket,
        "weather_bucket": source.get("weather_bucket"),
        "injury_bucket": source.get("injury_bucket"),
        "liquidity_bucket": source.get("liquidity_bucket"),
    }
    result = {
        "calibration_status": status,
        "sample_size": sample_size,
        "matched_outcomes_count": matched_count,
        "false_positive_rate": false_positive_rate,
        "hit_rate": hit_rate,
        "confidence_cap": confidence_cap,
        "insufficient_sample": matched_count < 30,
        "next_required_data": compact_list(
            [
                "real_settled_outcomes_by_market_role_context" if matched_count < 30 else None,
                "larger_bucketed_validation_sample" if 30 <= matched_count < 100 else None,
                "open_close_prices_for_clv" if "open_price" not in source and "close_price" not in source else None,
                "real_return_records_for_roi" if "return" not in source and "roi" not in source else None,
            ],
            limit=10,
        ),
        "calibration_buckets": bucket_payload,
    }
    returns = [safe_float(item.get("return")) for item in outcomes if safe_float(item.get("return")) is not None]
    if returns:
        result["roi_proxy"] = round(sum(returns) / len(returns), 6)
    open_close = [
        (safe_float(item.get("open_price")), safe_float(item.get("close_price")))
        for item in outcomes
        if safe_float(item.get("open_price")) is not None and safe_float(item.get("close_price")) is not None
    ]
    if open_close:
        result["clv_proxy"] = round(sum((close or 0.0) - (open_ or 0.0) for open_, close in open_close) / len(open_close), 6)
    fills = [
        (safe_float(item.get("fill_price")), safe_float(item.get("market_price")))
        for item in outcomes
        if safe_float(item.get("fill_price")) is not None and safe_float(item.get("market_price")) is not None
    ]
    if fills:
        result["slippage_proxy"] = round(sum((fill or 0.0) - (market_price or 0.0) for fill, market_price in fills) / len(fills), 6)
    return finalize_football_response(result, source_payload=source)

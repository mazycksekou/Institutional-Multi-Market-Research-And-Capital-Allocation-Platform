from __future__ import annotations

from typing import Any

from src.market_intelligence.baseball_impact_common import compact_list, finalize_baseball_response, normalize_baseball_market, normalize_baseball_role, normalize_baseball_sport, safe_float


def _records(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def evaluate_baseball_impact_calibration(
    row: dict[str, Any] | None = None,
    *,
    sport: str = "baseball_mlb",
    market_type: str = "moneyline",
    role: str = "UNKNOWN",
    data_tier: int = 0,
) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    predictions = _records(source.get("historical_predictions"))
    outcomes = _records(source.get("settled_outcomes"))
    explicit = int(safe_float(source.get("matched_outcomes_count"), 0.0) or 0)
    matched = explicit
    if predictions and outcomes:
        outcome_ids = {str(item.get("prediction_id") or item.get("candidate_id") or item.get("id")) for item in outcomes}
        matched = max(matched, sum(1 for item in predictions if str(item.get("prediction_id") or item.get("candidate_id") or item.get("id")) in outcome_ids))
    sample = max(int(safe_float(source.get("sample_size"), 0.0) or 0), len(predictions), matched)
    status = "insufficient_data" if matched < 30 else "partial_calibration" if matched < 100 else "calibration_ready"
    hits = 0
    false_pos = 0
    if predictions and outcomes:
        by_id = {str(item.get("prediction_id") or item.get("candidate_id") or item.get("id")): item for item in outcomes}
        for pred in predictions:
            out = by_id.get(str(pred.get("prediction_id") or pred.get("candidate_id") or pred.get("id")))
            if not out:
                continue
            predicted = str(pred.get("prediction") or pred.get("recommended_action") or "").lower() in {"over", "yes", "win", "review", "positive", "1", "true"}
            actual = str(out.get("final_outcome") or out.get("outcome") or "").lower() in {"hit", "win", "over", "yes", "positive", "1", "true"}
            hits += int(predicted and actual)
            false_pos += int(predicted and not actual)
    result = {
        "calibration_status": status,
        "sample_size": sample,
        "matched_outcomes_count": matched,
        "insufficient_sample": matched < 30,
        "hit_rate": round(hits / matched, 6) if matched and predictions and outcomes else None,
        "false_positive_rate": round(false_pos / matched, 6) if matched and predictions and outcomes else None,
        "confidence_cap": 35.0 if status == "insufficient_data" else 68.0 if status == "partial_calibration" else 88.0,
        "next_required_data": compact_list(["real_settled_outcomes_by_market_role_context" if matched < 30 else None, "larger_bucketed_validation_sample" if 30 <= matched < 100 else None, "open_close_prices_for_clv" if not source.get("closing_prices") and not source.get("entry_prices") else None, "realized_returns_for_roi" if not source.get("realized_returns") else None], limit=10),
        "calibration_buckets": {
            "sport": normalize_baseball_sport(sport),
            "market_type": normalize_baseball_market(market_type),
            "role": normalize_baseball_role(role),
            "data_tier": data_tier,
            "context_bucket": source.get("context_bucket"),
            "pitcher_context_bucket": source.get("pitcher_context_bucket"),
            "batter_context_bucket": source.get("batter_context_bucket"),
            "handedness_bucket": source.get("handedness_bucket"),
            "pitch_mix_bucket": source.get("pitch_mix_bucket"),
            "park_bucket": source.get("park_bucket"),
            "weather_bucket": source.get("weather_bucket") or source.get("park_weather_bucket"),
            "umpire_bucket": source.get("umpire_bucket"),
            "lineup_bucket": source.get("lineup_bucket"),
            "bullpen_bucket": source.get("bullpen_bucket"),
            "liquidity_bucket": source.get("liquidity_bucket"),
        },
    }
    returns = [safe_float(item) for item in (source.get("realized_returns") or [])] if isinstance(source.get("realized_returns"), list) else []
    returns = [item for item in returns if item is not None]
    if returns:
        result["roi_proxy"] = round(sum(returns) / len(returns), 6)
    entries = [safe_float(item) for item in (source.get("entry_prices") or [])] if isinstance(source.get("entry_prices"), list) else []
    closes = [safe_float(item) for item in (source.get("closing_prices") or [])] if isinstance(source.get("closing_prices"), list) else []
    pairs = [(a, b) for a, b in zip(entries, closes) if a is not None and b is not None]
    if pairs:
        result["clv_proxy"] = round(sum(b - a for a, b in pairs) / len(pairs), 6)
    fills = [safe_float(item) for item in (source.get("fill_prices") or [])] if isinstance(source.get("fill_prices"), list) else []
    market_prices = [safe_float(item) for item in (source.get("entry_prices") or [])] if isinstance(source.get("entry_prices"), list) else []
    slip_pairs = [(a, b) for a, b in zip(fills, market_prices) if a is not None and b is not None]
    if slip_pairs:
        result["slippage_proxy"] = round(sum(a - b for a, b in slip_pairs) / len(slip_pairs), 6)
    return finalize_baseball_response(result, source_payload=source)

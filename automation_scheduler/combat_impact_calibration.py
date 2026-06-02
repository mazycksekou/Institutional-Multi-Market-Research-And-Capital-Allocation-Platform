from __future__ import annotations

from typing import Any

from .combat_impact_common import clamp, compact_list, finalize_combat_response, normalize_combat_market, normalize_combat_sport, safe_float


EXTRA_CONSERVATIVE_MARKETS = {"exact_round", "winning_method_round", "split_decision", "draw"}


def _count_outcomes(payload: dict[str, Any]) -> int:
    outcomes = payload.get("settled_outcomes")
    if isinstance(outcomes, list):
        return len(outcomes)
    return int(safe_float(payload.get("matched_outcomes_count"), 0.0) or 0)


def evaluate_combat_impact_calibration(
    payload: dict[str, Any] | None = None,
    *,
    sport: str = "combat_sports",
    market_type: str = "moneyline",
    ruleset: str | None = None,
    weight_class: str | None = None,
    scheduled_rounds: Any = None,
    data_tier: int = 0,
) -> dict[str, Any]:
    source = payload if isinstance(payload, dict) else {}
    market = normalize_combat_market(market_type)
    sample = _count_outcomes(source)
    required = 80
    if market in EXTRA_CONSERVATIVE_MARKETS:
        required = 250
    elif market in {"method_of_victory", "ko_tko", "submission", "inside_distance"}:
        required = 120
    insufficient = sample < required
    status = "insufficient_data" if sample == 0 else "partial_calibration" if insufficient else "calibration_ready"
    hit_rate = None
    false_positive = None
    outcomes = source.get("settled_outcomes")
    if isinstance(outcomes, list) and outcomes:
        hits = sum(1 for item in outcomes if isinstance(item, dict) and bool(item.get("hit")))
        hit_rate = round(hits / len(outcomes), 4)
        false_positive = round(1.0 - hit_rate, 4)
    result = {
        "calibration_status": status,
        "sample_size": sample,
        "matched_outcomes_count": sample,
        "insufficient_sample": insufficient,
        "hit_rate": hit_rate,
        "false_positive_rate": false_positive,
        "confidence_cap": 42.0 if sample == 0 else 58.0 if insufficient else 82.0,
        "next_required_data": compact_list(
            [
                "settled_combat_outcomes_by_market_ruleset_context",
                "larger_method_round_context_bucket_sample" if insufficient else None,
                "closing_prices_for_clv",
                "realized_returns_for_roi",
            ],
            limit=10,
        ),
        "calibration_buckets": {
            "sport": normalize_combat_sport(sport),
            "ruleset": ruleset or source.get("ruleset") or "unknown_ruleset",
            "market_type": market,
            "data_tier": data_tier,
            "scheduled_rounds": scheduled_rounds or source.get("scheduled_rounds") or "unknown_rounds",
            "weight_class": weight_class or source.get("weight_class") or "unknown_weight_class",
            "striking_bucket": source.get("striking_bucket", "unknown_striking"),
            "grappling_bucket": source.get("grappling_bucket", "unknown_grappling"),
            "durability_bucket": source.get("durability_bucket", "unknown_durability"),
            "cardio_bucket": source.get("cardio_bucket", "unknown_cardio"),
            "method_bucket": source.get("method_bucket", "unknown_method"),
            "round_bucket": source.get("round_bucket", "unknown_round"),
            "judging_bucket": source.get("judging_bucket", "unknown_judging"),
            "injury_weightcut_bucket": source.get("injury_weightcut_bucket", "unknown_injury_weightcut"),
            "liquidity_bucket": source.get("market_liquidity_bucket", source.get("liquidity_bucket", "unknown_liquidity")),
        },
        "exact_round_extra_conservative": market in {"exact_round", "winning_method_round"},
        "split_decision_extra_conservative": market == "split_decision",
    }
    if source.get("realized_returns") not in (None, ""):
        result["roi_proxy"] = source.get("realized_returns")
    if source.get("closing_prices") not in (None, "") and source.get("entry_prices") not in (None, ""):
        result["clv_proxy"] = "available"
    if source.get("fill_prices") not in (None, "") or source.get("slippage_observations") not in (None, ""):
        result["slippage_proxy"] = source.get("slippage_observations", "available")
    return finalize_combat_response(result, source_payload=source)

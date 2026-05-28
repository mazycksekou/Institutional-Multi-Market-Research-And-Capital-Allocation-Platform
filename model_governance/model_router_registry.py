from __future__ import annotations

from typing import Any

from .activation_tiers import tier_rank
from .model_inventory import get_model_inventory

SHORT_HORIZONS = {"intraday", "same_day", "short_term", "event"}
LONG_HORIZONS = {"long_term", "retirement", "strategic"}


def route_registered_models(
    *,
    market_type: str,
    model_purpose: str,
    time_horizon: str,
    activation_tier: str,
    available_inputs: dict[str, Any],
    settlement_rule_confidence: float = 100.0,
) -> dict[str, Any]:
    eligible_models: list[dict[str, Any]] = []
    blocked_models: list[dict[str, Any]] = []
    missing_inputs: set[str] = set()
    routing_reasons: list[str] = []

    for item in get_model_inventory():
        if item["model_purpose"] != model_purpose:
            continue
        if market_type == "sportsbook" and item["model_family"] == "institutional_investment_models":
            blocked_models.append({"model_id": item["model_id"], "reason": "retirement_and_allocation_models_blocked_for_short_term_trade"})
            routing_reasons.append("retirement_and_allocation_models_blocked_for_short_term_trade")
            continue
        if item["market_type"] not in {market_type, "multi_market"}:
            blocked_models.append({"model_id": item["model_id"], "reason": "wrong_market_type"})
            routing_reasons.append("wrong_market_type")
            continue
        if market_type == "stocks" and item["model_family"] == "sportsbook_models":
            blocked_models.append({"model_id": item["model_id"], "reason": "sportsbook_model_blocked_for_stock_decision"})
            routing_reasons.append("sportsbook_model_blocked_for_stock_decision")
            continue
        if item["time_horizon"] in LONG_HORIZONS and time_horizon in SHORT_HORIZONS:
            blocked_models.append({"model_id": item["model_id"], "reason": "wrong_time_horizon"})
            routing_reasons.append("wrong_time_horizon")
            continue
        if tier_rank(item["activation_tier"]) < tier_rank(activation_tier):
            blocked_models.append({"model_id": item["model_id"], "reason": "activation_tier_insufficient"})
            routing_reasons.append("activation_tier_insufficient")
            continue
        if market_type == "prediction_markets" and settlement_rule_confidence < 75:
            blocked_models.append({"model_id": item["model_id"], "reason": "prediction_market_settlement_risk_failure"})
            routing_reasons.append("prediction_market_settlement_risk_failure")
            continue
        item_missing = [field for field in item["inputs_required"] if available_inputs.get(field) is None]
        if item_missing:
            missing_inputs.update(item_missing)
            blocked_models.append({"model_id": item["model_id"], "reason": "missing_inputs", "missing_inputs": item_missing})
            continue
        eligible_models.append(item)

    return {
        "eligible_models": eligible_models,
        "blocked_models": blocked_models,
        "missing_inputs": sorted(missing_inputs),
        "routing_reason": "; ".join(sorted(set(routing_reasons))) if routing_reasons else "eligible_models_identified",
    }

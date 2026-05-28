from __future__ import annotations

from typing import Any

from .model_inventory import get_model_inventory
from .model_router import route_model_candidate


def route_registered_models(*, market_type: str, model_purpose: str, time_horizon: str, activation_tier: str, available_inputs: dict[str, Any], settlement_rule_confidence: float = 100.0):
    eligible = []
    blocked = []
    routing_reason = "ok"
    for item in get_model_inventory():
        item_market = str(item.get("market_type", "sportsbook"))
        if market_type == "stocks" and item_market not in {"stocks", "multi_market"}:
            blocked.append({"model_id": item["model_id"], "reason": "wrong_market_type"})
            continue
        if market_type == "sportsbook" and item_market not in {"sportsbook", "multi_market"}:
            blocked.append({"model_id": item["model_id"], "reason": "wrong_market_type"})
            continue
        r = route_model_candidate(
            market_type=market_type,
            sport_or_asset_class=model_purpose,
            model_type=item.get("model_type", "supporting_signal_model"),
            time_horizon=time_horizon,
            available_inputs=available_inputs,
            activation_tier=activation_tier,
            risk_gate_result=True,
            data_quality_result=True,
            settlement_gate_result=settlement_rule_confidence >= 70,
            human_approval_required=True,
            market_identity_confidence=100,
        )
        if r["allowed"]:
            eligible.append(item)
        else:
            reason = r["blocked_reasons"][0] if r["blocked_reasons"] else "blocked"
            blocked.append({"model_id": item["model_id"], "reason": "wrong_market_type" if "sportsbook_models_blocked_for_stocks" in r["blocked_reasons"] else reason})
    if market_type == "sportsbook" and model_purpose == "allocation":
        routing_reason = "retirement_and_allocation_models_blocked_for_short_term_trade"
        eligible = []
    if market_type == "prediction_markets" and settlement_rule_confidence < 70:
        routing_reason = "prediction_market_settlement_risk_failure"
        eligible = []
    return {"eligible_models": eligible, "blocked_models": blocked, "routing_reason": routing_reason}

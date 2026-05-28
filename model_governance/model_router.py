from __future__ import annotations

from typing import Any


def route_model_candidate(*, market_type: str, sport_or_asset_class: str, model_type: str, time_horizon: str, available_inputs: dict[str, Any], activation_tier: str, risk_gate_result: bool, data_quality_result: bool, settlement_gate_result: bool, human_approval_required: bool, market_identity_confidence: float = 100.0, is_execution_later_module: bool = False) -> dict[str, Any]:
    blocked: list[str] = []
    if model_type == "allocation_model" and market_type == "sportsbook":
        blocked.append("allocation_models_blocked_for_sportsbook")
    if model_type in {"primary_predictive_model", "cross_book_model"} and market_type == "stocks" and sport_or_asset_class == "sportsbook":
        blocked.append("sportsbook_models_blocked_for_stocks")
    if activation_tier == "research_only":
        blocked.append("research_only_blocked_from_scoring")
    if activation_tier == "backtest_ready":
        blocked.append("backtest_ready_blocked_from_live_review_queue")
    if activation_tier == "paper_trade_ready":
        blocked.append("paper_trade_ready_blocked_from_actionable_recommendation")
    if time_horizon == "long_term" and market_type == "sportsbook":
        blocked.append("wrong_horizon")
    if model_type in {"cross_book_model", "arbitrage_model", "middle_model"} and market_identity_confidence < 80:
        blocked.append("low_identity_confidence")
    if not risk_gate_result:
        blocked.append("risk_gate_failed")
    if not data_quality_result:
        blocked.append("data_quality_failed")
    if not settlement_gate_result:
        blocked.append("settlement_gate_failed")
    if is_execution_later_module:
        blocked.append("execution_later_blocked")
    return {"allowed": len(blocked) == 0 and human_approval_required, "blocked_reasons": blocked}

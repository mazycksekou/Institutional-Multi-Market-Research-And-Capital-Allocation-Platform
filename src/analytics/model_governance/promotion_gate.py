from __future__ import annotations

from typing import Any

from .activation_tiers import can_promote_one_tier
from .model_card import validate_model_card
from . import contains_banned_language


def evaluate_promotion_gate(*, model_card: dict[str, Any], inventory_item: dict[str, Any], target_tier: str, evidence_score: float | None = None, backtest_score: float = 0, calibration_score: float = 0, risk_score: float = 0, input_quality_score: float = 0, governance_score: float = 0, no_data_leakage_detected: bool = True, costs_supported: bool = True, challenger_decision: str = "needs_more_data", roi_reality_check_passed: bool = True, stale_data: bool = False, settlement_mismatch: bool = False, live_monitoring_history_exists: bool = False, acceptable_drawdown: bool = False, acceptable_clv: bool = False, acceptable_risk_of_ruin: bool = False) -> dict[str, Any]:
    current_tier = inventory_item["activation_tier"]
    blocked = []
    if not can_promote_one_tier(current_tier, target_tier):
        blocked.append("promotion_must_be_one_tier_at_a_time")
    v = validate_model_card(model_card)
    if not v["valid"]:
        blocked.append("model_card_incomplete")
    if contains_banned_language(model_card):
        blocked.append("prohibited_claim_language_detected")
    ev = inventory_item.get("evidence_score", evidence_score or 0) if evidence_score is None else evidence_score
    if current_tier == "research_only" and (ev < 70):
        blocked.append("evidence_score_below_threshold")
    if current_tier == "backtest_ready":
        if min(backtest_score, calibration_score, risk_score) < 70:
            blocked.append("backtest_or_calibration_or_risk_below_threshold")
        if not no_data_leakage_detected:
            blocked.append("data_leakage_detected")
        if not costs_supported:
            blocked.append("cost_model_missing")
    if current_tier == "paper_trade_ready":
        if input_quality_score < 75:
            blocked.append("input_quality_below_threshold")
        if challenger_decision == "challenger_rejected":
            blocked.append("challenger_rejected")
        if not roi_reality_check_passed:
            blocked.append("roi_reality_check_failed")
        if stale_data or settlement_mismatch:
            blocked.append("stale_or_settlement_block")
    if current_tier == "review_queue_ready":
        if min(calibration_score, input_quality_score, risk_score, governance_score) < 80:
            blocked.append("active_threshold_not_met")
    if current_tier == "active_scoring_ready":
        if not (live_monitoring_history_exists and acceptable_drawdown and acceptable_clv and acceptable_risk_of_ruin and challenger_decision == "challenger_promoted"):
            blocked.append("production_evidence_missing")
    return {"approved": not blocked, "previous_tier": current_tier, "new_tier": target_tier, "blocked_reasons": blocked, "promotion_gate_result": "approved" if not blocked else "blocked_by_governance", "human_approval_required": True, "auto_execution_allowed": False}

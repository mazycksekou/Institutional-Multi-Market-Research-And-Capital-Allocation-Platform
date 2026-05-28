from __future__ import annotations

from typing import Any

from . import contains_banned_language
from .activation_tiers import can_promote_one_tier
from .model_card import validate_model_card


def evaluate_promotion_gate(
    *,
    model_card: dict[str, Any],
    inventory_item: dict[str, Any],
    target_tier: str,
    sample_size_score: float = 0,
    no_data_leakage_detected: bool = True,
    costs_supported: bool = False,
    challenger_decision: str = "needs_more_data",
    roi_reality_check_passed: bool = False,
    drawdown_controls_pass: bool = False,
    stale_data: bool = False,
    settlement_mismatch: bool = False,
    positive_clv_history: bool = False,
    stable_drawdown: bool = False,
    acceptable_risk_of_ruin: bool = False,
) -> dict[str, Any]:
    current_tier = inventory_item["activation_tier"]
    blocked_reasons: list[str] = []
    gate_results: dict[str, Any] = {
        "current_tier": current_tier,
        "target_tier": target_tier,
        "sample_size_score": float(sample_size_score),
    }
    if not can_promote_one_tier(current_tier, target_tier):
        blocked_reasons.append("promotion_must_be_one_tier_at_a_time")
    card_validation = validate_model_card(model_card)
    gate_results["model_card_validation"] = card_validation
    if not card_validation["valid"]:
        blocked_reasons.append("model_card_incomplete")
    if contains_banned_language(model_card):
        blocked_reasons.append("prohibited_claim_language_detected")

    if current_tier == "research_only" and target_tier == "backtest_ready":
        if inventory_item["evidence_score"] < 70:
            blocked_reasons.append("evidence_score_below_threshold")
    elif current_tier == "backtest_ready" and target_tier == "paper_trade_ready":
        if inventory_item["backtest_score"] < 70:
            blocked_reasons.append("backtest_score_below_threshold")
        if inventory_item["calibration_score"] < 70:
            blocked_reasons.append("calibration_score_below_threshold")
        if inventory_item["risk_score"] < 70:
            blocked_reasons.append("risk_score_below_threshold")
        if not no_data_leakage_detected:
            blocked_reasons.append("data_leakage_detected")
        if not costs_supported:
            blocked_reasons.append("transaction_cost_support_missing")
    elif current_tier == "paper_trade_ready" and target_tier == "review_queue_ready":
        if inventory_item["walk_forward_score"] < 70:
            blocked_reasons.append("walk_forward_score_below_threshold")
        if inventory_item["drift_score"] < 70:
            blocked_reasons.append("drift_score_below_threshold")
        if sample_size_score < 70:
            blocked_reasons.append("sample_size_score_below_threshold")
        if challenger_decision == "challenger_rejected":
            blocked_reasons.append("challenger_rejected")
        if not roi_reality_check_passed:
            blocked_reasons.append("roi_reality_check_failed")
    elif current_tier == "review_queue_ready" and target_tier == "active_scoring_ready":
        if inventory_item["calibration_score"] < 80:
            blocked_reasons.append("calibration_score_below_active_threshold")
        if inventory_item["input_quality_score"] < 80:
            blocked_reasons.append("input_quality_score_below_active_threshold")
        if inventory_item["risk_score"] < 80:
            blocked_reasons.append("risk_score_below_active_threshold")
        if inventory_item["governance_score"] < 80:
            blocked_reasons.append("governance_score_below_active_threshold")
        if not drawdown_controls_pass:
            blocked_reasons.append("drawdown_controls_failed")
        if stale_data:
            blocked_reasons.append("stale_data_detected")
        if settlement_mismatch:
            blocked_reasons.append("settlement_mismatch_detected")
    elif current_tier == "active_scoring_ready" and target_tier == "production_candidate":
        if not positive_clv_history:
            blocked_reasons.append("clv_history_insufficient")
        if not stable_drawdown:
            blocked_reasons.append("drawdown_stability_failed")
        if not acceptable_risk_of_ruin:
            blocked_reasons.append("risk_of_ruin_unacceptable")
        if challenger_decision != "challenger_promoted":
            blocked_reasons.append("champion_challenger_not_approved")

    return {
        "approved": not blocked_reasons,
        "previous_tier": current_tier,
        "new_tier": target_tier,
        "gate_results": gate_results,
        "blocked_reasons": blocked_reasons,
        "promotion_gate_result": "approved" if not blocked_reasons else "blocked_by_governance",
    }


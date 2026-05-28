from __future__ import annotations

from . import contains_banned_language
from .activation_tiers import tier_allows_active_scoring, tier_allows_review_queue


def evaluate_review_queue_gate(*, activation_tier: str, evidence_score: float, input_quality_score: float, model_risk_rating: str, stale_data: bool, settlement_mismatch: bool, reason_text: str = "", opportunity_score: float = 0.0, human_approval_required: bool = True):
    blocked_reason = ""
    if not tier_allows_review_queue(activation_tier): blocked_reason = "activation_tier_below_review_queue_ready"
    elif evidence_score < 70: blocked_reason = "evidence_score_below_threshold"
    elif input_quality_score < 75: blocked_reason = "input_quality_score_below_threshold"
    elif model_risk_rating.lower() not in {"low", "moderate"}: blocked_reason = "model_risk_rating_unacceptable"
    elif stale_data: blocked_reason = "stale_data_detected"
    elif settlement_mismatch: blocked_reason = "settlement_mismatch_detected"
    elif contains_banned_language(reason_text): blocked_reason = "prohibited_claim_language_detected"
    elif not human_approval_required: blocked_reason = "human_approval_missing"
    can_enter = blocked_reason == ""
    return {"can_enter_review_queue": can_enter, "can_escalate_urgent": can_enter and opportunity_score >= 85, "can_affect_opportunity_score": can_enter and tier_allows_active_scoring(activation_tier), "can_affect_stake_recommendation": can_enter and activation_tier == "production_candidate", "blocked_reason": blocked_reason, "review_queue_gate_result": "approved" if can_enter else "blocked_by_governance"}

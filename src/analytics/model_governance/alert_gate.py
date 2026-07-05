from __future__ import annotations

def evaluate_alert_gate(*, activation_tier: str, opportunity_score: float, risk_gate_passed: bool, suppression_count: int = 0):
    if activation_tier == "research_only":
        return {"can_alert": False, "alert_priority": "none", "alert_reason": "research_only_blocked", "alert_suppression_reason": "tier_block"}
    if suppression_count >= 3:
        return {"can_alert": False, "alert_priority": "none", "alert_reason": "spam_suppressed", "alert_suppression_reason": "rate_limit"}
    if opportunity_score >= 85 and risk_gate_passed:
        return {"can_alert": True, "alert_priority": "urgent_review", "alert_reason": "positive_ev_candidate", "alert_suppression_reason": ""}
    return {"can_alert": True, "alert_priority": "watch_recheck", "alert_reason": "review_required", "alert_suppression_reason": ""}

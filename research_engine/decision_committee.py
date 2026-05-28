from __future__ import annotations


def committee_decision(evidence_score: float, risk_score: float, approval_status: str = "pending"):
    if approval_status != "approved":
        return {"decision": "review_required", "reason": "human approval pending"}
    if evidence_score >= 80 and risk_score >= 80:
        return {"decision": "research_supported_candidate", "reason": "meets governance thresholds"}
    return {"decision": "needs_revalidation", "reason": "thresholds not met"}

from __future__ import annotations


def evidence_scorecard(source_quality: float, mathematical_definition_exists: bool, peer_review_basis: bool, input_availability: bool, out_of_sample_testability: bool, risk_control_support: bool, no_guarantee_language: bool = True):
    score = source_quality
    score += 10 if mathematical_definition_exists else -20
    score += 10 if peer_review_basis else -10
    score += 10 if input_availability else -20
    score += 10 if out_of_sample_testability else -20
    score += 10 if risk_control_support else -20
    if not no_guarantee_language:
        score = min(score, 40)
    score = max(0, min(100, score))
    return {"evidence_score": score, "no_guarantee_language": no_guarantee_language}

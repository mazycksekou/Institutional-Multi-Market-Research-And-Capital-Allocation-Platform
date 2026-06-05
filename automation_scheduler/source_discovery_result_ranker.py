from __future__ import annotations

from typing import Any


POLICY_SCORE = {
    "approved_open_free": 100,
    "approved_open_metadata": 98,
    "approved_open_historical": 98,
    "approved_public_pdf": 94,
    "approved_public_sitemap": 93,
    "approved_structured_api": 96,
    "approved_paid_transport": 90,
    "approved_manual_csv": 88,
    "approved_supplemental_structured_wiki": 82,
    "needs_manual_review": 60,
    "needs_paid_retrieval": 55,
    "blocked_reference_site": 5,
    "blocked_terms": 10,
    "blocked_robots": 8,
    "blocked_license": 6,
    "blocked_paywall_or_login": 4,
    "blocked_captcha_or_session": 2,
    "blocked_unclear_policy_after_max_effort": 1,
    "unavailable_after_max_effort": 1,
    "rate_limited_after_max_effort": 20,
}


def rank_source_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for candidate in candidates:
        policy_status = str(candidate.get("policy_status") or "needs_manual_review")
        confidence = float(candidate.get("confidence", 0.0) or 0.0)
        estimated_coverage = float(candidate.get("estimated_coverage", 0.0) or 0.0)
        score = POLICY_SCORE.get(policy_status, 25) + (confidence * 20.0) + (estimated_coverage * 15.0)
        if str(candidate.get("accepted_or_rejected") or "accepted") == "rejected":
            score -= 50.0
        if str(candidate.get("retrieval_method_candidate") or "") in {"none", ""}:
            score -= 10.0
        ranked.append({**candidate, "rank_score": round(score, 3)})
    return sorted(ranked, key=lambda row: (row.get("rank_score", 0.0), row.get("confidence", 0.0)), reverse=True)


def summarize_ranked_sources(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    ranked = rank_source_candidates(candidates)
    return {
        "candidate_count": len(candidates),
        "ranked_count": len(ranked),
        "top_candidate": ranked[0] if ranked else {},
        "ranked_candidates": ranked,
    }

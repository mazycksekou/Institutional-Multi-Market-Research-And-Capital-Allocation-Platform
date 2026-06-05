from __future__ import annotations

from typing import Any

from .basketball_free_vs_paid_readiness import FREE_VS_PAID_CATEGORIES, SOURCE_REFERENCES


BLOCKED_BASKETBALL_DOMAINS = {
    "basketball-reference.com",
    "sports-reference.com",
    "college-basketball-reference.com",
    "kenpom.com",
    "cleaningtheglass.com",
    "synergysports.com",
}


def evaluate_basketball_source_policy(source_name: str, domain: str = "", source_type: str = "") -> dict[str, Any]:
    lower_name = str(source_name or "").lower()
    lower_domain = str(domain or "").lower().removeprefix("www.")
    lower_type = str(source_type or "").lower()
    if lower_domain in BLOCKED_BASKETBALL_DOMAINS or any(token in lower_name for token in ("basketball reference", "sports reference", "kenpom", "synergy", "cleaning the glass")):
        category = "blocked_reference_or_restricted_source"
        status = "blocked"
        reason = "blocked_by_basketball_source_policy"
    elif "paid" in lower_type or "vendor" in lower_type or any(token in lower_name for token in ("sportradar", "genius sports", "stats perform", "second spectrum")):
        category = "paid_data_subscription_required"
        status = "paid_required"
        reason = "paid_or_licensed_feed_required"
    elif "espn" in lower_name or "nba_api" in lower_name or "stats.wnba" in lower_name:
        category = "license_terms_unclear"
        status = "terms_review_required"
        reason = "direct_endpoint_terms_need_exact_path_review"
    else:
        category = "free_open_sample_required"
        status = "sample_allowed"
        reason = "sample_verification_allowed_with_no_raw_payload_persistence"
    return {
        "ok": True,
        "source_name": source_name,
        "domain": domain,
        "source_type": source_type,
        "free_or_paid_category": category,
        "policy_status": status,
        "reason": reason,
        "allowed_categories": list(FREE_VS_PAID_CATEGORIES),
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def basketball_source_policy_registry() -> dict[str, Any]:
    return {
        "ok": True,
        "status": "ok",
        "source_references": SOURCE_REFERENCES,
        "blocked_domains": sorted(BLOCKED_BASKETBALL_DOMAINS),
        "provider_write": False,
        "execution_allowed": False,
    }

from __future__ import annotations

from typing import Any

from .active_source_discovery_policy import build_paid_retrieval_policy_registry, evaluate_active_source_discovery_policy


MAX_EFFORT_POLICY_STATUSES = (
    "approved_open_free",
    "approved_open_metadata",
    "approved_open_historical",
    "approved_public_pdf",
    "approved_public_sitemap",
    "approved_structured_api",
    "approved_paid_transport",
    "approved_manual_csv",
    "approved_supplemental_structured_wiki",
    "needs_manual_review",
    "needs_paid_retrieval",
    "blocked_reference_site",
    "blocked_terms",
    "blocked_robots",
    "blocked_license",
    "blocked_paywall_or_login",
    "blocked_captcha_or_session",
    "blocked_unclear_policy_after_max_effort",
    "unavailable_after_max_effort",
    "rate_limited_after_max_effort",
)


def evaluate_max_effort_retrieval_policy(
    *,
    source_id: str,
    domain: str,
    allow_oxylabs: bool = True,
    allow_paid_retrieval: bool = True,
    source_allowlist: tuple[str, ...] = (),
    domain_allowlist: tuple[str, ...] = (),
    allow_active_discovery: bool = True,
    allow_search_discovery: bool = True,
    allow_schema_expansion: bool = True,
) -> dict[str, Any]:
    decision = evaluate_active_source_discovery_policy(
        source_id=source_id,
        domain=domain,
        allow_oxylabs=allow_oxylabs,
        allow_paid_retrieval=allow_paid_retrieval,
        source_allowlist=source_allowlist,
        domain_allowlist=domain_allowlist,
    )
    policy_status = decision.policy_status
    if decision.allowed:
        if allow_oxylabs and allow_paid_retrieval:
            policy_status = "approved_paid_transport"
        elif allow_search_discovery:
            policy_status = "approved_open_free"
        else:
            policy_status = "approved_open_metadata"
    elif policy_status == "blocked_unclear_policy" and allow_active_discovery:
        policy_status = "needs_manual_review"
    return {
        "allowed": decision.allowed,
        "policy_status": policy_status,
        "blocked_reason": decision.blocked_reason,
        "paid_source_enabled_count": decision.paid_source_enabled_count if allow_paid_retrieval and allow_oxylabs else 0,
        "allow_active_discovery": allow_active_discovery,
        "allow_search_discovery": allow_search_discovery,
        "allow_schema_expansion": allow_schema_expansion,
    }


def build_max_effort_policy_registry(*, sport: str, allow_oxylabs: bool = True, allow_paid_retrieval: bool = True) -> dict[str, Any]:
    registry = build_paid_retrieval_policy_registry(sport=sport)
    return {
        **registry,
        "run_mode": "user_approved_paid_retrieval_mode" if allow_oxylabs and allow_paid_retrieval else "open_free_mode",
        "allow_oxylabs": allow_oxylabs,
        "allow_paid_retrieval": allow_paid_retrieval,
        "paid_source_enabled_count": 1 if allow_oxylabs and allow_paid_retrieval and registry.get("paid_source_records") else 0,
    }

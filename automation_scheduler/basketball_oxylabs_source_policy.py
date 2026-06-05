from __future__ import annotations

from typing import Any

from .basketball_oxylabs_common import (
    OXYLABS_BASKETBALL_ALLOWED_DOMAINS,
    OXYLABS_BASKETBALL_ALLOWED_SOURCE_IDS,
    source_spec_registry,
)
from .retrieval_policy import domain_is_blocked, normalize_domain


BASKETBALL_BLOCKED_DOMAINS = {
    "basketball-reference.com",
    "sports-reference.com",
    "college-basketball-reference.com",
    "kenpom.com",
    "cleaningtheglass.com",
    "synergysports.com",
}


def evaluate_basketball_oxylabs_source_policy(
    *,
    source_id: str,
    domain: str,
    transport: str,
    allow_oxylabs: bool = True,
    allow_paid_retrieval: bool = True,
    source_type: str = "",
) -> dict[str, Any]:
    normalized_domain = normalize_domain(domain)
    source_spec = source_spec_registry().get(source_id)
    if not allow_oxylabs:
        return {
            "allowed": False,
            "policy_status": "blocked_paywall_or_login",
            "blocked_reason": "oxylabs_disabled_by_default",
            "oxylabs_used": False,
            "oxylabs_transport_used": "hard_blocked",
            "oxylabs_calls_attempted": 0,
            "oxylabs_calls_successful": 0,
            "oxylabs_calls_failed": 0,
            "paid_source_enabled_count": 0,
        }
    if not allow_paid_retrieval:
        return {
            "allowed": False,
            "policy_status": "blocked_paywall_or_login",
            "blocked_reason": "paid_retrieval_not_authorized",
            "oxylabs_used": False,
            "oxylabs_transport_used": "hard_blocked",
            "oxylabs_calls_attempted": 0,
            "oxylabs_calls_successful": 0,
            "oxylabs_calls_failed": 0,
            "paid_source_enabled_count": 0,
        }
    if source_spec is None and source_id not in OXYLABS_BASKETBALL_ALLOWED_SOURCE_IDS:
        return {
            "allowed": False,
            "policy_status": "blocked_unclear_policy",
            "blocked_reason": "source_id_not_allowlisted",
            "oxylabs_used": False,
            "oxylabs_transport_used": "hard_blocked",
            "oxylabs_calls_attempted": 0,
            "oxylabs_calls_successful": 0,
            "oxylabs_calls_failed": 0,
            "paid_source_enabled_count": 0,
        }
    if normalized_domain in BASKETBALL_BLOCKED_DOMAINS or domain_is_blocked(normalized_domain, tuple(BASKETBALL_BLOCKED_DOMAINS)):
        return {
            "allowed": False,
            "policy_status": "blocked_reference_site",
            "blocked_reason": "domain_blocklisted",
            "oxylabs_used": False,
            "oxylabs_transport_used": "hard_blocked",
            "oxylabs_calls_attempted": 0,
            "oxylabs_calls_successful": 0,
            "oxylabs_calls_failed": 0,
            "paid_source_enabled_count": 0,
        }
    if source_spec and source_spec.domain and normalized_domain and normalized_domain != normalize_domain(source_spec.domain):
        return {
            "allowed": False,
            "policy_status": "needs_manual_review",
            "blocked_reason": "domain_not_allowlisted",
            "oxylabs_used": False,
            "oxylabs_transport_used": "hard_blocked",
            "oxylabs_calls_attempted": 0,
            "oxylabs_calls_successful": 0,
            "oxylabs_calls_failed": 0,
            "paid_source_enabled_count": 0,
        }
    if source_spec and source_spec.policy_status == "paid_subscription_required":
        policy_status = "paid_required"
    elif source_spec and source_spec.policy_status == "manual_import_only":
        policy_status = "manual_import_required"
    elif source_spec and source_spec.policy_status == "license_terms_unclear":
        policy_status = "terms_review_required"
    elif source_spec and source_spec.policy_status == "supplemental_only":
        policy_status = "supplemental_only"
    elif source_spec and source_spec.policy_status == "blocked_reference_or_restricted_source":
        policy_status = "blocked_reference_site"
    elif source_spec and source_spec.policy_status == "approved_free_open_transport":
        policy_status = "approved_free_open_transport"
    else:
        policy_status = "approved_paid_transport"
    return {
        "allowed": True,
        "policy_status": policy_status,
        "blocked_reason": None,
        "oxylabs_used": True,
        "oxylabs_transport_used": transport,
        "oxylabs_calls_attempted": 1,
        "oxylabs_calls_successful": 1,
        "oxylabs_calls_failed": 0,
        "paid_source_enabled_count": 1,
        "domain": normalized_domain,
        "source_id": source_id,
        "source_type": source_type or (source_spec.source_type if source_spec else ""),
    }


def basketball_oxylabs_policy_registry() -> dict[str, Any]:
    return {
        "ok": True,
        "status": "ok",
        "allowed_source_ids": list(OXYLABS_BASKETBALL_ALLOWED_SOURCE_IDS),
        "allowed_domains": list(OXYLABS_BASKETBALL_ALLOWED_DOMAINS),
        "blocked_domains": sorted(BASKETBALL_BLOCKED_DOMAINS),
        "source_references": {
            key: {
                "source_name": value.source_name,
                "domain": value.domain,
                "transport": value.transport,
                "policy_status": value.policy_status,
                "license_or_terms_note": value.license_or_terms_note,
            }
            for key, value in source_spec_registry().items()
        },
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }

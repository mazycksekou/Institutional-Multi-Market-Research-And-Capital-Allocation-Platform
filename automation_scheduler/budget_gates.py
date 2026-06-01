from __future__ import annotations

from typing import Any


CURRENT_ACCESS_TYPES = {
    "open_public",
    "free_key",
    "free_tier",
    "open_dataset",
    "public_wrapper_with_terms_review",
    "manual_import",
}

BUDGETED_ACCESS_TYPES = {
    "paid_candidate",
    "partner_candidate",
    "institutional_vendor_candidate",
    "broker_data_candidate",
    "sportsbook_account_candidate",
    "internal_proprietary_candidate",
}

LIMITED_CALL_ACCESS_TYPES = {"free_key", "free_tier"}


def default_approval_status(
    *,
    source_access_type: str,
    future_source_candidate: bool = False,
    requires_paid_subscription: bool = False,
    requires_terms_review: bool = True,
    current_phase_allowed: bool = False,
    verified_at: str | None = None,
) -> str:
    access_type = str(source_access_type or "unknown")
    budget_required = bool(
        future_source_candidate
        or requires_paid_subscription
        or access_type in BUDGETED_ACCESS_TYPES
    )
    if budget_required:
        return "not_approved"
    if requires_terms_review:
        return "needs_review"
    if current_phase_allowed and verified_at:
        return "approved_for_research"
    return "candidate"


def build_budget_gate(
    *,
    source_access_type: str,
    requires_api_key: bool = False,
    requires_paid_subscription: bool = False,
    future_source_candidate: bool = False,
    approval_status: str | None = None,
) -> dict[str, Any]:
    access_type = str(source_access_type or "unknown")
    budget_required = bool(
        future_source_candidate
        or requires_paid_subscription
        or access_type in BUDGETED_ACCESS_TYPES
    )
    limited_call = bool(requires_api_key or access_type in LIMITED_CALL_ACCESS_TYPES)
    paid_upgrade_required = bool(budget_required or requires_paid_subscription)
    approval = str(approval_status or ("not_approved" if budget_required else "candidate"))
    approved_budget = approval in {"approved_budget", "approved_paid_upgrade", "approved_substantial_usage"}

    if budget_required:
        call_budget_level = "blocked_pending_budget_approval"
        max_provider_calls_default = 0
        max_provider_calls_hard_cap = 0
    elif access_type in {"open_dataset", "manual_import"}:
        call_budget_level = "offline_or_manual_no_provider_calls"
        max_provider_calls_default = 0
        max_provider_calls_hard_cap = 0
    elif limited_call:
        call_budget_level = "no_call_audit_default_tiny_sample_if_explicit"
        max_provider_calls_default = 0
        max_provider_calls_hard_cap = 3
    else:
        call_budget_level = "no_call_audit_default"
        max_provider_calls_default = 0
        max_provider_calls_hard_cap = 1

    return {
        "requires_budget_approval": budget_required,
        "verification_phase_allowed": bool(access_type in CURRENT_ACCESS_TYPES and not budget_required),
        "call_budget_level": call_budget_level,
        "max_provider_calls_default": max_provider_calls_default,
        "max_provider_calls_hard_cap": max_provider_calls_hard_cap,
        "paid_upgrade_required": paid_upgrade_required,
        "paid_upgrade_allowed": bool(approved_budget and paid_upgrade_required),
        "substantial_usage_allowed": bool(approval == "approved_substantial_usage"),
    }


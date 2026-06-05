from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .paid_retrieval_source_registry import OXYLABS_REQUIRED_BLOCKLIST_DOMAINS, paid_retrieval_sources_for
from .retrieval_policy import RetrievalPolicy, normalize_domain


POLICY_STATUS_MAP = {
    "oxylabs_disabled_by_default": "blocked_paywall_or_login",
    "paid_retrieval_not_authorized": "blocked_paywall_or_login",
    "source_id_not_allowlisted": "blocked_unclear_policy",
    "domain_blocklisted": "blocked_reference_site",
    "domain_not_allowlisted": "needs_manual_review",
}


@dataclass(frozen=True)
class ActiveDiscoveryDecision:
    allowed: bool
    policy_status: str
    blocked_reason: str | None
    paid_source_enabled_count: int


def evaluate_active_source_discovery_policy(
    *,
    source_id: str,
    domain: str,
    allow_oxylabs: bool = False,
    allow_paid_retrieval: bool = False,
    source_allowlist: tuple[str, ...] = (),
    domain_allowlist: tuple[str, ...] = (),
    domain_blocklist: tuple[str, ...] = OXYLABS_REQUIRED_BLOCKLIST_DOMAINS,
) -> ActiveDiscoveryDecision:
    result = RetrievalPolicy(
        allow_oxylabs=allow_oxylabs,
        allow_paid_retrieval=allow_paid_retrieval,
        source_id=source_id,
        domain=domain,
        source_allowlist=source_allowlist,
        domain_allowlist=domain_allowlist,
        domain_blocklist=domain_blocklist,
    ).evaluate()
    blocked_reason = result.get("blocked_reason")
    policy_status = "approved_paid_transport" if bool(result.get("allowed")) else POLICY_STATUS_MAP.get(str(blocked_reason), "blocked_unclear_policy")
    return ActiveDiscoveryDecision(
        allowed=bool(result.get("allowed")),
        policy_status=policy_status,
        blocked_reason=str(blocked_reason) if blocked_reason else None,
        paid_source_enabled_count=int(result.get("paid_source_enabled_count", 0) or 0),
    )


def build_paid_retrieval_policy_registry(*, sport: str) -> dict[str, Any]:
    records = paid_retrieval_sources_for(sport)
    return {
        "sport": str(sport).lower(),
        "paid_source_records": [
            {
                "sport": record.sport,
                "source_id": record.source_id,
                "domain": normalize_domain(record.domain),
                "retrieval_method": record.retrieval_method,
                "terms_or_license_status": record.terms_or_license_status,
                "source_type": record.source_type,
            }
            for record in records
        ],
        "paid_source_enabled_count": 1 if records else 0,
        "domain_blocklist": list(OXYLABS_REQUIRED_BLOCKLIST_DOMAINS),
    }


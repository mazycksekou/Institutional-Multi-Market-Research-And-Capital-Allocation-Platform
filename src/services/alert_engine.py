from __future__ import annotations

import re
from typing import Any

from src.market_intelligence.opportunity_scoring import classify_opportunity

BANNED_WORDS = ("lock", "guaranteed", "risk-free", "sure thing", "can't lose", "cant lose")


def contains_banned_language(text: str) -> bool:
    lowered = text.lower()
    normalized = lowered.replace("\u2019", "'")
    return any(word in normalized for word in BANNED_WORDS)


def sanitize_reason(reason: str) -> tuple[str, list[str]]:
    if not reason:
        return "", []
    sanitized = reason
    blockers: list[str] = []
    for word in BANNED_WORDS:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        if pattern.search(sanitized):
            sanitized = pattern.sub("[redacted banned phrase]", sanitized)
            if "contains_banned_language" not in blockers:
                blockers.append("contains_banned_language")
    return sanitized, blockers


def build_alert(candidate: dict[str, Any], thresholds: dict[str, Any]) -> dict[str, Any]:
    base_blockers = list(candidate.get("blockers") or [])
    sanitized_reason, language_blockers = sanitize_reason(str(candidate.get("reason") or ""))
    for blocker in language_blockers:
        if blocker not in base_blockers:
            base_blockers.append(blocker)

    action = classify_opportunity(float(candidate.get("opportunity_score", 0)), thresholds)
    governance_status = str(candidate.get("governance_status") or "")
    review_queue_gate_result = str(candidate.get("review_queue_gate_result") or "")
    if governance_status == "blocked_by_governance" or review_queue_gate_result == "blocked_by_governance":
        if "blocked_by_governance" not in base_blockers:
            base_blockers.append("blocked_by_governance")
    if base_blockers:
        action = "no_bet"

    return {
        "recommended_action": action,
        "reason": sanitized_reason,
        "governance_status": "blocked_by_governance" if "blocked_by_governance" in base_blockers else "review_required",
        "blockers": base_blockers,
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "auto_bet_enabled": False,
        "auto_trade_enabled": False,
    }


def generate_alert_candidates(
    review_items: list[dict[str, Any]],
    *,
    max_alerts: int = 25,
    time_bucket: str | None = None,
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in review_items:
        reasons = list(item.get("reason_codes") or [])
        if not reasons and item.get("reason"):
            reasons = [str(item.get("reason"))]
        for reason in reasons:
            dedupe_key = "|".join(
                [
                    str(item.get("provider_id", item.get("provider", "unknown"))),
                    str(item.get("ticker") or item.get("contract_id") or item.get("id") or "unknown"),
                    str(reason),
                    str(time_bucket or "run"),
                ]
            )
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            severity = "watch"
            if reason in {"provider_blocker_warning", "stale_market", "low_liquidity"}:
                severity = "warning"
            if reason in {"status_change", "close_time_approaching"}:
                severity = "info"
            alerts.append(
                {
                    "alert_id": f"alert_{len(alerts)+1:04d}",
                    "provider": item.get("provider_id", item.get("provider")),
                    "reason": reason,
                    "severity": severity,
                    "review_item_id": item.get("id"),
                    "execution_allowed": False,
                    "human_approval_required": True,
                    "created_at": item.get("updated_at") or item.get("created_at"),
                    "summary": {
                        "ticker": item.get("ticker"),
                        "contract_id": item.get("contract_id"),
                        "event_name": item.get("event_name") or item.get("event_title"),
                        "recommendation_status": item.get("recommendation_status", "review_only"),
                    },
                }
            )
            if len(alerts) >= max_alerts:
                return alerts
    return alerts

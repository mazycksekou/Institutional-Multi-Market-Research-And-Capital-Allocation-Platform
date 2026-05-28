from __future__ import annotations

import re
from typing import Any

from .opportunity_scoring import classify_opportunity

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

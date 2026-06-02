from __future__ import annotations

from typing import Any, Mapping

from .hard_gate_policy import evaluate_hard_gates
from .secret_safety import redact_sensitive
from .security_policy import detect_execution_authority_violations, locked_safety_flags


def _as_score(value: Any, default: float = 0.0) -> float:
    try:
        return max(0.0, min(100.0, float(value)))
    except (TypeError, ValueError):
        return default


def evaluate_future_execution_eligibility(
    candidate: Mapping[str, Any] | None = None,
    *,
    aggregate: Mapping[str, Any] | None = None,
    hard_gate_result: Mapping[str, Any] | None = None,
    actor_type: str = "system",
) -> dict[str, Any]:
    safe_candidate = redact_sensitive(dict(candidate or {}))
    aggregate = redact_sensitive(dict(aggregate or {}))
    violations = detect_execution_authority_violations({"candidate": safe_candidate, "aggregate": aggregate})
    blockers: list[str] = []
    warnings: list[str] = []

    if actor_type == "ai_provider":
        if bool(safe_candidate.get("future_execution_eligible")) or bool(aggregate.get("future_execution_eligible")):
            blockers.append("ai_cannot_set_future_execution_eligible")
        if bool(safe_candidate.get("execution_allowed")) or bool(aggregate.get("execution_allowed")):
            blockers.append("ai_cannot_set_execution_allowed")
    blockers.extend(violations)

    hard = dict(hard_gate_result or evaluate_hard_gates(safe_candidate, persist_audit=False))
    if hard.get("failed_hard_gates"):
        blockers.append("hard_security_gate_locked")
    if bool(aggregate.get("fatal_safety_blocker")):
        blockers.append("fatal_safety_blocker")
    if _as_score(aggregate.get("weighted_score")) < 85:
        blockers.append("strategy_evidence_not_strong_enough")
    if _as_score(aggregate.get("calibration_support_score")) < 70:
        blockers.append("calibration_sample_not_sufficient")
    if _as_score(aggregate.get("liquidity_risk_score"), 100.0) > 30:
        blockers.append("liquidity_or_spread_risk_not_acceptable")
    if _as_score(aggregate.get("trap_risk_score"), 100.0) > 30:
        blockers.append("red_team_or_trap_risk_not_clear")

    future_eligible = not bool(blockers)
    if future_eligible:
        warnings.append("future_execution_eligible_is_not_current_execution_authority")

    return {
        "ok": True,
        "status": "future_execution_eligible_review_only" if future_eligible else "future_execution_blocked",
        "candidate_id": safe_candidate.get("candidate_id") or safe_candidate.get("id") or safe_candidate.get("ticker"),
        "future_execution_eligible": bool(future_eligible),
        "future_execution_blockers": sorted(set(blockers)),
        "future_execution_warnings": warnings,
        "hard_gate_status": hard.get("hard_gate_status", "locked"),
        "owner_approval_still_required": True,
        "execution_flags_still_need_explicit_enablement": True,
        **locked_safety_flags(),
    }

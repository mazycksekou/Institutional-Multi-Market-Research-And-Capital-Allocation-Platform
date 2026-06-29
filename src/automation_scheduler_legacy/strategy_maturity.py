from __future__ import annotations

from typing import Any, Mapping

from .security_policy import locked_safety_flags
from .strategy_context_buckets import candidate_available_inputs
from .strategy_registry import normalize_strategy_record


CONTROL_MATURITY_STATUSES = {"active_review", "active_ranking", "execution_eligible_future"}
NON_CONTROL_MATURITY_STATUSES = {"research_only", "calibration_only", "inactive"}
BLOCKED_MATURITY_STATUSES = {
    "disabled",
    "demoted",
    "blocked_insufficient_data",
    "blocked_missing_dependency",
    "blocked_safety_review",
}


def missing_required_inputs(strategy: Mapping[str, Any], candidate: Mapping[str, Any] | None = None) -> list[str]:
    available = candidate_available_inputs(candidate)
    required = [str(item) for item in list(strategy.get("required_inputs") or [])]
    return [item for item in required if item not in available]


def evaluate_strategy_maturity(
    strategy: Mapping[str, Any],
    *,
    candidate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    row = normalize_strategy_record(strategy)
    maturity = str(row.get("maturity_status") or "inactive")
    missing = missing_required_inputs(row, candidate)
    blocked_reason = row.get("blocked_reason")
    if not bool(row.get("enabled", True)):
        maturity = "disabled"
        blocked_reason = blocked_reason or "strategy_disabled"
    elif missing:
        maturity = "blocked_missing_dependency"
        blocked_reason = f"missing_required_inputs:{','.join(missing)}"
    elif int(row.get("current_sample_size", 0) or 0) < int(row.get("minimum_sample_size", 0) or 0):
        if maturity in {"active_review", "active_ranking", "execution_eligible_future"}:
            maturity = "blocked_insufficient_data"
            blocked_reason = blocked_reason or "current_sample_below_minimum"

    can_affect_review = maturity in CONTROL_MATURITY_STATUSES and bool(row.get("affects_review_queue", False))
    can_affect_ranking = maturity in {"active_ranking", "execution_eligible_future"} and bool(row.get("affects_ranking", False))
    can_affect_execution = False
    if maturity in {"research_only", "calibration_only"}:
        can_affect_review = False if maturity == "research_only" else bool(row.get("affects_review_queue", False))
        can_affect_ranking = False

    status = "blocked" if maturity in BLOCKED_MATURITY_STATUSES else "routable"
    return {
        "strategy_id": row.get("strategy_id"),
        "maturity_status": maturity,
        "status": status,
        "blocked": maturity in BLOCKED_MATURITY_STATUSES,
        "blocked_reason": blocked_reason,
        "missing_required_inputs": missing,
        "missing_optional_inputs": [
            item for item in [str(x) for x in list(row.get("optional_inputs") or [])] if item not in candidate_available_inputs(candidate)
        ],
        "can_affect_review": bool(can_affect_review),
        "can_affect_ranking": bool(can_affect_ranking),
        "can_affect_execution": can_affect_execution,
        "research_only_cannot_control_final_action": maturity == "research_only",
        "calibration_only_cannot_execute": maturity == "calibration_only",
        **locked_safety_flags(),
    }

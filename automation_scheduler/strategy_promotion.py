from __future__ import annotations

from typing import Any, Mapping

from .execution_gatekeeper import evaluate_future_execution_eligibility
from .secret_safety import redact_sensitive
from .security_policy import locked_safety_flags
from .strategy_context_buckets import build_context_bucket
from .strategy_registry import normalize_strategy_record


PROMOTION_STATUSES = {
    "not_ready",
    "monitor",
    "promote_to_active_review",
    "promote_to_active_ranking",
    "eligible_for_future_execution_review",
    "demote_to_calibration_only",
    "disable_strategy",
}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def evaluate_strategy_promotion(
    strategy: Mapping[str, Any],
    evidence: Mapping[str, Any] | None = None,
    *,
    context_candidate: Mapping[str, Any] | None = None,
    actor_type: str = "system",
) -> dict[str, Any]:
    row = normalize_strategy_record(strategy)
    safe_evidence = redact_sensitive(dict(evidence or {}))
    bucket = build_context_bucket(context_candidate or safe_evidence)
    sample = int(_float(safe_evidence.get("sample_size") or safe_evidence.get("current_sample_size"), row.get("current_sample_size", 0)))
    minimum = int(_float(safe_evidence.get("minimum_sample_size"), row.get("minimum_sample_size", 30)))
    outcome_coverage = _float(safe_evidence.get("outcome_coverage"), row.get("outcome_coverage", 0.0))
    calibration_error = _float(safe_evidence.get("calibration_error"), 1.0)
    false_positive_rate = _float(safe_evidence.get("false_positive_rate"), 1.0)
    expected_value = _float(safe_evidence.get("expected_value"), 0.0)
    average_return = _float(safe_evidence.get("average_return"), 0.0)
    average_clv = _float(safe_evidence.get("average_closing_line_value") or safe_evidence.get("average_clv"), 0.0)
    drawdown = abs(_float(safe_evidence.get("drawdown") or safe_evidence.get("max_drawdown"), 1.0))
    liquidity_adjusted = _float(safe_evidence.get("liquidity_adjusted_performance"), expected_value)
    stability_time = _float(safe_evidence.get("stability_across_time"), 0.0)
    stability_provider = _float(safe_evidence.get("stability_across_providers"), 0.0)
    reasons: list[str] = []

    if actor_type == "ai_provider":
        return {
            "ok": True,
            "status": "not_ready",
            "strategy_id": row.get("strategy_id"),
            "promotion_status": "not_ready",
            "promotion_reasons": ["ai_cannot_promote_strategy_or_set_execution_eligibility"],
            "context_bucket": bucket,
            "context_specific": True,
            "future_execution_eligible": False,
            **locked_safety_flags(),
        }
    if sample < minimum:
        status = "not_ready"
        reasons.append("insufficient_sample")
    elif false_positive_rate >= 0.65:
        status = "disable_strategy"
        reasons.append("false_positive_rate_severe")
    elif false_positive_rate >= 0.45 or expected_value < 0 or liquidity_adjusted < 0:
        status = "demote_to_calibration_only"
        reasons.append("negative_or_unstable_liquidity_adjusted_performance")
    elif outcome_coverage < 0.3 or calibration_error > 0.18:
        status = "monitor"
        reasons.append("coverage_or_calibration_not_ready")
    elif (
        sample >= max(minimum * 3, 150)
        and outcome_coverage >= 0.65
        and calibration_error <= 0.06
        and expected_value > 0
        and average_return >= 0
        and average_clv > 0
        and drawdown <= 0.2
        and stability_time >= 0.6
        and stability_provider >= 0.5
    ):
        status = "promote_to_active_ranking"
        reasons.append("strong_context_specific_outcome_evidence")
    elif expected_value > 0 and average_clv >= 0 and calibration_error <= 0.12:
        status = "promote_to_active_review"
        reasons.append("sufficient_real_outcome_evidence_for_review")
    else:
        status = "monitor"
        reasons.append("mixed_evidence_monitor")

    future = evaluate_future_execution_eligibility(
        {"candidate_id": row.get("strategy_id"), **bucket},
        aggregate={
            "weighted_score": 90 if status == "promote_to_active_ranking" else 75,
            "calibration_support_score": min(100.0, outcome_coverage * 100.0),
            "liquidity_risk_score": 25 if liquidity_adjusted > 0 else 70,
            "trap_risk_score": 25 if false_positive_rate < 0.25 else 70,
        },
    )
    return {
        "ok": True,
        "status": status,
        "strategy_id": row.get("strategy_id"),
        "strategy_family": row.get("strategy_family"),
        "promotion_status": status,
        "demotion_status": status if status in {"demote_to_calibration_only", "disable_strategy"} else "none",
        "sample_size": sample,
        "minimum_sample_size": minimum,
        "outcome_coverage": outcome_coverage,
        "calibration_error": calibration_error,
        "false_positive_rate": false_positive_rate,
        "expected_value": expected_value,
        "average_return": average_return,
        "average_closing_line_value": average_clv,
        "drawdown": drawdown,
        "liquidity_adjusted_performance": liquidity_adjusted,
        "promotion_reasons": reasons,
        "context_bucket": bucket,
        "context_specific": True,
        "future_execution_eligible": False,
        "future_execution_review_status": future.get("status"),
        "future_execution_blockers": list(future.get("future_execution_blockers") or [])[:20],
        "promotion_does_not_enable_execution": True,
        "owner_security_review_required_for_future_execution": True,
        **locked_safety_flags(),
    }

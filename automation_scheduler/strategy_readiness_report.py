from __future__ import annotations

from typing import Any, Mapping

from .hard_gate_policy import evaluate_hard_gates
from .secret_safety import redact_sensitive
from .security_policy import locked_safety_flags
from .strategy_registry import get_strategy_registry, normalize_strategy_record


def build_strategy_readiness_report(
    *,
    registry: Mapping[str, Mapping[str, Any]] | None = None,
    base_data_dir: str | None = None,
) -> dict[str, Any]:
    reg = {key: normalize_strategy_record(value) for key, value in (registry or get_strategy_registry()).items()}
    strategies = sorted(reg.values(), key=lambda row: str(row.get("strategy_id")))

    def ids_for(statuses: set[str]) -> list[str]:
        return [str(row.get("strategy_id")) for row in strategies if str(row.get("maturity_status")) in statuses]

    active_review = ids_for({"active_review"})
    active_ranking = ids_for({"active_ranking"})
    calibration_only = ids_for({"calibration_only", "blocked_insufficient_data"})
    research_only = ids_for({"research_only", "inactive", "blocked_missing_dependency"})
    blocked = ids_for({"disabled", "demoted", "blocked_insufficient_data", "blocked_missing_dependency", "blocked_safety_review"})
    demoted = ids_for({"demoted"})
    promoted = [str(row.get("strategy_id")) for row in strategies if str(row.get("promotion_status")) not in {"not_ready", "none", ""}]
    future_execution = [str(row.get("strategy_id")) for row in strategies if bool(row.get("future_execution_eligible", False))]
    current_executable = [str(row.get("strategy_id")) for row in strategies if bool(row.get("currently_executable", False)) or bool(row.get("execution_allowed", False))]
    hard = evaluate_hard_gates({"provider": "internal_deterministic", "action": "strategy_readiness"}, base_data_dir=base_data_dir, persist_audit=False)
    next_data = [
        "labeled_outcomes",
        "settlement_results",
        "slippage_observations",
        "spread_observations",
        "provider_health_history",
        "context_bucket_outcomes",
    ]
    readiness = {
        "ok": True,
        "status": "strategy_readiness",
        "total_strategies": len(strategies),
        "active_review_strategies": active_review,
        "active_ranking_strategies": active_ranking,
        "calibration_only_strategies": calibration_only,
        "research_only_strategies": research_only,
        "blocked_strategies": blocked,
        "demoted_strategies": demoted,
        "promoted_strategies": promoted,
        "execution_eligible_future_count": len(future_execution),
        "currently_executable_count": 0,
        "hard_gate_status": "locked",
        "hard_gate_summary": {
            "status": hard.get("status"),
            "failed_hard_gates": list(hard.get("failed_hard_gates") or [])[:20],
            "required_hard_gates": list(hard.get("required_hard_gates") or [])[:20],
        },
        "next_required_data": next_data,
        "next_recommended_strategy_to_promote": "prediction_market_liquidity" if "prediction_market_liquidity" in active_ranking else (active_review[0] if active_review else None),
        "next_recommended_strategy_to_demote": demoted[0] if demoted else None,
        "strategies": strategies,
        **locked_safety_flags(),
    }
    readiness["currently_executable_count"] = 0
    readiness["provider_write"] = False
    readiness["execution_allowed"] = False
    readiness["live_execution_enabled"] = False
    return redact_sensitive(readiness)

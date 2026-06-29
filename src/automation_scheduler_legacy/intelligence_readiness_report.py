from __future__ import annotations

from collections import Counter
from typing import Any

from .data_intelligence_registry import build_data_intelligence_registry
from src.data.data_paths import get_storage_health, resolve_base_data_dir
from .manifold_feature_builder import infer_asset_type
from .outcome_store import load_outcome_records
from .security_readiness_report import build_security_readiness_report
from src.security.policy import locked_safety_flags


def _asset_type_for_outcome(row: dict[str, Any]) -> str:
    inferred = infer_asset_type(row)
    if inferred:
        return inferred
    provider = str(row.get("provider") or "").lower()
    if "kalshi" in provider or "prediction" in provider:
        return "prediction_market"
    if "sportsbook" in provider or "sharp" in provider:
        return "sportsbook"
    return "unknown"


def _outcome_coverage(records: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(_asset_type_for_outcome(row) for row in records if isinstance(row, dict))
    total = max(1, len(records))
    return {
        asset_type: {
            "labeled_outcomes": count,
            "outcome_coverage": round(count / total, 6),
        }
        for asset_type, count in sorted(counts.items())
    }


def _bucket_models(models: list[dict[str, Any]], status: str) -> list[str]:
    return [
        str(row.get("model_name") or row.get("model_family"))
        for row in models
        if str(row.get("model_maturity_status")) == status
    ]


def _blocked_models(models: list[dict[str, Any]]) -> list[str]:
    return [
        str(row.get("model_name") or row.get("model_family"))
        for row in models
        if str(row.get("model_maturity_status") or "").startswith("blocked")
    ]


def build_intelligence_readiness_report(*, base_data_dir: str = "data") -> dict[str, Any]:
    base = str(resolve_base_data_dir(base_data_dir))
    outcomes = load_outcome_records(base)
    total_labeled = len(outcomes)
    coverage = _outcome_coverage(outcomes)
    coverage_values = {
        asset_type: payload.get("outcome_coverage", 0.0)
        for asset_type, payload in coverage.items()
        if isinstance(payload, dict)
    }
    registry = build_data_intelligence_registry(
        total_labeled_outcomes=total_labeled,
        outcome_coverage_by_asset_type=coverage_values,
    )
    maturity = registry.get("model_maturity_registry", {})
    models = [row for row in maturity.get("models", []) if isinstance(row, dict)]
    active_review = _bucket_models(models, "active_review")
    active_calibration = _bucket_models(models, "active_calibration")
    calibration_only = _bucket_models(models, "calibration_only")
    research_only = _bucket_models(models, "research_only")
    blocked = _blocked_models(models)
    safety = build_security_readiness_report(base_data_dir=base)
    feasible_now = [
        "deterministic_representation_vectors",
        "graph_relationship_mapping",
        "out_of_distribution_detection",
        "no_bet_no_trade_trap_detection",
        "calibration_outcome_tracking",
    ]
    if total_labeled >= 30:
        feasible_now.append("manifold_nearest_neighbor_review_priority")
    feasible_later = [
        "markov_chain_transition_modeling",
        "hidden_markov_model_regime_diagnostics",
        "monte_carlo_risk_calibration",
        "xgboost_calibration",
        "lightgbm_calibration",
        "mdp_review_policy_optimization",
        "causal_effect_testing",
    ]
    next_required_data = [
        "more_labeled_outcomes_by_asset_type",
        "stable_join_keys_between_signals_and_outcomes",
        "train_validation_split_for_tabular_lanes",
        "feature_leakage_tests",
        "confounder_capture_for_causal_scaffold",
        "ordered_state_transition_history_for_markov_hmm",
    ]
    payload = {
        "ok": True,
        "status": "intelligence_readiness",
        "active_review_models": active_review,
        "active_calibration_models": active_calibration,
        "calibration_only_models": calibration_only,
        "research_only_models": research_only,
        "blocked_models": blocked,
        "active_review_count": len(active_review),
        "active_calibration_count": len(active_calibration),
        "calibration_only_count": len(calibration_only),
        "research_only_count": len(research_only),
        "blocked_count": len(blocked),
        "total_labeled_outcomes": total_labeled,
        "outcome_coverage_by_asset_type": coverage,
        "feasible_now": feasible_now,
        "feasible_later": feasible_later,
        "research_only": registry.get("research_only", []),
        "next_required_data": next_required_data,
        "safety_status": {
            "status": safety.get("status"),
            "security_posture": safety.get("security_posture"),
            "provider_write_firewall": safety.get("provider_write_firewall"),
            "kill_switches_active": bool(safety.get("kill_switches_active", True)),
            "ai_execution_authority": safety.get("ai_execution_authority"),
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "human_approval_required": True,
            "owner_approval_required": True,
        },
        "registry_summary": {
            "schema_version": registry.get("schema_version"),
            "supported_domains": registry.get("supported_domains", []),
            "build_now": registry.get("build_now", []),
            "build_later": registry.get("build_later", []),
            "research_only": registry.get("research_only", []),
        },
        "storage_backend": "file",
        "storage_health": get_storage_health(),
        "raw_payload_included": False,
        "secrets_included": False,
        "compact_response": True,
    }
    payload.update(locked_safety_flags())
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
    return payload

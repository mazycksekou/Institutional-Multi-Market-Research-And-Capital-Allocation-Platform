from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from .security_policy import locked_safety_flags


MODEL_MATURITY_STATUSES = {
    "active_review",
    "active_calibration",
    "calibration_only",
    "research_only",
    "disabled",
    "blocked_insufficient_data",
    "blocked_missing_dependency",
    "blocked_safety_review",
}

SUPPORTED_ASSET_TYPES = (
    "prediction_market",
    "sportsbook",
    "stock",
    "crypto",
    "etf",
    "bond_rate",
    "major_asset",
    "macro_linked_asset",
    "sports_full_board",
)

ALLOWED_MDP_ACTIONS = (
    "NO_REVIEW",
    "LOW_PRIORITY_REVIEW",
    "WATCHLIST_REVIEW",
    "ACTIVE_REVIEW",
    "DATA_INSUFFICIENT",
    "NO_BET",
    "NO_TRADE",
    "NO_TRADE_SESSION_LOCK",
)

FORBIDDEN_MDP_ACTIONS = (
    "BUY",
    "SELL",
    "SHORT",
    "PLACE_BET",
    "PLACE_ORDER",
    "EXECUTE",
    "SUBMIT_ORDER",
    "SUBMIT_WAGER",
    "SEND_TO_BROKER",
    "SEND_TO_SPORTSBOOK",
    "SEND_TO_EXCHANGE",
    "SEND_TO_KALSHI",
)


def _coverage_for(asset_type: str, outcome_coverage_by_asset_type: Mapping[str, Any] | None) -> float:
    payload = dict(outcome_coverage_by_asset_type or {})
    value = payload.get(asset_type)
    if isinstance(value, Mapping):
        value = value.get("outcome_coverage", value.get("coverage", 0.0))
    try:
        return round(float(value or 0.0), 6)
    except (TypeError, ValueError):
        return 0.0


def _required_sample(status: str, default: int) -> int:
    if status == "active_review":
        return max(0, int(default))
    if status == "active_calibration":
        return max(30, int(default))
    if status == "calibration_only":
        return max(100, int(default))
    if status.startswith("blocked"):
        return max(100, int(default))
    return max(0, int(default))


def _model(
    *,
    model_family: str,
    model_name: str,
    asset_type: str = "cross_asset",
    market_type: str = "*",
    model_maturity_status: str,
    data_requirement_level: str,
    compute_requirement_level: str,
    interpretability_score: float,
    current_sample_size: int = 0,
    required_sample_size: int = 0,
    outcome_coverage: float = 0.0,
    calibration_status: str = "not_started",
    blocked_reason: str | None = None,
    affects_review_queue: bool = False,
) -> dict[str, Any]:
    status = model_maturity_status if model_maturity_status in MODEL_MATURITY_STATUSES else "blocked_safety_review"
    required = _required_sample(status, required_sample_size)
    current = max(0, int(current_sample_size or 0))
    insufficient = current < required
    if status in {"active_review", "active_calibration"} and insufficient and required > 0:
        status = "blocked_insufficient_data"
        blocked_reason = blocked_reason or "insufficient_labeled_outcomes"
    research_only = status == "research_only"
    record = {
        "model_family": model_family,
        "model_name": model_name,
        "asset_type": asset_type,
        "market_type": market_type,
        "model_maturity_status": status,
        "data_requirement_level": data_requirement_level,
        "compute_requirement_level": compute_requirement_level,
        "interpretability_score": float(interpretability_score),
        "current_sample_size": current,
        "required_sample_size": required,
        "outcome_coverage": round(float(outcome_coverage or 0.0), 6),
        "calibration_status": calibration_status,
        "insufficient_sample": bool(insufficient),
        "blocked_reason": blocked_reason,
        "research_only": research_only,
        "affects_review_queue": bool(affects_review_queue and not research_only and status == "active_review"),
        "affects_execution": False,
    }
    record.update(locked_safety_flags())
    record["provider_write"] = False
    record["execution_allowed"] = False
    record["live_execution_enabled"] = False
    record["human_approval_required"] = True
    return record


def normalize_model_maturity_record(record: Mapping[str, Any]) -> dict[str, Any]:
    row = dict(record)
    status = str(row.get("model_maturity_status") or row.get("status") or "blocked_safety_review")
    row["model_maturity_status"] = status if status in MODEL_MATURITY_STATUSES else "blocked_safety_review"
    row["research_only"] = bool(row.get("research_only", row["model_maturity_status"] == "research_only"))
    if row["research_only"] or row["model_maturity_status"] in {"research_only", "disabled"}:
        row["affects_review_queue"] = False
    elif row["model_maturity_status"] != "active_review":
        row["affects_review_queue"] = False
    else:
        row["affects_review_queue"] = bool(row.get("affects_review_queue", False))
    row["affects_execution"] = False
    row["provider_write"] = False
    row["execution_allowed"] = False
    row["live_execution_enabled"] = False
    row["human_approval_required"] = True
    for key, value in locked_safety_flags().items():
        if key in {
            "provider_write",
            "execution_allowed",
            "live_execution_enabled",
            "auto_execution",
            "auto_execution_enabled",
            "human_approval_required",
            "owner_approval_required",
            "raw_payload_included",
            "secrets_included",
        }:
            row[key] = value
    return row


def build_core_model_maturity_records(
    *,
    total_labeled_outcomes: int = 0,
    outcome_coverage_by_asset_type: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    total = max(0, int(total_labeled_outcomes or 0))
    cross_asset_coverage = round(min(1.0, total / 1000.0), 6)
    records = [
        _model(
            model_family="deterministic_rule_scoring",
            model_name="Deterministic Rule Scoring",
            model_maturity_status="active_review",
            data_requirement_level="low",
            compute_requirement_level="low",
            interpretability_score=95,
            required_sample_size=0,
            current_sample_size=total,
            outcome_coverage=cross_asset_coverage,
            calibration_status="rules_active_calibration_pending",
            affects_review_queue=True,
        ),
        _model(
            model_family="representation_vectors",
            model_name="Deterministic Cross-Asset Representation Vectors",
            model_maturity_status="active_review",
            data_requirement_level="low",
            compute_requirement_level="low",
            interpretability_score=90,
            required_sample_size=0,
            current_sample_size=total,
            outcome_coverage=cross_asset_coverage,
            calibration_status="feature_normalization_active",
            affects_review_queue=True,
        ),
        _model(
            model_family="manifold_nearest_neighbor",
            model_name="Manifold Nearest-Neighbor Market-State Mapping",
            model_maturity_status="active_calibration" if total < 30 else "active_review",
            data_requirement_level="medium",
            compute_requirement_level="low",
            interpretability_score=82,
            required_sample_size=30,
            current_sample_size=total,
            outcome_coverage=cross_asset_coverage,
            calibration_status="insufficient_data" if total < 30 else "partial_calibration",
            blocked_reason="needs_cluster_labeled_outcomes" if total < 30 else None,
            affects_review_queue=total >= 30,
        ),
        _model(
            model_family="graph_relationship_mapping",
            model_name="Compact Graph-Style Relationship Mapping",
            model_maturity_status="active_review",
            data_requirement_level="low",
            compute_requirement_level="low",
            interpretability_score=92,
            required_sample_size=0,
            current_sample_size=total,
            outcome_coverage=cross_asset_coverage,
            calibration_status="relationship_catalog_active",
            affects_review_queue=True,
        ),
        _model(
            model_family="markov_chain",
            model_name="Markov Chain State Transition Diagnostics",
            model_maturity_status="active_calibration" if total >= 100 else "blocked_insufficient_data",
            data_requirement_level="medium",
            compute_requirement_level="low",
            interpretability_score=78,
            required_sample_size=100,
            current_sample_size=total,
            outcome_coverage=cross_asset_coverage,
            calibration_status="transition_counts_pending" if total < 100 else "transition_counts_ready",
            blocked_reason="needs_ordered_labeled_state_transitions" if total < 100 else None,
        ),
        _model(
            model_family="hidden_markov_model",
            model_name="HMM Regime Diagnostics",
            model_maturity_status="active_calibration" if total >= 300 else "blocked_insufficient_data",
            data_requirement_level="high",
            compute_requirement_level="medium",
            interpretability_score=62,
            required_sample_size=300,
            current_sample_size=total,
            outcome_coverage=cross_asset_coverage,
            calibration_status="hidden_state_calibration_pending" if total < 300 else "calibration_ready",
            blocked_reason="needs_labeled_regime_sequences" if total < 300 else None,
        ),
        _model(
            model_family="monte_carlo_risk_simulation",
            model_name="Deterministic Monte Carlo-Style Risk Scenarios",
            model_maturity_status="active_calibration" if total >= 50 else "blocked_insufficient_data",
            data_requirement_level="medium",
            compute_requirement_level="low",
            interpretability_score=80,
            required_sample_size=50,
            current_sample_size=total,
            outcome_coverage=cross_asset_coverage,
            calibration_status="scenario_assumptions_pending" if total < 50 else "scenario_calibration_ready",
            blocked_reason="needs_labeled_return_or_hit_rate_history" if total < 50 else None,
        ),
        _model(
            model_family="calibration_outcome_tracking",
            model_name="Calibration and Outcome Tracking",
            model_maturity_status="active_calibration",
            data_requirement_level="low",
            compute_requirement_level="low",
            interpretability_score=94,
            required_sample_size=0,
            current_sample_size=total,
            outcome_coverage=cross_asset_coverage,
            calibration_status="tracking_active",
        ),
        _model(
            model_family="out_of_distribution_detection",
            model_name="Out-of-Distribution and Trap Detection",
            model_maturity_status="active_review",
            data_requirement_level="low",
            compute_requirement_level="low",
            interpretability_score=88,
            required_sample_size=0,
            current_sample_size=total,
            outcome_coverage=cross_asset_coverage,
            calibration_status="rule_guard_active",
            affects_review_queue=True,
        ),
        _model(
            model_family="causal_effect_testing",
            model_name="Causal Effect Testing Scaffold",
            model_maturity_status="calibration_only",
            data_requirement_level="high",
            compute_requirement_level="low",
            interpretability_score=86,
            required_sample_size=200,
            current_sample_size=total,
            outcome_coverage=cross_asset_coverage,
            calibration_status="not_ready",
            blocked_reason="causal_claims_blocked_until_design_and_confounders_pass",
        ),
    ]
    for asset_type in ("prediction_market", "sportsbook", "stock", "crypto", "bond_rate"):
        records.append(
            _model(
                model_family=f"{asset_type}_calibration_bucket",
                model_name=f"{asset_type.replace('_', ' ').title()} Calibration Bucket",
                asset_type=asset_type,
                market_type=asset_type,
                model_maturity_status="active_calibration",
                data_requirement_level="medium",
                compute_requirement_level="low",
                interpretability_score=90,
                required_sample_size=30,
                current_sample_size=total,
                outcome_coverage=_coverage_for(asset_type, outcome_coverage_by_asset_type),
                calibration_status="partial" if _coverage_for(asset_type, outcome_coverage_by_asset_type) > 0 else "insufficient_data",
            )
        )
    return [normalize_model_maturity_record(row) for row in records]


def validate_mdp_action_space(actions: list[str] | tuple[str, ...] | None) -> dict[str, Any]:
    requested = [str(action or "").strip().upper() for action in (actions or [])]
    accepted = [action for action in requested if action in ALLOWED_MDP_ACTIONS]
    rejected = [action for action in requested if action in FORBIDDEN_MDP_ACTIONS or action not in ALLOWED_MDP_ACTIONS]
    return {
        "accepted_actions": sorted(set(accepted), key=accepted.index),
        "rejected_actions": sorted(set(rejected), key=rejected.index),
        "forbidden_actions_rejected": [action for action in sorted(set(rejected), key=rejected.index) if action in FORBIDDEN_MDP_ACTIONS],
        **locked_safety_flags(),
    }


def build_mdp_review_policy_scaffold(
    *,
    current_sample_size: int = 0,
    allowed_actions: list[str] | None = None,
    forbidden_actions: list[str] | None = None,
) -> dict[str, Any]:
    sample = max(0, int(current_sample_size or 0))
    requested_allowed = allowed_actions if allowed_actions is not None else list(ALLOWED_MDP_ACTIONS)
    validation = validate_mdp_action_space(requested_allowed)
    rejected_forbidden = validate_mdp_action_space(forbidden_actions or list(FORBIDDEN_MDP_ACTIONS))
    status = "calibration_only" if sample >= 500 else "blocked_insufficient_data"
    safety_blockers = ["execution_actions_forbidden", "provider_write_disabled", "human_approval_required"]
    if sample < 500:
        safety_blockers.append("insufficient_labeled_review_outcomes")
    payload = {
        "state_space_version": "review_state_space_v1",
        "action_space_version": "review_only_actions_v1",
        "reward_definition": "review quality calibration only; no order, wager, trade, or execution reward",
        "review_policy_status": status,
        "allowed_actions": validation["accepted_actions"],
        "forbidden_actions_rejected": sorted(set(validation["forbidden_actions_rejected"] + rejected_forbidden["forbidden_actions_rejected"])),
        "insufficient_sample": sample < 500,
        "safety_blockers": safety_blockers,
        "current_sample_size": sample,
        "required_sample_size": 500,
        "model_family": "mdp_review_policy",
        "model_name": "MDP Review-Policy Optimization Scaffold",
        "model_maturity_status": status,
        "research_only": False,
        "affects_review_queue": False,
        "affects_execution": False,
    }
    payload.update(locked_safety_flags())
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
    return payload


def summarize_maturity_registry(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    normalized = [normalize_model_maturity_record(row) for row in records]
    counts = Counter(str(row.get("model_maturity_status") or "unknown") for row in normalized)
    return {
        "total_models": len(normalized),
        "status_counts": dict(sorted(counts.items())),
        "active_review_count": counts.get("active_review", 0),
        "active_calibration_count": counts.get("active_calibration", 0),
        "calibration_only_count": counts.get("calibration_only", 0),
        "research_only_count": counts.get("research_only", 0),
        "blocked_count": sum(count for status, count in counts.items() if str(status).startswith("blocked")),
        "execution_allowed_count": 0,
        "provider_write_enabled_count": 0,
    }


def build_model_maturity_registry(
    *,
    total_labeled_outcomes: int = 0,
    outcome_coverage_by_asset_type: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    from src.research import build_deep_learning_maturity_records, build_tabular_maturity_records

    records = build_core_model_maturity_records(
        total_labeled_outcomes=total_labeled_outcomes,
        outcome_coverage_by_asset_type=outcome_coverage_by_asset_type,
    )
    records.extend(
        build_tabular_maturity_records(
            total_labeled_outcomes=total_labeled_outcomes,
            outcome_coverage_by_asset_type=outcome_coverage_by_asset_type,
        )
    )
    records.extend(build_deep_learning_maturity_records())
    records.append(
        normalize_model_maturity_record(
            {
                **build_mdp_review_policy_scaffold(current_sample_size=total_labeled_outcomes),
                "asset_type": "cross_asset",
                "market_type": "review_policy",
                "data_requirement_level": "high",
                "compute_requirement_level": "low",
                "interpretability_score": 70,
                "outcome_coverage": round(min(1.0, max(0, int(total_labeled_outcomes or 0)) / 1000.0), 6),
                "calibration_status": "not_ready" if int(total_labeled_outcomes or 0) < 500 else "calibration_ready",
                "blocked_reason": "needs_500_labeled_review_outcomes" if int(total_labeled_outcomes or 0) < 500 else None,
            }
        )
    )
    normalized = [normalize_model_maturity_record(row) for row in records]
    summary = summarize_maturity_registry(normalized)
    payload = {
        "ok": True,
        "status": "model_maturity_registry",
        "schema_version": "model_maturity_registry_v1",
        **summary,
        "models": sorted(normalized, key=lambda row: (str(row.get("model_maturity_status")), str(row.get("model_family")))),
    }
    payload.update(locked_safety_flags())
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
    return payload


def get_model_maturity_registry(
    *,
    total_labeled_outcomes: int = 0,
    outcome_coverage_by_asset_type: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return build_model_maturity_registry(
        total_labeled_outcomes=total_labeled_outcomes,
        outcome_coverage_by_asset_type=outcome_coverage_by_asset_type,
    )

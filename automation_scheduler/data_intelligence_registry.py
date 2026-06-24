from __future__ import annotations

from typing import Any, Mapping

from .security_policy import locked_safety_flags
from src.research import build_mdp_review_policy_scaffold, build_model_maturity_registry


DATA_INTELLIGENCE_SCHEMA_VERSION = "cross_asset_data_intelligence_registry_v1"

SUPPORTED_DOMAINS = (
    "prediction_markets",
    "sportsbooks",
    "stocks",
    "crypto",
    "ETFs",
    "bonds_rates",
    "major_assets",
    "macro_linked_assets",
    "sports_full_board_analysis",
)

BUILD_NOW_LAYERS = (
    "deterministic_rule_scoring",
    "feature_normalization",
    "deterministic_representation_vectors",
    "nearest_neighbor_lookup",
    "manifold_cluster_mapping",
    "markov_chain_state_diagnostics",
    "hmm_state_modeling_scaffold",
    "monte_carlo_risk_simulation_scaffold",
    "graph_relationship_mapping",
    "calibration_outcome_tracking",
    "out_of_distribution_detection",
    "no_bet_no_trade_trap_detection",
)

BUILD_LATER_LAYERS = (
    "xgboost",
    "lightgbm",
    "tabular_foundation_model_research",
    "mdp_review_policy_optimization",
    "causal_effect_testing",
)

RESEARCH_ONLY_LAYERS = (
    "lstm",
    "transformer_models",
    "deep_manifold_learning",
    "autoencoders",
    "full_graph_neural_networks",
    "graph_neural_networks",
    "deep_metric_learning",
)

STRICT_SAFETY_GATES = {
    "provider_write": False,
    "execution_allowed": False,
    "live_execution_enabled": False,
    "auto_execution": False,
    "human_approval_required": True,
    "owner_approval_required": True,
    "no_real_orders": True,
    "no_real_trades": True,
    "no_real_bets": True,
    "no_raw_payload_exposure": True,
    "no_auth_signature_api_key_secret_exposure": True,
    "compact_responses_only": True,
}


def build_data_intelligence_registry(
    *,
    total_labeled_outcomes: int = 0,
    outcome_coverage_by_asset_type: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    maturity = build_model_maturity_registry(
        total_labeled_outcomes=total_labeled_outcomes,
        outcome_coverage_by_asset_type=outcome_coverage_by_asset_type,
    )
    mdp = build_mdp_review_policy_scaffold(current_sample_size=total_labeled_outcomes)
    payload = {
        "ok": True,
        "status": "data_intelligence_registry",
        "schema_version": DATA_INTELLIGENCE_SCHEMA_VERSION,
        "major_lesson": "Modern market data intelligence is a hybrid stack, not one model.",
        "supported_domains": list(SUPPORTED_DOMAINS),
        "build_now": list(BUILD_NOW_LAYERS),
        "build_later": list(BUILD_LATER_LAYERS),
        "research_only": list(RESEARCH_ONLY_LAYERS),
        "active_review_models": maturity.get("active_review_count", 0),
        "active_calibration_models": maturity.get("active_calibration_count", 0),
        "calibration_only_models": maturity.get("calibration_only_count", 0),
        "research_only_models": maturity.get("research_only_count", 0),
        "blocked_models": maturity.get("blocked_count", 0),
        "total_labeled_outcomes": int(total_labeled_outcomes or 0),
        "outcome_coverage_by_asset_type": dict(outcome_coverage_by_asset_type or {}),
        "model_maturity_registry": maturity,
        "mdp_review_policy_scaffold": mdp,
        "strict_safety_gates": dict(STRICT_SAFETY_GATES),
        "provider_write_enabled_count": 0,
        "execution_allowed_count": 0,
        "raw_payload_included": False,
        "secrets_included": False,
    }
    payload.update(locked_safety_flags())
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
    return payload

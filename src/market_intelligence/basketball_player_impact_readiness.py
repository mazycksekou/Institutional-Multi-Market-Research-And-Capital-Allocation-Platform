from __future__ import annotations

from typing import Any

from .basketball_player_impact_common import SUPPORTED_BASKETBALL_SPORTS, SPORT_CONTRACTS, finalize_safe_response


FEASIBLE_NOW = [
    "possession_level_impact",
    "tracking_derived_opportunity",
    "role_adjusted_usage_efficiency",
    "lineup_matchup_context",
    "availability_minutes_reliability",
    "incentive_contract_behavior_modifiers",
    "market_specific_prop_spread_total_relevance",
    "market_specific_calibration",
    "read_only_red_team_review",
]

NOT_IMPLEMENTED = [
    "graph_neural_networks",
    "counterfactual_causal_gans",
    "rl_micro_action_decision_quality",
    "multimodal_foundation_models",
]


def build_basketball_player_impact_readiness(*, base_data_dir: str | None = None) -> dict[str, Any]:
    contracts = {
        sport: {
            "league": contract["league"],
            "sport_contract_id": contract["sport_contract_id"],
            "calibration_bucket_prefix": contract["calibration_bucket_prefix"],
            "contract_context": contract["contract_context"],
            "screenshot_analysis_parity_key": contract["screenshot_analysis_parity_key"],
        }
        for sport, contract in SPORT_CONTRACTS.items()
    }
    payload = {
        "ok": True,
        "status": "basketball_player_impact_readiness",
        "supported_sports": list(SUPPORTED_BASKETBALL_SPORTS),
        "sport_contracts": contracts,
        "feasible_now": FEASIBLE_NOW,
        "not_implemented": NOT_IMPLEMENTED,
        "possession_impact_ready": True,
        "tracking_opportunity_ready": True,
        "role_context_ready": True,
        "lineup_matchup_ready": True,
        "availability_minutes_ready": True,
        "incentive_context_ready": True,
        "market_relevance_ready": True,
        "calibration_ready": True,
        "red_team_ready": True,
        "base_data_dir_configured": bool(base_data_dir),
        "next_required_data": [
            "possession_level_logs",
            "tracking_opportunity_summaries",
            "projected_lineups",
            "minutes_outcomes",
            "settled_market_outcomes",
            "closing_line_value",
        ],
    }
    return finalize_safe_response(payload, source_payload=payload)

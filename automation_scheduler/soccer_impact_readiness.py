from __future__ import annotations

from .soccer_data_availability import FIELD_GROUPS
from .soccer_impact_common import DATA_TIER_REQUIREMENTS, SUPPORTED_SOCCER_MARKETS, SUPPORTED_SOCCER_ROLES, SUPPORTED_SOCCER_SPORTS, finalize_soccer_response


def build_soccer_impact_readiness() -> dict:
    return finalize_soccer_response(
        {
            "ok": True,
            "status": "soccer_impact_readiness",
            "supported_sports": list(SUPPORTED_SOCCER_SPORTS),
            "supported_roles": list(SUPPORTED_SOCCER_ROLES),
            "supported_markets": list(SUPPORTED_SOCCER_MARKETS),
            "data_tier_requirements": DATA_TIER_REQUIREMENTS,
            "field_groups": {key: list(value) for key, value in FIELD_GROUPS.items()},
            "soccer_readiness": {
                "status": "foundation_ready_read_only",
                "minimum_useful_tier": 1,
                "shot_xg_tier": 2,
                "possession_value_player_role_tier": 3,
                "tracking_optional_tier": 4,
                "provider_write": False,
                "execution_allowed": False,
            },
            "missing_data_by_market": {
                "team_markets": ["xg_context", "lineup_status", "goalkeeper_confirmation", "settled_team_market_outcomes"],
                "totals_btts": ["both_teams_xg", "transition_context", "goalkeeper_context", "referee_penalty_red_card_context"],
                "player_props": ["confirmed_lineup", "player_role_context", "minutes_projection", "settled_player_prop_outcomes"],
                "correct_score": ["large_calibration_sample", "goalkeeper_quality", "red_card_volatility", "xg_distribution"],
            },
            "calibration_requirements": [
                "settled_outcomes_by_market_lineup_goalkeeper_tactical_referee_bucket",
                "closing_prices_for_clv",
                "realized_returns_only_when_available",
                "extra_large_correct_score_sample",
            ],
            "no_spend_policy": {
                "paid_provider_required": False,
                "new_api_keys_required": False,
                "tracking_optional": True,
                "external_provider_calls_in_tests": False,
            },
            "forbidden_features": [
                "live_execution",
                "provider_write",
                "paid_provider_required",
                "fabricated_xg",
                "fabricated_xt",
                "fabricated_obv_vaep",
                "fabricated_tracking",
                "fabricated_pitch_control",
                "fabricated_formation",
                "fabricated_lineup",
                "fabricated_goalkeeper_confirmation",
                "fabricated_referee_tendency",
                "fabricated_penalty_taker",
                "fabricated_calibration",
                "automatic_betting",
            ],
        }
    )

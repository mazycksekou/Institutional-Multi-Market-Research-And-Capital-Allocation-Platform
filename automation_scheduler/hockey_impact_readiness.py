from __future__ import annotations

from .hockey_data_availability import FIELD_GROUPS
from .hockey_impact_common import (
    DATA_TIER_REQUIREMENTS,
    SUPPORTED_HOCKEY_MARKETS,
    SUPPORTED_HOCKEY_ROLES,
    SUPPORTED_HOCKEY_SPORTS,
    finalize_hockey_response,
)


def build_hockey_impact_readiness() -> dict:
    return finalize_hockey_response(
        {
            "ok": True,
            "status": "hockey_impact_readiness",
            "supported_sports": list(SUPPORTED_HOCKEY_SPORTS),
            "supported_roles": list(SUPPORTED_HOCKEY_ROLES),
            "supported_markets": list(SUPPORTED_HOCKEY_MARKETS),
            "data_tier_requirements": DATA_TIER_REQUIREMENTS,
            "field_groups": {key: list(value) for key, value in FIELD_GROUPS.items()},
            "nhl_readiness": {
                "status": "foundation_ready_read_only",
                "minimum_useful_tier": 1,
                "shot_possession_tier": 2,
                "xg_line_goalie_tier": 3,
                "tracking_optional_tier": 4,
                "provider_write": False,
                "execution_allowed": False,
            },
            "missing_data_by_market": {
                "skater_props": ["confirmed_lines", "skater_role_context", "individual_xg_or_shot_volume", "settled_prop_outcomes"],
                "goalie_props": ["confirmed_goalie", "shot_quality_adjusted_goalie_context", "opponent_volume", "settled_goalie_prop_outcomes"],
                "team_markets": ["goalie_confirmation", "xg_share", "special_teams_context", "line_pair_injuries", "settled_team_market_outcomes"],
                "first_period_markets": ["first_period_shot_rate", "first_period_xg_rate", "starting_goalie", "settled_first_period_outcomes"],
            },
            "calibration_requirements": [
                "settled_outcomes_by_market_role_goalie_status_rest_line_stability",
                "closing_prices_for_clv",
                "realized_returns_only_when_available",
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
                "fabricated_tracking",
                "fabricated_zone_entries",
                "fabricated_zone_exits",
                "fabricated_gsax",
                "fabricated_lines",
                "fabricated_goalie_confirmation",
                "fabricated_calibration",
                "automatic_betting",
            ],
        }
    )

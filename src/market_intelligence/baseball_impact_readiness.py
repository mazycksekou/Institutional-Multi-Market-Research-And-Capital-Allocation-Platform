from __future__ import annotations

from typing import Any

from .baseball_data_availability import FIELD_GROUPS
from .baseball_impact_common import DATA_TIER_REQUIREMENTS, SUPPORTED_BASEBALL_MARKETS, SUPPORTED_BASEBALL_ROLES, SUPPORTED_BASEBALL_SPORTS, finalize_baseball_response


def build_baseball_impact_readiness() -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": True,
        "status": "baseball_impact_readiness",
        "supported_sports": list(SUPPORTED_BASEBALL_SPORTS),
        "supported_roles": list(SUPPORTED_BASEBALL_ROLES),
        "supported_markets": list(SUPPORTED_BASEBALL_MARKETS),
        "data_tier_requirements": DATA_TIER_REQUIREMENTS,
        "field_groups": {key: list(value) for key, value in FIELD_GROUPS.items()},
        "mlb_readiness": {
            "status": "foundation_ready",
            "minimum_useful_tier": 1,
            "player_prop_useful_tier": 2,
            "pitch_contact_useful_tier": 3,
            "advanced_tracking_optional_tier": 4,
        },
        "missing_data_by_market": {
            "pitcher_strikeouts": ["pitcher_k_rate", "whiff_rate", "opponent_k_rate", "pitch_count_limit", "umpire_zone_if_available"],
            "pitcher_outs_recorded": ["confirmed_starter", "pitch_count_limit", "recent_pitch_count", "weather_delay_risk"],
            "batter_hits": ["confirmed_lineup", "lineup_slot", "contact_quality", "platoon_split"],
            "batter_home_runs": ["barrel_rate", "xslg", "pitcher_hr_risk", "park_weather"],
            "stolen_bases": ["runner_attempt_rate", "pitcher_hold", "catcher_pop_time"],
            "totals": ["park_factor", "weather", "roof_status", "umpire_tendency_if_available", "bullpen_context"],
        },
        "calibration_requirements": [
            "bucketed_by_sport_market_role_data_tier_pitcher_batter_park_weather_umpire_lineup_bullpen",
            "real_settled_outcomes_required",
            "open_close_prices_required_for_clv_proxy",
            "realized_returns_required_for_roi_proxy",
        ],
        "no_spend_policy": {
            "paid_provider_required": False,
            "new_provider_calls_added": False,
            "mandatory_api_key_required": False,
            "heavy_ml_training_added": False,
        },
        "forbidden_features": [
            "live_execution",
            "provider_write",
            "paid_provider_required",
            "fabricated_statcast",
            "fabricated_pitch_tracking",
            "fabricated_bat_tracking",
            "fabricated_umpire_tendency",
            "fabricated_calibration",
            "automatic_betting",
        ],
    }
    return finalize_baseball_response(payload, source_payload=payload)

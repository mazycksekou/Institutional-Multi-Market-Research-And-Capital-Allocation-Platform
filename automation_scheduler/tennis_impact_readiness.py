from __future__ import annotations

from typing import Any

from .tennis_impact_common import DATA_TIER_REQUIREMENTS, SUPPORTED_TENNIS_CONTEXTS, SUPPORTED_TENNIS_MARKETS, SUPPORTED_TENNIS_SPORTS, finalize_tennis_response


def build_tennis_impact_readiness() -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ok": True,
        "status": "tennis_impact_readiness",
        "supported_sports": list(SUPPORTED_TENNIS_SPORTS),
        "supported_markets": list(SUPPORTED_TENNIS_MARKETS),
        "supported_contexts": list(SUPPORTED_TENNIS_CONTEXTS),
        "data_tier_requirements": DATA_TIER_REQUIREMENTS,
        "tennis_readiness": {
            "status": "foundation_ready",
            "minimum_useful_tier": 1,
            "serve_return_useful_tier": 2,
            "surface_pressure_useful_tier": 3,
            "tracking_shot_pattern_optional_tier": 4,
        },
        "atp_readiness": {
            "status": "supported_when_payload_fields_exist",
            "best_of_five_supported": True,
            "point_tracking_required": False,
        },
        "wta_readiness": {
            "status": "supported_when_payload_fields_exist",
            "best_of_three_default_supported": True,
            "point_tracking_required": False,
        },
        "missing_data_by_market": {
            "moneyline": ["hold_break_differential", "surface_adjusted_serve_return", "injury_retirement_context", "calibration_outcomes"],
            "set_game_handicap": ["set_game_distribution", "serve_return_separation", "volatility_context", "best_of"],
            "total_games": ["hold_rates", "tiebreak_likelihood", "surface_speed", "retirement_risk"],
            "correct_score": ["set_distribution", "best_of", "retirement_risk", "large_calibration_sample"],
            "first_set": ["first_set_hold_break", "first_set_win_rate", "conditions_context"],
            "tiebreak": ["hold_rates", "ace_rates", "court_speed", "tiebreak_frequency", "surface"],
            "player_props": ["serve_return_stats", "opponent_context", "surface_conditions", "pressure_context"],
        },
        "calibration_requirements": [
            "bucketed_by_sport_tour_surface_market_data_tier_best_of",
            "real_settled_outcomes_required",
            "correct_score_requires_extra_sample",
            "tiebreak_markets_require_extra_sample",
            "open_close_prices_required_for_clv_proxy",
            "realized_returns_required_for_roi_proxy",
        ],
        "no_spend_policy": {
            "paid_provider_required": False,
            "new_provider_calls_added": False,
            "mandatory_api_key_required": False,
            "heavy_ml_training_added": False,
            "model_training_added": False,
        },
        "forbidden_features": [
            "live_execution",
            "provider_write",
            "paid_provider_required",
            "fabricated_serve_placement",
            "fabricated_serve_speed",
            "fabricated_return_position",
            "fabricated_shot_pattern",
            "fabricated_court_speed",
            "fabricated_ball_type",
            "fabricated_injury_status",
            "fabricated_retirement_risk",
            "fabricated_weather_conditions",
            "fabricated_calibration",
            "automatic_betting",
        ],
    }
    return finalize_tennis_response(payload)


def build_tennis_impact_readiness_report() -> dict[str, Any]:
    return build_tennis_impact_readiness()

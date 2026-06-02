from __future__ import annotations

from .golf_impact_common import DATA_TIER_REQUIREMENTS, SUPPORTED_GOLF_MARKETS, SUPPORTED_GOLF_SKILL_GROUPS, SUPPORTED_GOLF_SPORTS, finalize_golf_response


def build_golf_impact_readiness() -> dict:
    return finalize_golf_response(
        {
            "ok": True,
            "status": "golf_impact_readiness",
            "supported_sports": list(SUPPORTED_GOLF_SPORTS),
            "supported_skill_groups": list(SUPPORTED_GOLF_SKILL_GROUPS),
            "supported_markets": list(SUPPORTED_GOLF_MARKETS),
            "data_tier_requirements": DATA_TIER_REQUIREMENTS,
            "golf_readiness": {
                "status": "foundation_ready",
                "minimum_useful_tier": 1,
                "strokes_gained_useful_tier": 2,
                "course_weather_field_useful_tier": 3,
                "shot_level_simulation_optional_tier": 4,
                "pga_supported": True,
                "lpga_supported_when_payload_fields_exist": True,
            },
            "missing_data_by_market": {
                "outright_winner": ["sg_total", "sg_tee_to_green", "course_fit", "field_strength", "calibration_outcomes"],
                "top_finish": ["sg_total", "course_fit", "field_strength", "cut_risk", "volatility_bucket"],
                "make_cut": ["sg_tee_to_green", "bogey_avoidance", "cut_rate", "cut_rule", "injury_withdrawal_status"],
                "tournament_matchup": ["relative_sg_profile", "course_fit_differential", "weather_wave", "fatigue_context"],
                "first_round_leader": ["round_1_scoring", "tee_time_wave", "weather_by_wave", "putting_volatility"],
                "round_score": ["scoring_average", "course_difficulty", "weather", "tee_time"],
                "player_props": ["off_tee", "approach", "putting", "course_architecture", "weather"],
            },
            "calibration_requirements": [
                "bucketed_by_sport_market_data_tier_skill_group_course_weather_field_cut_volatility",
                "real_settled_outcomes_required",
                "outright_markets_require_extra_sample",
                "placement_markets_bucketed_separately",
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
                "fabricated_strokes_gained",
                "fabricated_course_fit",
                "fabricated_tee_time_wave",
                "fabricated_weather_wave",
                "fabricated_grass_fit",
                "fabricated_injury_status",
                "fabricated_field_strength",
                "fabricated_calibration",
                "automatic_betting",
            ],
        },
        source_payload={},
    )

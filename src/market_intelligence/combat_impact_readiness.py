from __future__ import annotations

from .combat_impact_common import DATA_TIER_REQUIREMENTS, SUPPORTED_COMBAT_MARKETS, SUPPORTED_COMBAT_PHASES, SUPPORTED_COMBAT_SPORTS, finalize_combat_response


def build_combat_impact_readiness() -> dict:
    return finalize_combat_response(
        {
            "ok": True,
            "status": "combat_impact_readiness",
            "supported_sports": list(SUPPORTED_COMBAT_SPORTS),
            "supported_markets": list(SUPPORTED_COMBAT_MARKETS),
            "supported_phases": list(SUPPORTED_COMBAT_PHASES),
            "data_tier_requirements": DATA_TIER_REQUIREMENTS,
            "mma_readiness": {
                "status": "foundation_ready_read_only",
                "minimum_useful_tier": 1,
                "summary_striking_grappling_tier": 2,
                "phase_round_damage_tier": 3,
                "film_camp_judging_optional_tier": 4,
                "provider_write": False,
                "execution_allowed": False,
            },
            "ufc_readiness": {
                "status": "foundation_ready_read_only",
                "ruleset": "mma",
                "five_round_context_supported_when_supplied": True,
                "provider_write": False,
                "execution_allowed": False,
            },
            "boxing_readiness": {
                "status": "foundation_ready_read_only",
                "punch_profile_supported_when_supplied": True,
                "ruleset_separated_from_mma": True,
                "provider_write": False,
                "execution_allowed": False,
            },
            "missing_data_by_market": {
                "moneyline": ["fighter_identity", "summary_striking_grappling", "settled_moneyline_outcomes"],
                "method_markets": ["finish_path_outcomes", "durability_context", "submission_control_context"],
                "round_total_markets": ["round_level_pace_damage", "cardio_decline_context", "finish_timing_outcomes"],
                "fighter_props": ["round_duration_projection", "phase_control_context", "opponent_suppression_context"],
                "boxing_props": ["jab_power_punch_tracking", "round_projection", "settled_boxing_prop_outcomes"],
            },
            "calibration_requirements": [
                "settled_outcomes_by_ruleset_market_weight_class_round_context",
                "closing_prices_for_clv",
                "realized_returns_only_when_available",
                "extra_large_exact_round_split_decision_samples",
            ],
            "no_spend_policy": {
                "paid_provider_required": False,
                "new_api_keys_required": False,
                "film_tracking_optional": True,
                "external_provider_calls_in_tests": False,
            },
            "forbidden_features": [
                "live_execution",
                "provider_write",
                "paid_provider_required",
                "fabricated_phase_control",
                "fabricated_punch_tracking",
                "fabricated_grappling_control",
                "fabricated_durability",
                "fabricated_chin",
                "fabricated_injury_status",
                "fabricated_weight_cut",
                "fabricated_camp_context",
                "fabricated_referee_tendency",
                "fabricated_judge_tendency",
                "fabricated_calibration",
                "automatic_betting",
            ],
        }
    )

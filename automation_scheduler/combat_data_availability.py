from __future__ import annotations

from typing import Any

from .combat_impact_common import DATA_TIER_REQUIREMENTS, compact_list, finalize_combat_response, normalize_combat_sport, present_fields


FIELD_GROUPS: dict[str, tuple[str, ...]] = {
    "basic_bout_context": ("organization", "bout_id", "event_id", "weight_class", "scheduled_rounds", "ruleset"),
    "fighter_identity_context": ("fighter_id", "fighter_name", "fighter_a_fighter_id", "fighter_a_fighter_name", "fighter_b_fighter_id", "fighter_b_fighter_name"),
    "sport_ruleset_context": ("sport", "ruleset", "organization", "cage_or_ring", "glove_size"),
    "weight_class_context": ("weight_class", "catchweight_context", "moved_weight_class"),
    "scheduled_rounds_context": ("scheduled_rounds", "title_fight", "main_event"),
    "stance_reach_context": ("stance", "fighter_a_stance", "fighter_b_stance", "reach_inches", "fighter_a_reach_inches", "fighter_b_reach_inches", "height_inches"),
    "basic_record_context": ("wins", "losses", "draws", "fighter_a_wins", "fighter_b_wins", "recent_wins", "recent_losses"),
    "finish_history_context": ("finish_rate", "decision_rate", "ko_wins", "submission_wins", "ko_losses", "submission_losses"),
    "striking_summary_context": ("significant_strikes_landed_per_minute", "fighter_a_significant_strikes_landed_per_minute", "fighter_b_significant_strikes_landed_per_minute", "striking_accuracy", "striking_defense"),
    "grappling_summary_context": ("takedowns_per_15", "fighter_a_takedowns_per_15", "fighter_b_takedowns_per_15", "control_time_average", "submission_attempts_per_15"),
    "takedown_context": ("takedowns_per_15", "takedown_accuracy", "takedown_defense", "takedown_attempts_per_15"),
    "submission_context": ("submission_attempts_per_15", "submission_attempt_quality", "submission_defense", "back_take_rate"),
    "knockdown_context": ("knockdown_average", "knockdowns_landed", "knockdowns_absorbed", "fighter_a_knockdown_average"),
    "pace_context": ("average_fight_time", "first_round_pace", "late_round_striking_pace", "cardio_rating_proxy"),
    "round_level_context": ("round_by_round_pace", "first_round_pace", "second_round_pace", "third_round_pace", "output_decline_by_round", "knockdowns_by_round"),
    "opponent_adjusted_context": ("opponent_adjusted_striking_score", "opponent_adjusted_grappling_score", "opponent_adjusted_phase_score"),
    "phase_control_context": ("open_space_striking_control", "pocket_boxing_control", "clinch_control", "cage_wrestling_control", "top_control_success"),
    "clinch_cage_context": ("clinch_control", "cage_control_rate", "cage_wrestling_control", "mat_return_rate"),
    "ground_control_context": ("top_control_time", "bottom_time", "top_control_success", "ground_and_pound_control"),
    "scramble_context": ("scramble_success_rate", "get_up_rate", "guard_retention_rate"),
    "damage_durability_context": ("knockdowns_absorbed", "head_strike_absorption_rate", "cut_history", "stun_or_wobble_history", "recent_damage_taken"),
    "cardio_decline_context": ("output_decline_by_round", "defensive_decline_by_round", "takedown_defense_decline", "striking_defense_decline"),
    "weight_cut_context": ("weight_cut_severity", "missed_weight_history", "weigh_in_status", "rehydration_context"),
    "injury_medical_context": ("injury_status", "medical_suspension_context", "illness_context", "last_fight_damage_context"),
    "camp_context": ("camp_length", "camp_change_context", "team_change_context", "training_camp_length"),
    "judging_context": ("judge_names", "judging_variance_proxy", "split_decision_rate_proxy", "open_scoring_context"),
    "referee_context": ("referee_name", "referee_stoppage_tendency", "referee_standup_tendency", "referee_point_deduction_tendency"),
    "betting_market_context": ("market_type", "odds", "moneyline", "method_of_victory"),
    "calibration_outcomes": ("historical_predictions", "settled_outcomes", "matched_outcomes_count", "final_outcome", "outcome"),
    "film_tracking_context": ("film_tracking_available", "lead_hand_control", "calf_kick_vulnerability", "punch_tracking_available", "biomechanical_context", "medical_context"),
}


def _merge(*contexts: dict[str, Any] | None) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for context in contexts:
        if isinstance(context, dict):
            row.update(context)
    return row


def evaluate_combat_data_availability(
    sport: Any = "combat_sports",
    *,
    market_type: Any = None,
    bout_context: dict[str, Any] | None = None,
    fighter_a_context: dict[str, Any] | None = None,
    fighter_b_context: dict[str, Any] | None = None,
    striking_context: dict[str, Any] | None = None,
    grappling_context: dict[str, Any] | None = None,
    phase_context: dict[str, Any] | None = None,
    damage_context: dict[str, Any] | None = None,
    pace_cardio_context: dict[str, Any] | None = None,
    matchup_context: dict[str, Any] | None = None,
    ruleset_context: dict[str, Any] | None = None,
    judging_referee_context: dict[str, Any] | None = None,
    availability_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
    calibration_context: dict[str, Any] | None = None,
    film_tracking_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_sport = normalize_combat_sport(sport)
    row = _merge(
        {"sport": sport, "market_type": market_type} if market_type else {"sport": sport},
        bout_context,
        fighter_a_context,
        fighter_b_context,
        striking_context,
        grappling_context,
        phase_context,
        damage_context,
        pace_cardio_context,
        matchup_context,
        ruleset_context,
        judging_referee_context,
        availability_context,
        incentive_context,
        calibration_context,
        film_tracking_context,
    )
    available: list[str] = []
    missing: list[str] = []
    for group, fields in FIELD_GROUPS.items():
        if present_fields(row, fields):
            available.append(group)
        else:
            missing.append(group)

    fighter_available = bool(present_fields(fighter_a_context or {}, FIELD_GROUPS["fighter_identity_context"])) and bool(
        present_fields(fighter_b_context or {}, FIELD_GROUPS["fighter_identity_context"])
    )
    bout_available = bool(present_fields(bout_context or {}, FIELD_GROUPS["basic_bout_context"]))
    film_available = bool(present_fields(film_tracking_context or {}, FIELD_GROUPS["film_tracking_context"]))

    if not fighter_available and not bout_available:
        data_tier = 0
    elif film_available or any(group in available for group in ("injury_medical_context", "camp_context", "judging_context", "referee_context", "weight_cut_context")) and any(
        group in available for group in ("phase_control_context", "round_level_context", "damage_durability_context")
    ):
        data_tier = 4
    elif any(
        group in available
        for group in (
            "round_level_context",
            "opponent_adjusted_context",
            "phase_control_context",
            "clinch_cage_context",
            "ground_control_context",
            "scramble_context",
            "damage_durability_context",
            "cardio_decline_context",
        )
    ):
        data_tier = 3
    elif any(group in available for group in ("striking_summary_context", "grappling_summary_context", "takedown_context", "submission_context", "knockdown_context", "pace_context")):
        data_tier = 2
    elif fighter_available or bout_available:
        data_tier = 1
    else:
        data_tier = 0

    cap = {0: 20.0, 1: 42.0, 2: 62.0, 3: 78.0, 4: 88.0}[data_tier]
    reason = DATA_TIER_REQUIREMENTS[data_tier]["tier_name"]
    calibration_allowed = "calibration_outcomes" in available
    if not calibration_allowed:
        cap = min(cap, 68.0)
    if not fighter_available and data_tier > 0:
        cap = min(cap, 45.0)
        reason = "fighter_identity_missing_caps_combat_review"

    next_data: list[str] = []
    if data_tier == 0:
        next_data.extend(["fighter_a_identity", "fighter_b_identity", "basic_bout_context"])
    if data_tier < 2:
        next_data.extend(["summary_striking_metrics", "summary_grappling_metrics", "finish_history"])
    if data_tier < 3:
        next_data.extend(["round_level_pace_damage", "phase_control_context", "control_time_by_round"])
    if data_tier < 4:
        next_data.extend(["optional_film_tracking", "optional_weight_cut_camp_referee_judging_context"])
    if not calibration_allowed:
        next_data.append("settled_combat_market_outcomes")

    return finalize_combat_response(
        {
            "status": "DATA_INSUFFICIENT" if data_tier == 0 else "combat_data_available",
            "sport": normalized_sport,
            "data_tier": data_tier,
            "tier_name": DATA_TIER_REQUIREMENTS[data_tier]["tier_name"],
            "fighter_level_allowed": fighter_available,
            "striking_level_allowed": "striking_summary_context" in available,
            "grappling_level_allowed": any(group in available for group in ("grappling_summary_context", "takedown_context", "submission_context")),
            "phase_control_allowed": "phase_control_context" in available,
            "damage_durability_allowed": "damage_durability_context" in available,
            "judging_referee_allowed": any(group in available for group in ("judging_context", "referee_context")),
            "calibration_allowed": calibration_allowed,
            "available_field_groups": available,
            "missing_field_groups": missing,
            "confidence_cap": cap,
            "confidence_cap_reason": reason,
            "no_fabrication": True,
            "phase_control_not_fabricated": "phase_control_context" not in available,
            "punch_tracking_not_fabricated": not film_available,
            "grappling_control_not_fabricated": "ground_control_context" not in available,
            "durability_not_fabricated": "damage_durability_context" not in available,
            "injury_status_not_fabricated": "injury_medical_context" not in available,
            "weight_cut_not_fabricated": "weight_cut_context" not in available,
            "camp_context_not_fabricated": "camp_context" not in available,
            "referee_tendency_not_fabricated": "referee_context" not in available,
            "judge_tendency_not_fabricated": "judging_context" not in available,
            "next_data_to_collect": compact_list(next_data, limit=35),
            "data_tier_requirements": DATA_TIER_REQUIREMENTS,
        },
        source_payload=row,
    )


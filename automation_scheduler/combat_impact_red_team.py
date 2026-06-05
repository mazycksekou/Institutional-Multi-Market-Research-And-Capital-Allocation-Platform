from __future__ import annotations

from typing import Any

from .combat_impact_common import compact_list, finalize_combat_response, normalize_combat_market


def evaluate_combat_impact_red_team(
    *,
    market_type: str | None = None,
    data_availability: dict[str, Any] | None = None,
    striking_impact: dict[str, Any] | None = None,
    grappling_control_impact: dict[str, Any] | None = None,
    phase_control_context: dict[str, Any] | None = None,
    damage_durability_context: dict[str, Any] | None = None,
    pace_cardio_context: dict[str, Any] | None = None,
    matchup_context: dict[str, Any] | None = None,
    availability_context: dict[str, Any] | None = None,
    ruleset_referee_judging_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
    market_relevance: dict[str, Any] | None = None,
    calibration: dict[str, Any] | None = None,
    film_tracking_context: dict[str, Any] | None = None,
    source_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = data_availability or {}
    striking = striking_impact or {}
    grappling = grappling_control_impact or {}
    phase = phase_control_context or {}
    damage = damage_durability_context or {}
    pace = pace_cardio_context or {}
    avail = availability_context or {}
    rules = ruleset_referee_judging_context or {}
    incentive = incentive_context or {}
    market_rel = market_relevance or {}
    calib = calibration or {}
    film = film_tracking_context or {}
    source = source_payload or {}
    market = normalize_combat_market(market_type or market_rel.get("selected_market_type") or "moneyline")
    missing_groups = set(data.get("missing_field_groups") or [])
    reasons: list[str] = []
    missing: list[str] = []

    if ("phase_control_context" in missing_groups or not data.get("phase_control_allowed", False)) and (film.get("claimed_phase_control") or phase.get("phase_control_score", 0) >= 65):
        reasons.append("phase_control_missing_but_claimed")
        missing.append("phase_control_context")
    if ("film_tracking_context" in missing_groups or data.get("punch_tracking_not_fabricated")) and (film.get("claimed_punch_tracking") or striking.get("boxing_punch_profile_score", 0) >= 75 and striking.get("limited_proxy")):
        reasons.append("punch_tracking_missing_but_claimed")
        missing.append("punch_tracking")
    if ("ground_control_context" in missing_groups or grappling.get("control_time_fabricated") is False and grappling.get("limited_proxy")) and film.get("claimed_grappling_control"):
        reasons.append("grappling_control_missing_but_claimed")
        missing.append("grappling_control")
    if ("damage_durability_context" in missing_groups or not data.get("damage_durability_allowed", False)) and (film.get("claimed_durability") or damage.get("durability_risk_score", 0) >= 70):
        reasons.append("durability_missing_but_claimed")
        missing.append("durability_context")
    if "chin_not_inferred_from_record_only" in (damage.get("no_bet_reasons") or []) or film.get("claimed_chin_from_record_only"):
        reasons.append("chin_claim_from_record_only")
    if ("injury_medical_context" in missing_groups or avail.get("injury_status_fabricated") is False) and film.get("claimed_injury_status"):
        reasons.append("injury_status_missing_but_claimed")
        missing.append("injury_status")
    if ("weight_cut_context" in missing_groups or avail.get("weight_cut_fabricated") is False) and film.get("claimed_weight_cut"):
        reasons.append("weight_cut_missing_but_claimed")
        missing.append("weight_cut")
    if ("camp_context" in missing_groups or avail.get("camp_context_fabricated") is False) and film.get("claimed_camp_context"):
        reasons.append("camp_context_missing_but_claimed")
        missing.append("camp_context")
    if "referee_context" in missing_groups and film.get("claimed_referee_tendency"):
        reasons.append("referee_tendency_missing_but_claimed")
        missing.append("referee_tendency")
    if "judging_context" in missing_groups and film.get("claimed_judge_tendency"):
        reasons.append("judge_tendency_missing_but_claimed")
        missing.append("judge_tendency")
    if striking.get("ko_tko_relevance_modifier", 0) >= 70 and striking.get("insufficient_sample"):
        reasons.append("small_sample_finish_rate_overfit")
    if "knockdown_average_sample_capped" in (striking.get("no_bet_reasons") or []):
        reasons.append("knockdown_rate_overfit")
    if grappling.get("submission_relevance_modifier", 0) >= 70 and grappling.get("insufficient_sample"):
        reasons.append("submission_rate_overfit")
    if avail.get("age_curve_risk_score", 0) >= 65 and source.get("claimed_age_curve_edge"):
        reasons.append("age_curve_overfit")
    if avail.get("layoff_risk_score", 0) >= 65 or source.get("claimed_layoff_narrative"):
        reasons.append("layoff_narrative_overfit")
    if incentive.get("narrative_overfit_risk") == "high" and source.get("rivalry_context") not in (None, ""):
        reasons.append("rivalry_narrative_overfit")
    if market in {"exact_round", "winning_method_round"} and calib.get("calibration_status") != "calibration_ready":
        reasons.append("exact_round_overconfidence")
    if market == "split_decision" and calib.get("calibration_status") != "calibration_ready":
        reasons.append("split_decision_overconfidence")
    if source.get("scheduled_rounds") in (5, "5") and pace.get("five_round_readiness_score", 0) <= 25 and film.get("claimed_five_round_cardio"):
        reasons.append("five_round_cardio_overclaim")
    ruleset = str(rules.get("ruleset") or source.get("ruleset") or "").lower()
    if (ruleset == "boxing" and grappling.get("grappling_impact_score", 0) > 40) or (ruleset == "mma" and source.get("boxing_only_claim")):
        reasons.append("boxing_mma_context_confusion")
    if calib.get("calibration_status") in (None, "", "insufficient_data"):
        reasons.append("calibration_missing")
        missing.extend(calib.get("next_required_data") or ["settled_combat_market_outcomes"])

    downgrade = min(100.0, len(reasons) * 8.0 + (20.0 if "calibration_missing" in reasons else 0.0))
    adjustment = "NO_CHANGE"
    if "phase_control_missing_but_claimed" in reasons or "durability_missing_but_claimed" in reasons or "boxing_mma_context_confusion" in reasons:
        adjustment = "NO_BET"
    elif downgrade >= 45:
        adjustment = "NO_BET"
    elif downgrade >= 20:
        adjustment = "DATA_INSUFFICIENT"
    return finalize_combat_response(
        {
            "red_team_status": "downgrade" if reasons else "clear",
            "downgrade_score": round(downgrade, 2),
            "recommended_action_adjustment": adjustment,
            "no_bet_reasons": compact_list(["red_team_hard_block_overconfidence"] if adjustment == "NO_BET" else [], limit=10),
            "red_team_reasons": compact_list(reasons, limit=30),
            "missing_inputs": compact_list(missing, limit=30),
            "confidence_cap_reason": "red_team_downgrade" if reasons else None,
            "red_team_only": True,
        },
        source_payload=source,
    )


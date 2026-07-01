from __future__ import annotations

from typing import Any

from .combat_impact_common import boolish, clamp, compact_list, finalize_combat_response, missing_fields, score_from_range, weighted_average


AVAILABILITY_FIELDS = ("injury_status", "short_notice_flag", "weight_cut_severity", "layoff_days", "camp_length", "age")


def evaluate_combat_availability_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    injury = 70.0 if str(source.get("injury_status", "")).lower() in {"questionable", "injured", "out", "uncertain"} else 0.0
    if source.get("medical_suspension_context") not in (None, ""):
        injury = max(injury, score_from_range(source.get("medical_suspension_context"), low=0.0, high=1.0) or 0.0)
    weight_cut = score_from_range(source.get("weight_cut_severity"), low=0.0, high=1.0) or 0.0
    missed_weight = score_from_range(source.get("missed_weight_history"), low=0.0, high=3.0) or 0.0
    short_notice = 75.0 if boolish(source.get("short_notice_flag")) else score_from_range(source.get("days_notice"), low=5.0, high=60.0, inverse=True) or 0.0
    layoff = score_from_range(source.get("layoff_days"), low=90.0, high=900.0) or 0.0
    camp = weighted_average(((score_from_range(source.get("camp_length"), low=0.0, high=12.0), 0.4), (score_from_range(source.get("training_camp_length"), low=0.0, high=12.0), 0.3), (100.0 - (score_from_range(source.get("camp_change_context"), low=0.0, high=1.0) or 0.0), 0.2), (100.0 - (score_from_range(source.get("team_change_context"), low=0.0, high=1.0) or 0.0), 0.1))) or 50.0
    age_curve = score_from_range(source.get("age"), low=28.0, high=42.0) or 0.0
    travel = weighted_average(((score_from_range(source.get("travel_distance"), low=0.0, high=7000.0), 0.25), (score_from_range(source.get("time_zone_change"), low=0.0, high=8.0), 0.25), (score_from_range(source.get("altitude_context"), low=0.0, high=1.0), 0.2))) or 0.0
    fight_week = weighted_average(((100.0 - injury, 0.25), (100.0 - weight_cut, 0.25), (100.0 - short_notice, 0.2), (camp, 0.2), (100.0 - travel, 0.1))) or 0.0
    availability = weighted_average(((fight_week, 0.45), (100.0 - layoff, 0.2), (100.0 - age_curve, 0.15), (camp, 0.2))) or 0.0
    no_bet = []
    if source.get("injury_status") in (None, ""):
        no_bet.append("injury_status_missing_not_fabricated")
    if source.get("weight_cut_severity") in (None, ""):
        no_bet.append("weight_cut_missing_not_fabricated")
    elif weight_cut >= 60:
        no_bet.append("bad_weight_cut_supplied_hard_warning")
    if boolish(source.get("short_notice_flag")):
        no_bet.append("short_notice_supplied_market_wide_uncertainty")
    if source.get("opponent_change_context") not in (None, ""):
        no_bet.append("opponent_change_invalidates_matchup_assumptions")
    if source.get("camp_change_context") not in (None, ""):
        no_bet.append("camp_change_uncertainty_modifier_only")
    return finalize_combat_response(
        {
            "availability_score": round(clamp(availability), 2),
            "injury_risk_score": round(clamp(injury), 2),
            "weight_cut_risk_score": round(clamp(weighted_average(((weight_cut, 0.6), (missed_weight, 0.3))) or 0.0), 2),
            "short_notice_risk_score": round(clamp(short_notice), 2),
            "layoff_risk_score": round(clamp(layoff), 2),
            "camp_stability_score": round(clamp(camp), 2),
            "age_curve_risk_score": round(clamp(age_curve), 2),
            "fight_week_stability_score": round(clamp(fight_week), 2),
            "confidence_cap_reason": "fight_week_uncertainty_cap" if no_bet else None,
            "injury_status_fabricated": False,
            "weight_cut_fabricated": False,
            "camp_context_fabricated": False,
            "health_fabricated": False,
            "missing_inputs": compact_list(missing_fields(source, AVAILABILITY_FIELDS), limit=20),
            "no_bet_reasons": compact_list(no_bet, limit=20),
        },
        source_payload=source,
    )

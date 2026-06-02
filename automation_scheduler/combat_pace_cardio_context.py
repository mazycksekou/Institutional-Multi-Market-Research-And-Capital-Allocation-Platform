from __future__ import annotations

from typing import Any

from .combat_impact_common import boolish, clamp, compact_list, finalize_combat_response, missing_fields, score_from_range, weighted_average


PACE_FIELDS = ("average_fight_time", "first_round_pace", "second_round_pace", "third_round_pace", "output_decline_by_round", "cardio_rating_proxy")


def evaluate_combat_pace_cardio_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    pace = weighted_average(((score_from_range(source.get("first_round_pace"), low=0.0, high=1.0), 0.3), (score_from_range(source.get("second_round_pace"), low=0.0, high=1.0), 0.25), (score_from_range(source.get("third_round_pace"), low=0.0, high=1.0), 0.2), (score_from_range(source.get("average_fight_time"), low=2.0, high=25.0), 0.15)))
    decline = weighted_average(((score_from_range(source.get("output_decline_by_round"), low=0.0, high=1.0), 0.35), (score_from_range(source.get("defensive_decline_by_round"), low=0.0, high=1.0), 0.3), (score_from_range(source.get("takedown_defense_decline"), low=0.0, high=1.0), 0.2), (score_from_range(source.get("striking_defense_decline"), low=0.0, high=1.0), 0.2)))
    cardio = weighted_average(((score_from_range(source.get("cardio_rating_proxy"), low=0.0, high=1.0), 0.35), (score_from_range(source.get("five_round_performance"), low=0.0, high=1.0), 0.25), (100.0 - (decline or 0.0), 0.25), (score_from_range(source.get("training_camp_length"), low=0.0, high=12.0), 0.15)))
    five_round = weighted_average(((score_from_range(source.get("five_round_experience"), low=0.0, high=5.0), 0.35), (score_from_range(source.get("five_round_performance"), low=0.0, high=1.0), 0.45), (cardio, 0.3)))
    short_notice_risk = 70.0 if boolish(source.get("short_notice_flag")) else 0.0
    weight_cut = score_from_range(source.get("weight_cut_severity"), low=0.0, high=1.0) or 0.0
    age_risk = score_from_range(source.get("age"), low=26.0, high=42.0) or 0.0
    layoff_risk = score_from_range(source.get("layoff_days"), low=90.0, high=900.0) or 0.0
    late_risk = weighted_average(((decline, 0.5), (short_notice_risk, 0.25), (weight_cut, 0.2), (age_risk, 0.15), (layoff_risk, 0.15))) or 0.0
    no_bet = []
    if source.get("average_fight_time") not in (None, "") and missing_fields(source, ("output_decline_by_round", "cardio_rating_proxy")):
        no_bet.append("average_fight_time_alone_does_not_infer_cardio")
    if boolish(source.get("short_notice_flag")):
        no_bet.append("short_notice_caps_cardio_confidence")
    if source.get("weight_cut_severity") not in (None, ""):
        no_bet.append("weight_cut_severity_caps_late_round_confidence")
    if source.get("scheduled_rounds") in (5, "5") and five_round is None:
        no_bet.append("five_round_markets_require_five_round_context_or_cap")
    return finalize_combat_response(
        {
            "pace_score": round(clamp(pace or 0.0), 2),
            "cardio_score": round(clamp(cardio or 0.0), 2),
            "round_progression_score": round(clamp(weighted_average(((pace, 0.45), (100.0 - (late_risk or 0.0), 0.35), (five_round, 0.2))) or 0.0), 2),
            "late_fight_risk_score": round(clamp(late_risk), 2),
            "five_round_readiness_score": round(clamp(five_round or 0.0), 2),
            "gas_tank_warning_score": round(clamp(late_risk), 2),
            "over_under_rounds_modifier": round(clamp(weighted_average(((pace, 0.25), (cardio, 0.3), (100.0 - late_risk, 0.3))) or 0.0), 2),
            "late_finish_relevance": round(clamp(weighted_average(((late_risk, 0.35), (decline, 0.35), (pace, 0.2))) or 0.0), 2),
            "round_decline_fabricated": False,
            "weight_cut_fabricated": False,
            "missing_inputs": compact_list(missing_fields(source, PACE_FIELDS), limit=20),
            "no_bet_reasons": compact_list(no_bet, limit=20),
        },
        source_payload=source,
    )

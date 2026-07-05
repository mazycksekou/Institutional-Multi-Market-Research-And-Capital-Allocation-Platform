from __future__ import annotations

from typing import Any

from .soccer_impact_common import clamp, compact_list, finalize_soccer_response, missing_fields, score_from_range, weighted_average


PRESSING_FIELDS = ("pressures", "high_turnovers", "counterpress_regains", "counterattack_xg", "transition_xg_against", "rest_defense_quality")


def evaluate_soccer_pressing_transition_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    pressing = weighted_average(
        (
            (score_from_range(source.get("pressures"), low=60, high=220), 0.35),
            (score_from_range(source.get("successful_pressures"), low=15, high=80), 0.35),
            (score_from_range(source.get("pressures_final_third"), low=5, high=55), 0.35),
            (score_from_range(source.get("ppda_proxy"), low=18, high=6), 0.45),
        )
    )
    high_turnover = weighted_average(((score_from_range(source.get("high_turnovers"), low=1, high=14), 0.6), (score_from_range(source.get("turnovers_forced_final_third"), low=1, high=14), 0.4)))
    counterpress = weighted_average(((score_from_range(source.get("counterpress_regains"), low=1, high=18), 0.55), (score_from_range(source.get("pressure_regain_time"), low=12, high=3), 0.35)))
    transition_attack = weighted_average(
        (
            (score_from_range(source.get("counterattack_xg"), low=0, high=0.8), 0.55),
            (score_from_range(source.get("counterattack_shots"), low=0, high=6), 0.35),
            (score_from_range(source.get("direct_attacks"), low=0, high=12), 0.3),
            (score_from_range(source.get("transition_xg_for"), low=0, high=0.9), 0.5),
            (score_from_range(source.get("fast_break_rate"), low=0, high=1), 0.25),
        )
    )
    transition_risk = weighted_average(
        (
            (score_from_range(source.get("transition_xg_against"), low=0, high=0.9), 0.55),
            (score_from_range(source.get("transition_shots_against"), low=0, high=7), 0.35),
            (score_from_range(source.get("defensive_transition_vulnerability"), low=0, high=1), 0.45),
            (score_from_range(source.get("turnovers_in_own_third"), low=0, high=8), 0.35),
            (score_from_range(source.get("opponent_counterattack_rate"), low=0, high=1), 0.25),
        )
    )
    rest_defense = weighted_average(((score_from_range(source.get("rest_defense_quality"), low=0, high=1), 0.7), (100.0 - (transition_risk or 0.0), 0.3))) or 0.0
    modifier = weighted_average(((pressing, 0.2), (high_turnover, 0.2), (transition_attack, 0.25), (100.0 - (transition_risk or 0.0), 0.2), (rest_defense, 0.15))) or 0.0
    no_bet = []
    if missing_fields(source, PRESSING_FIELDS):
        no_bet.append("pressing_transition_data_optional_missing_caps_advanced_confidence")
    if source.get("pressures") in (None, "") and source.get("possession_share") not in (None, ""):
        no_bet.append("pressing_not_inferred_from_possession_share")
    return finalize_soccer_response(
        {
            "pressing_impact_score": round(clamp(pressing or 0.0), 2),
            "high_turnover_score": round(clamp(high_turnover or 0.0), 2),
            "counterpress_score": round(clamp(counterpress or 0.0), 2),
            "transition_attack_score": round(clamp(transition_attack or 0.0), 2),
            "transition_defense_risk": round(clamp(transition_risk or 0.0), 2),
            "rest_defense_score": round(clamp(rest_defense), 2),
            "market_relevance_modifier": round(clamp(modifier), 2),
            "pressing_fabricated": False,
            "missing_inputs": compact_list(missing_fields(source, PRESSING_FIELDS), limit=20),
            "no_bet_reasons": compact_list(no_bet, limit=20),
        },
        source_payload=source,
    )

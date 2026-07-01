from __future__ import annotations

from typing import Any

from .soccer_impact_common import boolish, clamp, compact_list, finalize_soccer_response, missing_fields, score_from_range, weighted_average


TACTICAL_FIELDS = ("formation", "high_press_rate", "ppda_proxy", "defensive_line_height", "counter_pressing_rate", "manager_style_context")


def evaluate_soccer_tactical_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    has_formation = source.get("formation") not in (None, "")
    pressing = weighted_average(
        (
            (score_from_range(source.get("high_press_rate"), low=0, high=1), 0.55),
            (score_from_range(source.get("pressure_intensity"), low=0, high=1), 0.45),
            (score_from_range(source.get("ppda_proxy"), low=18, high=6), 0.55),
        )
    )
    counterpress = weighted_average(
        (
            (score_from_range(source.get("counter_pressing_rate"), low=0, high=1), 0.55),
            (score_from_range(source.get("counterattack_rate"), low=0, high=1), 0.2),
        )
    )
    directness = score_from_range(source.get("directness_score"), low=0, high=1)
    formation_stability = weighted_average(
        (
            (90.0 if has_formation else 25.0, 0.45),
            (score_from_range(source.get("tactical_shift_recent"), low=0, high=1, inverse=True), 0.35),
            (score_from_range(source.get("home_away_style_split"), low=0, high=1, inverse=True), 0.2),
        )
    )
    style_balance = weighted_average(
        (
            (pressing, 0.25),
            (counterpress, 0.2),
            (directness, 0.2),
            (score_from_range(source.get("defensive_line_height"), low=0, high=1), 0.2),
            (score_from_range(source.get("compactness_proxy"), low=0, high=1), 0.15),
        )
    )
    tactical_fit = weighted_average(((formation_stability, 0.35), (style_balance, 0.45), (score_from_range(source.get("central_progression_rate"), low=0, high=1), 0.2))) or 0.0
    mismatch_risk = weighted_average(
        (
            (100.0 if not has_formation else 20.0, 0.35),
            (score_from_range(source.get("tactical_shift_recent"), low=0, high=1), 0.45),
            (score_from_range(source.get("rest_defense_structure"), low=0, high=1, inverse=True), 0.3),
        )
    )
    relevance = weighted_average(((tactical_fit, 0.45), (pressing, 0.25), (directness, 0.2), (100.0 - (mismatch_risk or 0.0), 0.1))) or 0.0
    no_bet = []
    if not has_formation:
        no_bet.append("formation_missing_not_fabricated")
    if source.get("tactical_shift_recent"):
        no_bet.append("recent_tactical_or_manager_change_caps_history")
    return finalize_soccer_response(
        {
            "tactical_fit_score": round(clamp(tactical_fit), 2),
            "tactical_stability_score": round(clamp(formation_stability or 0.0), 2),
            "pressing_score": round(clamp(pressing or 0.0), 2),
            "counter_pressing_score": round(clamp(counterpress or 0.0), 2),
            "directness_score": round(clamp(directness or 0.0), 2),
            "formation_stability_score": round(clamp(formation_stability or 0.0), 2),
            "tactical_mismatch_risk": round(clamp(mismatch_risk or 0.0), 2),
            "style_market_relevance": round(clamp(relevance), 2),
            "formation": source.get("formation") if has_formation else None,
            "formation_fabricated": False,
            "tactical_context_standalone_edge": False,
            "missing_inputs": compact_list(missing_fields(source, TACTICAL_FIELDS), limit=20),
            "no_bet_reasons": compact_list(no_bet, limit=20),
        },
        source_payload=source,
    )

from __future__ import annotations

from typing import Any

from .soccer_impact_common import boolish, clamp, compact_list, finalize_soccer_response, score_from_range, weighted_average


def evaluate_soccer_matchup_context(row: dict[str, Any] | None = None, *, market_type: str = "three_way_moneyline") -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    high_press_build = weighted_average(((score_from_range(source.get("high_press_rate"), low=0, high=1), 0.45), (score_from_range(source.get("opponent_build_up_error_rate"), low=0, high=1), 0.45), (score_from_range(source.get("ppda_proxy"), low=18, high=6), 0.25)))
    counter_high_line = weighted_average(((score_from_range(source.get("counterattack_xg"), low=0, high=0.8), 0.45), (score_from_range(source.get("opponent_defensive_line_height"), low=0, high=1), 0.4), (score_from_range(source.get("directness_score"), low=0, high=1), 0.25)))
    wide_overload = weighted_average(((score_from_range(source.get("wide_progression_rate"), low=0, high=1), 0.35), (score_from_range(source.get("overload_side"), low=0, high=1), 0.35), (score_from_range(source.get("opponent_fullback_weakness"), low=0, high=1), 0.45)))
    central_progression = weighted_average(((score_from_range(source.get("central_progression_rate"), low=0, high=1), 0.4), (score_from_range(source.get("opponent_midfield_compactness"), low=0, high=1, inverse=True), 0.45)))
    set_piece = weighted_average(((score_from_range(source.get("set_piece_xg_for"), low=0, high=0.9), 0.45), (score_from_range(source.get("opponent_set_piece_defense"), low=0, high=1, inverse=True), 0.35), (score_from_range(source.get("aerial_duel_strength"), low=0, high=1), 0.25)))
    low_block = weighted_average(((score_from_range(source.get("possession_share"), low=0.35, high=0.7), 0.25), (score_from_range(source.get("opponent_low_block"), low=0, high=1), 0.35), (score_from_range(source.get("xg_per_shot"), low=0.04, high=0.18), 0.3)))
    referee_aggression = weighted_average(((score_from_range(source.get("card_rate"), low=1, high=8), 0.35), (score_from_range(source.get("team_foul_rate"), low=5, high=20), 0.25), (score_from_range(source.get("derby_rivalry_intensity"), low=0, high=1), 0.25)))
    advantage = weighted_average(((high_press_build, 0.18), (counter_high_line, 0.2), (wide_overload, 0.16), (central_progression, 0.14), (set_piece, 0.16), (low_block, 0.08), (100.0 - (referee_aggression or 0.0), 0.08))) or 0.0
    risk = weighted_average(((100.0 if not boolish(source.get("confirmed_lineup")) and source.get("formation") in (None, "") else 20.0, 0.35), (100.0 if source.get("formation") in (None, "") else 20.0, 0.25), (score_from_range(source.get("transition_xg_against"), low=0, high=0.9), 0.25), (score_from_range(source.get("red_card_rate"), low=0, high=0.5), 0.25))) or 0.0
    notes = []
    if high_press_build and high_press_build >= 60:
        notes.append("high_press_vs_weak_build_up")
    if counter_high_line and counter_high_line >= 60:
        notes.append("counterattack_vs_high_defensive_line")
    if wide_overload and wide_overload >= 60:
        notes.append("wide_overload_vs_weak_fullback_side")
    if set_piece and set_piece >= 60:
        notes.append("set_piece_attack_vs_set_piece_defense")
    if low_block and low_block >= 60:
        notes.append("possession_team_vs_low_block_shot_quality")
    no_bet = []
    if not notes:
        no_bet.append("tactical_mismatch_not_claimed_without_supporting_fields")
    if risk >= 65:
        no_bet.append("conflicting_or_missing_matchup_signals_reduce_confidence")
    return finalize_soccer_response(
        {
            "matchup_advantage_score": round(clamp(advantage), 2),
            "matchup_risk_score": round(clamp(risk), 2),
            "tactical_mismatch_reasons": compact_list(notes, limit=15),
            "no_bet_reasons": compact_list(no_bet, limit=15),
            "market_specific_matchup_notes": compact_list(notes, limit=15),
            "three_way_relevance": round(clamp(weighted_average(((advantage, 0.45), (100.0 - risk, 0.25), (low_block, 0.15))) or 0.0), 2),
            "asian_handicap_relevance": round(clamp(weighted_average(((advantage, 0.45), (counter_high_line, 0.25), (set_piece, 0.15), (100.0 - risk, 0.15))) or 0.0), 2),
            "total_relevance": round(clamp(weighted_average(((counter_high_line, 0.3), (set_piece, 0.2), (referee_aggression, 0.2), (score_from_range(source.get("transition_xg_against"), low=0, high=0.9), 0.25))) or 0.0), 2),
            "btts_relevance": round(clamp(weighted_average(((counter_high_line, 0.25), (score_from_range(source.get("transition_xg_against"), low=0, high=0.9), 0.35), (set_piece, 0.15))) or 0.0), 2),
            "team_total_relevance": round(clamp(weighted_average(((advantage, 0.3), (set_piece, 0.25), (low_block, 0.2))) or 0.0), 2),
            "player_prop_relevance": round(clamp(weighted_average(((wide_overload, 0.25), (central_progression, 0.25), (set_piece, 0.25), (counter_high_line, 0.2))) or 0.0), 2),
            "card_prop_relevance": round(clamp(referee_aggression or 0.0), 2),
            "tactical_mismatch_fabricated": False,
        },
        source_payload=source,
    )

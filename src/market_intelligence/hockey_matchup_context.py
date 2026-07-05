from __future__ import annotations

from typing import Any

from .hockey_impact_common import boolish, clamp, compact_list, finalize_hockey_response, score_from_range, weighted_average


def evaluate_hockey_matchup_context(row: dict[str, Any] | None = None, *, market_type: str = "moneyline") -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    pp_vs_pk = weighted_average(
        (
            (score_from_range(source.get("power_play_xg_rate"), low=0.25, high=1.25), 0.55),
            (score_from_range(source.get("opponent_penalty_kill_xg_against_rate"), low=0.25, high=1.25), 0.45),
            (score_from_range(source.get("opponent_penalty_rate"), low=1.5, high=5.5), 0.25),
        )
    )
    line_pair = weighted_average(
        (
            (score_from_range(source.get("line_xg_share"), low=0.38, high=0.62), 0.45),
            (score_from_range(source.get("defensive_pair_xg_share"), low=0.38, high=0.62, inverse=True), 0.35),
            (score_from_range(source.get("matchup_deployment"), low=0, high=1), 0.25),
        )
    )
    rush_matchup = weighted_average(
        (
            (score_from_range(source.get("rush_chances_for"), low=1, high=10), 0.4),
            (score_from_range(source.get("rush_chances_against"), low=1, high=10, inverse=True), 0.35),
            (score_from_range(source.get("odd_man_rushes_for"), low=0, high=5), 0.25),
        )
    )
    shot_suppression = weighted_average(
        (
            (score_from_range(source.get("shots_for_per_game"), low=22, high=38), 0.3),
            (score_from_range(source.get("opponent_shot_suppression"), low=0, high=1, inverse=True), 0.45),
            (score_from_range(source.get("opponent_shots_against_per_game"), low=22, high=38), 0.35),
        )
    )
    goalie_hd = weighted_average(
        (
            (score_from_range(source.get("high_danger_chances_for"), low=5, high=18), 0.35),
            (score_from_range(source.get("opponent_goalie_high_danger_save_percentage"), low=0.74, high=0.89, inverse=True), 0.45),
            (score_from_range(source.get("rebound_chances_for"), low=1, high=8), 0.25),
            (score_from_range(source.get("opponent_goalie_rebound_control_proxy"), low=0, high=1, inverse=True), 0.25),
        )
    )
    fatigue_mismatch = weighted_average(
        (
            (85.0 if boolish(source.get("opponent_back_to_back")) else 20.0, 0.35),
            (score_from_range(source.get("rest_advantage_days"), low=-3, high=3), 0.35),
            (score_from_range(source.get("opponent_three_in_four"), low=0, high=1), 0.25),
        )
    )
    matchup_advantage = weighted_average(((pp_vs_pk, 0.22), (line_pair, 0.22), (rush_matchup, 0.18), (shot_suppression, 0.18), (goalie_hd, 0.12), (fatigue_mismatch, 0.08))) or 0.0
    risk = weighted_average(
        (
            (100.0 if not boolish(source.get("confirmed_lines")) and source.get("line_xg_share") in (None, "") else 20.0, 0.35),
            (100.0 if not boolish(source.get("confirmed_goalie")) and not boolish(source.get("confirmed_starter")) else 20.0, 0.35),
            (score_from_range(source.get("opponent_rush_chances_for"), low=1, high=10), 0.25),
            (100.0 if source.get("referee_penalty_tendency_proxy") in (None, "") and market_type in {"total", "team_total"} else 30.0, 0.2),
        )
    )
    notes = []
    if pp_vs_pk and pp_vs_pk >= 60:
        notes.append("power_play_vs_penalty_kill_relevant")
    if line_pair and line_pair >= 60:
        notes.append("line_vs_pair_matchup_relevant")
    if rush_matchup and rush_matchup >= 60:
        notes.append("rush_offense_vs_rush_defense_relevant")
    if goalie_hd and goalie_hd >= 60:
        notes.append("high_danger_rebound_vs_goalie_context_relevant")
    if fatigue_mismatch and fatigue_mismatch >= 60:
        notes.append("rest_fatigue_mismatch_relevant")
    no_bet = []
    if risk and risk >= 65:
        no_bet.append("matchup_context_uncertain_caps_confidence")
    if not boolish(source.get("confirmed_lines")) and source.get("line_xg_share") in (None, ""):
        no_bet.append("line_pair_deployment_not_fabricated")
    if source.get("referee_penalty_tendency_proxy") in (None, ""):
        no_bet.append("penalty_environment_missing_not_fabricated")
    return finalize_hockey_response(
        {
            "matchup_advantage_score": round(clamp(matchup_advantage), 2),
            "matchup_risk_score": round(clamp(risk or 0.0), 2),
            "mismatch_reasons": compact_list(notes, limit=15),
            "no_bet_reasons": compact_list(no_bet, limit=15),
            "market_specific_matchup_notes": compact_list(notes, limit=15),
            "moneyline_relevance": round(clamp(weighted_average(((matchup_advantage, 0.55), (100.0 - (risk or 0.0), 0.25), (fatigue_mismatch, 0.2))) or 0.0), 2),
            "puckline_relevance": round(clamp(weighted_average(((matchup_advantage, 0.5), (rush_matchup, 0.25), (goalie_hd, 0.2))) or 0.0), 2),
            "total_relevance": round(clamp(weighted_average(((pp_vs_pk, 0.3), (rush_matchup, 0.25), (goalie_hd, 0.25), (fatigue_mismatch, 0.15))) or 0.0), 2),
            "team_total_relevance": round(clamp(weighted_average(((pp_vs_pk, 0.35), (shot_suppression, 0.3), (goalie_hd, 0.25))) or 0.0), 2),
            "player_prop_relevance": round(clamp(weighted_average(((line_pair, 0.35), (shot_suppression, 0.25), (pp_vs_pk, 0.25))) or 0.0), 2),
            "goalie_prop_relevance": round(clamp(weighted_average(((shot_suppression, 0.25), (goalie_hd, 0.25), (fatigue_mismatch, 0.25), (rush_matchup, 0.15))) or 0.0), 2),
            "deployment_fabricated": False,
        },
        source_payload=source,
    )

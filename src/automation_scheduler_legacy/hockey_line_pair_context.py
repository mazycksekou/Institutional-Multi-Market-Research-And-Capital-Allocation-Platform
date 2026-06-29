from __future__ import annotations

from typing import Any

from .hockey_impact_common import boolish, clamp, compact_list, finalize_hockey_response, missing_fields, score_centered, score_from_range, weighted_average


LINE_PAIR_FIELDS = (
    "confirmed_lines",
    "line_xg_share",
    "line_shot_share",
    "line_time_on_ice",
    "defensive_pair_xg_share",
    "defensive_pair_time_on_ice",
)


def evaluate_hockey_line_pair_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    confirmed_lines = boolish(source.get("confirmed_lines"))
    projected_lines = boolish(source.get("projected_lines"))
    confirmed_pairs = boolish(source.get("confirmed_pairs") if "confirmed_pairs" in source else source.get("confirmed_defensive_pairs"))
    line_quality = weighted_average(
        (
            (score_centered(source.get("line_xg_share"), center=0.5, span=0.2), 0.7),
            (score_centered(source.get("line_shot_share"), center=0.5, span=0.2), 0.55),
            (score_centered(source.get("line_high_danger_share"), center=0.5, span=0.2), 0.45),
            (score_from_range(source.get("line_time_on_ice"), low=5, high=18), 0.25),
        )
    )
    line_stability = weighted_average(
        (
            (95.0 if confirmed_lines else 62.0 if projected_lines else 28.0, 0.55),
            (score_from_range(source.get("line_continuity"), low=0, high=1), 0.45),
            (score_from_range(source.get("line_time_on_ice"), low=5, high=18), 0.25),
        )
    )
    pair_quality = weighted_average(
        (
            (score_centered(source.get("defensive_pair_xg_share"), center=0.5, span=0.2), 0.65),
            (score_centered(source.get("defensive_pair_shot_share"), center=0.5, span=0.2), 0.45),
            (score_from_range(source.get("defensive_pair_time_on_ice"), low=8, high=24), 0.25),
        )
    )
    pair_stability = weighted_average(
        (
            (95.0 if confirmed_pairs else 55.0 if source.get("defensive_pair_xg_share") not in (None, "") else 25.0, 0.45),
            (score_from_range(source.get("defensive_pair_continuity"), low=0, high=1), 0.5),
            (score_from_range(source.get("defensive_pair_time_on_ice"), low=8, high=24), 0.25),
        )
    )
    matchup_deployment = weighted_average(
        (
            (score_from_range(source.get("matchup_deployment"), low=0, high=1), 0.4),
            (score_from_range(source.get("opponent_top_line_context"), low=0, high=1), 0.25),
            (score_from_range(source.get("opponent_top_pair_context"), low=0, high=1), 0.25),
        )
    )
    last_change = 68.0 if boolish(source.get("home_last_change")) else 45.0 if source.get("home_last_change") not in (None, "") else 0.0
    prop_volume_modifier = weighted_average(((line_quality, 0.45), (line_stability, 0.45), (last_change, 0.12))) or 0.0
    team_modifier = weighted_average(((line_quality, 0.35), (pair_quality, 0.35), (line_stability, 0.15), (pair_stability, 0.15))) or 0.0
    missing = missing_fields(source, LINE_PAIR_FIELDS)
    no_bet = []
    if not confirmed_lines:
        no_bet.append("confirmed_lines_missing_caps_skater_props")
    if not confirmed_pairs and source.get("defensive_pair_xg_share") in (None, ""):
        no_bet.append("defensive_pair_context_missing_caps_goalie_team_defense")
    if source.get("line_xg_share") in (None, ""):
        no_bet.append("line_xg_share_missing_not_fabricated")

    return finalize_hockey_response(
        {
            "line_quality_score": round(clamp(line_quality or 0.0), 2),
            "line_stability_score": round(clamp(line_stability or 0.0), 2),
            "pair_quality_score": round(clamp(pair_quality or 0.0), 2),
            "pair_stability_score": round(clamp(pair_stability or 0.0), 2),
            "matchup_deployment_score": round(clamp(matchup_deployment or 0.0), 2),
            "last_change_context_score": round(clamp(last_change), 2),
            "prop_volume_modifier": round(clamp(prop_volume_modifier), 2),
            "team_market_modifier": round(clamp(team_modifier), 2),
            "confirmed_lines": confirmed_lines,
            "line_role_fabricated": False,
            "defensive_pair_fabricated": False,
            "missing_inputs": compact_list(missing, limit=20),
            "no_bet_reasons": compact_list(no_bet, limit=20),
        },
        source_payload=source,
    )

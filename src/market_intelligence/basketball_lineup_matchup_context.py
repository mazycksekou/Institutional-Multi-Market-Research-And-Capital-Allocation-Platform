from __future__ import annotations

from typing import Any

from .basketball_player_impact_common import (
    boolish,
    clamp,
    compact_list,
    finalize_safe_response,
    missing_fields,
    percent_score,
    present_fields,
    safe_float,
    score_centered,
    score_from_range,
    weighted_average,
)


LINEUP_MATCHUP_INPUTS = (
    "projected_starting_lineup",
    "projected_closing_lineup",
    "teammate_injuries",
    "teammate_usage_absences",
    "lineup_net_rating",
    "lineup_offensive_rating",
    "lineup_defensive_rating",
    "lineup_pace",
    "lineup_spacing_score",
    "lineup_rebounding_score",
    "lineup_defensive_scheme",
    "opponent_defensive_scheme",
    "opponent_pace",
    "opponent_rebounding_profile",
    "opponent_pick_and_roll_defense",
    "opponent_rim_protection",
    "opponent_three_point_allowed_profile",
    "opponent_foul_rate",
    "opponent_turnover_forced_rate",
    "opponent_switch_rate",
    "player_primary_defender",
    "defensive_matchup_rating",
    "team_spread",
    "game_total",
    "implied_team_total",
    "blowout_risk",
    "back_to_back",
    "rest_days",
    "travel_fatigue",
    "schedule_density",
)


def _absence_shift(row: dict[str, Any]) -> float:
    explicit = safe_float(row.get("teammate_absence_usage_shift"))
    if explicit is not None:
        return explicit
    absences = row.get("teammate_usage_absences")
    if isinstance(absences, list):
        return min(12.0, len(absences) * 2.5)
    injuries = row.get("teammate_injuries")
    if isinstance(injuries, list):
        high_usage = sum(1 for item in injuries if isinstance(item, dict) and boolish(item.get("high_usage")))
        return min(10.0, high_usage * 3.0)
    return 0.0


def evaluate_lineup_matchup_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    present = present_fields(source, LINEUP_MATCHUP_INPUTS)
    missing = missing_fields(source, LINEUP_MATCHUP_INPUTS)
    lineup_fit = weighted_average(
        (
            (score_centered(source.get("lineup_net_rating"), center=0.0, span=18.0), 1.2),
            (score_from_range(source.get("lineup_offensive_rating"), low=96.0, high=124.0), 0.55),
            (score_from_range(source.get("lineup_defensive_rating"), low=96.0, high=124.0, inverse=True), 0.55),
            (percent_score(source.get("lineup_spacing_score")), 0.7),
            (percent_score(source.get("lineup_rebounding_score")), 0.45),
        )
    )
    matchup_fit = weighted_average(
        (
            (percent_score(source.get("defensive_matchup_rating")), 0.9),
            (score_from_range(source.get("opponent_pick_and_roll_defense"), low=0.0, high=100.0, inverse=True), 0.5),
            (score_from_range(source.get("opponent_rim_protection"), low=0.0, high=100.0, inverse=True), 0.55),
            (percent_score(source.get("opponent_three_point_allowed_profile")), 0.45),
            (score_from_range(source.get("opponent_foul_rate"), low=0.08, high=0.28), 0.35),
            (score_from_range(source.get("opponent_turnover_forced_rate"), low=0.08, high=0.22, inverse=True), 0.3),
            (score_from_range(source.get("opponent_rebounding_profile"), low=0.0, high=100.0, inverse=True), 0.35),
        )
    )
    projected_minutes = score_from_range(source.get("projected_minutes"), low=8.0, high=38.0)
    closing_probability = percent_score(source.get("closing_lineup_probability"))
    if closing_probability is None:
        closing_status = str(source.get("closing_lineup_status") or "").strip().lower()
        if closing_status in {"yes", "starter", "closing", "likely"}:
            closing_probability = 78.0
        elif closing_status in {"fringe", "uncertain", "questionable"}:
            closing_probability = 45.0
        elif closing_status:
            closing_probability = 25.0
    absence_shift = _absence_shift(source)
    blowout = percent_score(source.get("blowout_risk"))
    if blowout is None:
        spread = abs(safe_float(source.get("team_spread"), 0.0) or 0.0)
        blowout = clamp(max(0.0, (spread - 6.0) * 8.0))
    pace_score = weighted_average(
        (
            (score_from_range(source.get("lineup_pace"), low=66.0, high=106.0), 0.55),
            (score_from_range(source.get("opponent_pace"), low=66.0, high=106.0), 0.55),
            (score_from_range(source.get("game_total"), low=128.0, high=252.0), 0.4),
            (score_from_range(source.get("implied_team_total"), low=58.0, high=132.0), 0.35),
        )
    )
    fatigue_penalty = weighted_average(
        (
            (100.0 if boolish(source.get("back_to_back")) else 0.0, 0.4),
            (score_from_range(source.get("travel_fatigue"), low=0.0, high=1.0), 0.5),
            (score_from_range(source.get("schedule_density"), low=0.0, high=5.0), 0.35),
        )
    ) or 0.0
    game_script_fit = weighted_average(
        (
            (pace_score, 0.65),
            (lineup_fit, 0.5),
            (matchup_fit, 0.45),
            (100.0 - blowout, 0.45),
            (100.0 - fatigue_penalty, 0.25),
        )
    )
    status = "missing" if not present else ("partial" if source.get("projected_starting_lineup") in (None, "", []) else "ok")
    confidence = clamp(20.0 + min(len(present) / len(LINEUP_MATCHUP_INPUTS), 1.0) * 75.0)

    return finalize_safe_response(
        {
            "lineup_fit_score": round(clamp(lineup_fit or 0.0), 2),
            "matchup_fit_score": round(clamp(matchup_fit or 0.0), 2),
            "projected_minutes_context": round(clamp(projected_minutes or 0.0), 2),
            "closing_lineup_probability": round(clamp(closing_probability or 0.0), 2),
            "teammate_absence_usage_shift": round(float(absence_shift), 2),
            "opponent_matchup_edge": round(clamp(matchup_fit or 0.0), 2),
            "blowout_minutes_risk": round(clamp(blowout or 0.0), 2),
            "pace_context_score": round(clamp(pace_score or 0.0), 2),
            "game_script_fit_score": round(clamp(game_script_fit or 0.0), 2),
            "lineup_matchup_confidence": round(confidence, 2),
            "lineup_matchup_status": status,
            "lineup_matchup_missing_inputs": compact_list(missing, limit=35),
        },
        source_payload=source,
    )

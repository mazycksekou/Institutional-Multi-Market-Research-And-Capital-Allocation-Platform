from __future__ import annotations

from typing import Any

from .hockey_impact_common import boolish, clamp, compact_list, finalize_hockey_response, missing_fields, score_from_range, weighted_average


AVAILABILITY_FIELDS = (
    "skater_injury_status",
    "goalie_injury_status",
    "confirmed_goalie",
    "confirmed_lines",
    "rest_days",
    "back_to_back",
)


def _injury_risk(*values: Any) -> float:
    joined = " ".join(str(value or "").lower() for value in values)
    if "out" in joined or "doubtful" in joined or "injured" in joined:
        return 95.0
    if "questionable" in joined or "game_time" in joined:
        return 72.0
    if "probable" in joined:
        return 35.0
    if "healthy" in joined or "active" in joined:
        return 10.0
    return 45.0


def evaluate_hockey_availability_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    injury_risk = _injury_risk(source.get("skater_injury_status"), source.get("goalie_injury_status"), source.get("injury_status"))
    confirmed_goalie = boolish(source.get("confirmed_goalie") if "confirmed_goalie" in source else source.get("confirmed_starter"))
    confirmed_lines = boolish(source.get("confirmed_lines"))
    lineup_certainty = weighted_average(((95.0 if confirmed_lines else 45.0, 0.45), (score_from_range(source.get("scratches_context"), low=0, high=1, inverse=True), 0.25), (score_from_range(source.get("callup_context"), low=0, high=1, inverse=True), 0.2))) or (95.0 if confirmed_lines else 45.0)
    goalie_certainty = 95.0 if confirmed_goalie else 42.0 if boolish(source.get("projected_goalie")) else 25.0
    rest_travel = weighted_average(
        (
            (85.0 if boolish(source.get("back_to_back")) else 20.0, 0.45),
            (88.0 if boolish(source.get("three_in_four")) else 20.0, 0.4),
            (score_from_range(source.get("rest_days"), low=0, high=4, inverse=True), 0.3),
            (score_from_range(source.get("travel_distance"), low=0, high=2500), 0.25),
            (score_from_range(source.get("time_zone_change"), low=0, high=3), 0.25),
            (score_from_range(source.get("altitude"), low=0, high=6000), 0.15),
        )
    )
    fatigue = weighted_average(
        (
            (rest_travel, 0.55),
            (score_from_range(source.get("overtime_recent"), low=0, high=3), 0.25),
            (score_from_range(source.get("shootout_recent"), low=0, high=3), 0.2),
            (score_from_range(source.get("starting_goalie_workload"), low=0, high=8), 0.35),
        )
    )
    role_stability = weighted_average(
        (
            (lineup_certainty, 0.35),
            (score_from_range(source.get("minutes_or_toi_recent"), low=8, high=23), 0.25),
            (score_from_range(source.get("shift_count_recent"), low=10, high=28), 0.25),
            (score_from_range(source.get("schedule_density"), low=0, high=1, inverse=True), 0.15),
        )
    )
    availability = weighted_average(((100.0 - injury_risk, 0.4), (lineup_certainty, 0.22), (goalie_certainty, 0.18), (100.0 - clamp(fatigue or 0.0), 0.2))) or 0.0
    no_bet = []
    if not confirmed_goalie:
        no_bet.append("unconfirmed_goalie_major_market_warning")
    if not confirmed_lines:
        no_bet.append("confirmed_lines_missing_caps_skater_props")
    if injury_risk >= 70:
        no_bet.append("injury_uncertainty_hard_warning")
    if boolish(source.get("back_to_back")):
        no_bet.append("back_to_back_fatigue_risk")
    if boolish(source.get("three_in_four")):
        no_bet.append("three_in_four_fatigue_risk")
    if source.get("top_line_absence"):
        no_bet.append("top_line_absence_affects_team_and_player_markets")
    if source.get("defensive_pair_injury"):
        no_bet.append("top_pair_or_defensive_pair_injury_affects_goalie_team_markets")
    confidence_reason = None
    if not confirmed_goalie:
        confidence_reason = "goalie_unconfirmed_caps_moneyline_puckline_total_goalie_props"
    elif not confirmed_lines:
        confidence_reason = "confirmed_lines_missing_caps_skater_props"
    elif injury_risk >= 70:
        confidence_reason = "injury_uncertainty_caps_confidence"
    elif fatigue and fatigue >= 70:
        confidence_reason = "fatigue_schedule_spot_caps_confidence"

    return finalize_hockey_response(
        {
            "availability_score": round(clamp(availability), 2),
            "lineup_certainty_score": round(clamp(lineup_certainty), 2),
            "goalie_certainty_score": round(clamp(goalie_certainty), 2),
            "rest_travel_risk_score": round(clamp(rest_travel or 0.0), 2),
            "fatigue_risk_score": round(clamp(fatigue or 0.0), 2),
            "injury_risk_score": round(clamp(injury_risk), 2),
            "role_stability_score": round(clamp(role_stability or 0.0), 2),
            "confidence_cap_reason": confidence_reason,
            "missing_inputs": compact_list(missing_fields(source, AVAILABILITY_FIELDS), limit=20),
            "no_bet_reasons": compact_list(no_bet, limit=20),
            "injury_status_fabricated": False,
            "confirmed_goalie_fabricated": False,
            "confirmed_lines_fabricated": False,
        },
        source_payload=source,
    )

from __future__ import annotations

from typing import Any

from .baseball_impact_common import boolish, clamp, compact_list, finalize_baseball_response, missing_fields, score_from_range, weighted_average


AVAILABILITY_INPUTS = (
    "player_injury_status",
    "pitcher_injury_status",
    "catcher_status",
    "confirmed_starter",
    "opener_risk",
    "pitch_count_limit",
    "recent_pitch_count",
    "rest_days",
    "back_to_back_game",
    "doubleheader_context",
    "day_game_after_night_game",
    "travel_distance",
    "time_zone_change",
    "team_rest_days",
    "lineup_rest_risk",
    "bullpen_fatigue",
    "weather_delay_risk",
    "postponement_risk",
)


def _injury_risk(value: Any) -> tuple[float, str | None]:
    raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if raw in {"out", "il", "injured_list", "doubtful"}:
        return 95.0, "player_unavailable"
    if raw in {"questionable", "day_to_day", "gtd", "game_time_decision"}:
        return 68.0, "injury_uncertainty_caps_confidence"
    if raw in {"healthy", "active", "available", ""}:
        return 8.0, None
    return 35.0, "unknown_injury_status"


def evaluate_baseball_availability_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    player_risk, player_reason = _injury_risk(source.get("player_injury_status"))
    pitcher_risk, pitcher_reason = _injury_risk(source.get("pitcher_injury_status"))
    starter_certainty = 95.0 if boolish(source.get("confirmed_starter")) else 35.0 if source.get("confirmed_starter") is not None else 45.0
    if boolish(source.get("opener_risk")):
        starter_certainty = min(starter_certainty, 28.0)
    pitch_limit_score = score_from_range(source.get("pitch_count_limit"), low=55.0, high=105.0)
    recent_pitch = score_from_range(source.get("recent_pitch_count"), low=45.0, high=105.0)
    rest = score_from_range(source.get("rest_days"), low=2.0, high=6.0)
    workload = weighted_average(((100.0 - (rest if rest is not None else 60.0), 0.45), (recent_pitch, 0.35), (85.0 if pitch_limit_score is not None and pitch_limit_score < 45.0 else None, 0.65), (score_from_range(source.get("bullpen_fatigue"), low=0.0, high=100.0), 0.25))) or 0.0
    lineup_rest = weighted_average(((score_from_range(source.get("lineup_rest_risk"), low=0.0, high=100.0), 0.5), (35.0 if boolish(source.get("doubleheader_context")) else 0.0, 0.35), (30.0 if boolish(source.get("day_game_after_night_game")) else 0.0, 0.35), (20.0 if boolish(source.get("back_to_back_game")) else 0.0, 0.2)))
    travel = weighted_average(((score_from_range(source.get("travel_distance"), low=250.0, high=2600.0), 0.45), (score_from_range(source.get("time_zone_change"), low=0.0, high=3.0), 0.35), (100.0 - (score_from_range(source.get("team_rest_days"), low=0.0, high=3.0) or 80.0), 0.25)))
    weather_delay = max(score_from_range(source.get("weather_delay_risk"), low=0.0, high=100.0) or 0.0, score_from_range(source.get("postponement_risk"), low=0.0, high=100.0) or 0.0)
    role_stability = weighted_average(((starter_certainty, 0.55), (100.0 - workload, 0.35), (100.0 - (lineup_rest or 0.0), 0.25)))
    availability = weighted_average(((100.0 - max(player_risk, pitcher_risk), 0.75), (role_stability, 0.55), (100.0 - (travel or 0.0), 0.25), (100.0 - weather_delay, 0.35)))
    no_bet = []
    cap_reason = player_reason or pitcher_reason
    starter_explicitly_uncertain = source.get("confirmed_starter") not in (None, "") and starter_certainty < 50
    if starter_explicitly_uncertain or boolish(source.get("opener_risk")):
        no_bet.append("unconfirmed_starter_caps_pitcher_props_and_first_five")
        no_bet.append("unconfirmed_starter_caps_pitcher_prop_and_first_five_confidence")
        cap_reason = "starter_unconfirmed"
    if pitch_limit_score is not None and pitch_limit_score < 45:
        no_bet.append("pitch_count_limit_hard_warning_for_outs_and_strikeouts")
        no_bet.append("pitch_count_limit_caps_outs_and_strikeout_props")
        cap_reason = "pitch_count_limit"
    if weather_delay >= 60:
        no_bet.append("weather_delay_risk_can_break_pitcher_props")
        no_bet.append("weather_delay_breaks_pitcher_prop_confidence")
        cap_reason = "weather_delay_risk"
    if lineup_rest and lineup_rest >= 55:
        no_bet.append("doubleheader_or_day_after_night_caps_lineup_props")
    return finalize_baseball_response(
        {
            "availability_score": round(clamp(availability or 0.0), 2),
            "role_stability_score": round(clamp(role_stability or 0.0), 2),
            "starter_certainty_score": round(clamp(starter_certainty), 2),
            "workload_fatigue_score": round(clamp(workload), 2),
            "lineup_rest_risk_score": round(clamp(lineup_rest or 0.0), 2),
            "travel_schedule_risk_score": round(clamp(travel or 0.0), 2),
            "weather_delay_risk_score": round(clamp(weather_delay), 2),
            "confidence_cap_reason": cap_reason,
            "missing_inputs": compact_list(missing_fields(source, AVAILABILITY_INPUTS), limit=30),
            "no_bet_reasons": compact_list(no_bet, limit=12),
        },
        source_payload=source,
    )

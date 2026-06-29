from __future__ import annotations

from typing import Any

from .tennis_impact_common import categorical_score, clamp, compact_list, finalize_tennis_response, missing_fields, percent_score, score_from_range, weighted_average


SURFACE_INPUTS = (
    "surface",
    "court_speed_index",
    "indoor",
    "outdoor",
    "altitude",
    "temperature",
    "humidity",
    "wind_speed",
    "ball_type",
    "tournament_surface_speed_proxy",
    "player_a_surface_win_rate",
    "player_b_surface_win_rate",
    "player_a_surface_hold_rate",
    "player_b_surface_hold_rate",
    "player_a_surface_break_rate",
    "player_b_surface_break_rate",
    "grass_specific_context",
    "clay_specific_context",
    "hardcourt_specific_context",
    "indoor_hard_context",
    "sample_size_surface",
)


def _surface_base(value: Any) -> float | None:
    return categorical_score(value, {"grass": 72.0, "hard": 60.0, "indoor_hard": 68.0, "clay": 42.0, "carpet": 78.0})


def _bool_field(source: dict[str, Any], key: str) -> bool | None:
    if key not in source or source.get(key) in (None, ""):
        return None
    value = source.get(key)
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "indoor", "outdoor"}


def evaluate_tennis_surface_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    surface = _surface_base(source.get("surface"))
    court_speed = percent_score(source.get("court_speed_index")) or percent_score(source.get("tournament_surface_speed_proxy"))
    indoor = _bool_field(source, "indoor")
    outdoor = _bool_field(source, "outdoor")
    indoor_score = 65.0 if indoor else 48.0 if indoor is False or outdoor else None
    altitude = score_from_range(source.get("altitude"), low=0.0, high=5500.0)
    temp = score_from_range(source.get("temperature"), low=45.0, high=98.0)
    humidity = score_from_range(source.get("humidity"), low=20.0, high=90.0)
    wind = score_from_range(source.get("wind_speed"), low=0.0, high=28.0)
    ball = 55.0 if source.get("ball_type") not in (None, "", []) else None
    a_hold = score_from_range(source.get("player_a_surface_hold_rate"), low=0.62, high=0.88)
    b_hold = score_from_range(source.get("player_b_surface_hold_rate"), low=0.62, high=0.88)
    a_break = score_from_range(source.get("player_a_surface_break_rate"), low=0.12, high=0.35)
    b_break = score_from_range(source.get("player_b_surface_break_rate"), low=0.12, high=0.35)
    hold_break = weighted_average(((a_hold, 0.35), (b_hold, 0.35), (a_break, 0.25), (b_break, 0.25)))
    a_win = percent_score(source.get("player_a_surface_win_rate"))
    b_win = percent_score(source.get("player_b_surface_win_rate"))
    split_fit = weighted_average(((a_win, 0.25), (b_win, 0.25), (hold_break, 0.55)))
    style_context = weighted_average(
        (
            (percent_score(source.get("grass_specific_context")), 0.2),
            (percent_score(source.get("clay_specific_context")), 0.2),
            (percent_score(source.get("hardcourt_specific_context")), 0.2),
            (percent_score(source.get("indoor_hard_context")), 0.2),
        )
    )
    sample = source.get("sample_size_surface")
    sample_num = float(sample or 0.0) if str(sample or "").replace(".", "", 1).isdigit() else 0.0
    surface_fit = weighted_average(((surface, 0.25), (split_fit, 0.45), (style_context, 0.25), (court_speed, 0.2), (indoor_score, 0.15)))
    altitude_conditions = weighted_average(((altitude, 0.45), (temp, 0.2), (100.0 - (humidity or 50.0), 0.15), (100.0 - (wind or 0.0), 0.25)))
    total_modifier = weighted_average(((court_speed, 0.45), (surface, 0.35), (hold_break, 0.25), (indoor_score, 0.2), (altitude, 0.2), (100.0 - (wind or 0.0), 0.15)))
    tiebreak_modifier = weighted_average(((court_speed, 0.45), (surface, 0.35), (a_hold, 0.25), (b_hold, 0.25), (altitude, 0.2), (indoor_score, 0.15)))
    no_bet: list[str] = []
    if surface is None:
        no_bet.append("surface_missing_caps_surface_matchup")
    if court_speed is None:
        no_bet.append("court_speed_missing_no_court_speed_claim")
    if ball is None:
        no_bet.append("ball_type_missing_no_ball_type_claim")
    if sample_num and sample_num < 20:
        no_bet.append("surface_split_small_sample_capped")
    if altitude is not None:
        no_bet.append("altitude_modifies_ace_hold_tiebreak_only_when_supplied")
    return finalize_tennis_response(
        {
            "surface_fit_score": round(clamp(surface_fit or 0.0), 2),
            "court_speed_fit_score": round(clamp(court_speed or 0.0), 2),
            "indoor_outdoor_fit_score": round(clamp(indoor_score or 0.0), 2),
            "altitude_conditions_score": round(clamp(altitude_conditions or 0.0), 2),
            "surface_hold_break_modifier": round(clamp(hold_break or 0.0), 2),
            "total_games_surface_modifier": round(clamp(total_modifier or 0.0), 2),
            "tiebreak_surface_modifier": round(clamp(tiebreak_modifier or 0.0), 2),
            "court_speed_fabricated": False,
            "ball_type_fabricated": False,
            "weather_conditions_fabricated": False,
            "missing_inputs": compact_list(missing_fields(source, SURFACE_INPUTS), limit=35),
            "no_bet_reasons": compact_list(no_bet, limit=12),
        },
        source_payload=source,
    )

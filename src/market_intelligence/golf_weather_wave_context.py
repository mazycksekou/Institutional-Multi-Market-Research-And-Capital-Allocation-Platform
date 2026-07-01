from __future__ import annotations

from typing import Any

from .golf_impact_common import categorical_score, clamp, compact_list, finalize_golf_response, missing_fields, percent_score, score_from_range, weighted_average


WEATHER_WAVE_INPUTS = (
    "tee_time",
    "tee_wave",
    "round_number",
    "wind_speed",
    "wind_gust",
    "wind_direction",
    "rain_probability",
    "precipitation_intensity",
    "temperature",
    "humidity",
    "air_density_proxy",
    "morning_wave_conditions",
    "afternoon_wave_conditions",
    "weather_edge_by_wave",
    "course_drainage_context",
    "delay_risk",
    "suspension_risk",
    "wind_skill",
    "bad_weather_skill",
    "calm_weather_skill",
)


def _edge_score(value: Any) -> float | None:
    if value in (None, "", "not_supplied", "unknown"):
        return None
    return categorical_score(value, {"bad": 20.0, "negative": 30.0, "neutral": 50.0, "none": 50.0, "positive": 70.0, "good": 80.0, "strong": 90.0}, percent_score(value))


def evaluate_golf_weather_wave_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    wind = weighted_average(((score_from_range(source.get("wind_speed"), low=0.0, high=24.0), 0.55), (score_from_range(source.get("wind_gust"), low=5.0, high=34.0), 0.65)))
    rain = weighted_average(((percent_score(source.get("rain_probability")), 0.45), (score_from_range(source.get("precipitation_intensity"), low=0.0, high=1.0), 0.35)))
    temp = score_from_range(source.get("temperature"), low=45.0, high=95.0)
    wind_skill = percent_score(source.get("wind_skill"))
    bad_weather_skill = percent_score(source.get("bad_weather_skill"))
    calm_skill = percent_score(source.get("calm_weather_skill"))
    tee_wave = str(source.get("tee_wave") or "").strip().lower()
    wave_supplied = tee_wave not in {"", "unknown", "not_supplied", "none"}
    wave_edge = _edge_score(source.get("weather_edge_by_wave"))
    raw_wave_edge = str(source.get("weather_edge_by_wave") or "").strip().lower()
    if wave_edge is None and wave_supplied and raw_wave_edge in {"morning", "am", "early", "afternoon", "pm", "late"}:
        wave_edge = 72.0 if raw_wave_edge in {tee_wave, "am" if tee_wave == "morning" else "", "pm" if tee_wave == "afternoon" else ""} else 32.0
    morning = _edge_score(source.get("morning_wave_conditions"))
    afternoon = _edge_score(source.get("afternoon_wave_conditions"))
    wave_draw = weighted_average(((wave_edge, 0.65), (morning if tee_wave == "morning" else None, 0.35), (afternoon if tee_wave == "afternoon" else None, 0.35)))
    wind_fit = weighted_average(((100.0 - (wind or 50.0), 0.35), (wind_skill, 0.55), (bad_weather_skill if wind and wind >= 55 else calm_skill, 0.25)))
    delay = max(percent_score(source.get("delay_risk")) or 0.0, percent_score(source.get("suspension_risk")) or 0.0)
    scoring_modifier = weighted_average(((100.0 - (wind or 50.0), 0.5), (100.0 - (rain or 0.0), 0.25), (temp, 0.15), (wave_draw, 0.25), (percent_score(source.get("course_drainage_context")), 0.15)))
    round_modifier = weighted_average(((scoring_modifier, 0.55), (wave_draw, 0.45), (100.0 - delay, 0.35)))
    no_bet: list[str] = []
    if not wave_supplied:
        no_bet.append("tee_time_wave_missing_no_wave_draw_claim")
    if wave_supplied and wave_edge is None and morning is None and afternoon is None:
        no_bet.append("weather_by_wave_missing_no_wave_edge_claim")
    if wind and wind >= 55 and wind_skill is None:
        no_bet.append("wind_skill_missing_caps_wind_edge")
    if delay >= 55:
        no_bet.append("delay_or_suspension_risk_increases_volatility")
    return finalize_golf_response(
        {
            "weather_impact_score": round(clamp(weighted_average(((100.0 - (wind or 50.0), 0.35), (100.0 - (rain or 0.0), 0.2), (wind_fit, 0.35))) or 0.0), 2),
            "wave_draw_score": round(clamp(wave_draw or 0.0), 2),
            "wind_fit_score": round(clamp(wind_fit or 0.0), 2),
            "delay_risk_score": round(clamp(delay), 2),
            "scoring_condition_modifier": round(clamp(scoring_modifier or 0.0), 2),
            "round_score_modifier": round(clamp(round_modifier or 0.0), 2),
            "market_confidence_modifier": round(clamp(weighted_average(((round_modifier, 0.45), (100.0 - delay, 0.4))) or 0.0), 2),
            "tee_time_wave_fabricated": False,
            "weather_wave_edge_fabricated": False,
            "wind_skill_fabricated": False,
            "missing_inputs": compact_list(missing_fields(source, WEATHER_WAVE_INPUTS), limit=35),
            "no_bet_reasons": compact_list(no_bet, limit=12),
        },
        source_payload=source,
    )

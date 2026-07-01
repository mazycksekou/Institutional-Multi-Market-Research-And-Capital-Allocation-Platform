from __future__ import annotations

from typing import Any

from .baseball_impact_common import boolish, clamp, compact_list, finalize_baseball_response, missing_fields, score_from_range, weighted_average


PARK_WEATHER_UMPIRE_INPUTS = (
    "park_factor",
    "handedness_park_factor",
    "home_run_factor",
    "run_factor",
    "foul_territory_context",
    "altitude",
    "roof_status",
    "wind_speed",
    "wind_direction",
    "temperature",
    "humidity",
    "precipitation_risk",
    "air_density_proxy",
    "umpire_name",
    "umpire_zone_size_proxy",
    "umpire_k_rate_proxy",
    "umpire_walk_rate_proxy",
    "umpire_over_under_tendency_proxy",
)


def _wind_modifier(speed: Any, direction: Any) -> float | None:
    wind = score_from_range(speed, low=0.0, high=18.0)
    if wind is None:
        return None
    raw = str(direction or "").lower()
    if any(part in raw for part in ("out", "to_outfield", "out_to")):
        return clamp(50.0 + wind * 0.5)
    if any(part in raw for part in ("in", "from_outfield", "in_from")):
        return clamp(50.0 - wind * 0.45)
    return 50.0


def _factor(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if abs(number) <= 5:
        number *= 100.0
    return number


def evaluate_baseball_park_weather_umpire_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    roof = str(source.get("roof_status") or "").strip().lower()
    roof_closed = roof in {"closed", "dome", "retractable_closed"}
    park_run = weighted_average(((score_from_range(_factor(source.get("park_factor")), low=85.0, high=115.0), 0.45), (score_from_range(_factor(source.get("run_factor")), low=85.0, high=118.0), 0.65), (score_from_range(source.get("altitude"), low=0.0, high=5200.0), 0.25)))
    hr_env = weighted_average(((score_from_range(_factor(source.get("home_run_factor")), low=80.0, high=130.0), 0.75), (score_from_range(_factor(source.get("handedness_park_factor")), low=80.0, high=130.0), 0.35), (_wind_modifier(source.get("wind_speed"), source.get("wind_direction")), 0.45 if not roof_closed else 0.05), (score_from_range(source.get("temperature"), low=45.0, high=92.0), 0.25 if not roof_closed else 0.05)))
    weather_run = weighted_average(((_wind_modifier(source.get("wind_speed"), source.get("wind_direction")), 0.55 if not roof_closed else 0.05), (score_from_range(source.get("temperature"), low=45.0, high=92.0), 0.35 if not roof_closed else 0.05), (score_from_range(source.get("humidity"), low=20.0, high=85.0), 0.15), (score_from_range(source.get("air_density_proxy"), low=0.0, high=100.0), 0.2), (score_from_range(source.get("precipitation_risk"), low=0.0, high=100.0, inverse=True), 0.25 if not roof_closed else 0.05)))
    zone = score_from_range(source.get("umpire_zone_size_proxy"), low=0.0, high=100.0)
    ump_k = score_from_range(source.get("umpire_k_rate_proxy"), low=0.0, high=100.0)
    ump_walk = score_from_range(source.get("umpire_walk_rate_proxy"), low=0.0, high=100.0)
    ump_total = score_from_range(source.get("umpire_over_under_tendency_proxy"), low=0.0, high=100.0)
    umpire_zone = weighted_average(((zone, 0.55), (ump_k, 0.35), (100.0 - ump_walk if ump_walk is not None else None, 0.25)))
    total_market = weighted_average(((park_run, 0.55), (weather_run, 0.45), (ump_total, 0.35), (100.0 - (umpire_zone or 50.0), 0.2)))
    no_bet = []
    cap_reason = None
    if source.get("umpire_name") and umpire_zone is None and ump_total is None:
        cap_reason = "umpire_name_without_tendency_data"
        no_bet.append("umpire_tendency_missing")
        no_bet.append("umpire_name_without_tendency_data_no_zone_claim")
    if not roof_closed and source.get("precipitation_risk") not in (None, "") and (score_from_range(source.get("precipitation_risk"), low=0.0, high=100.0) or 0.0) >= 60:
        no_bet.append("weather_delay_risk_caps_pitcher_props")
        cap_reason = "weather_delay_risk"
    return finalize_baseball_response(
        {
            "park_run_environment_score": round(clamp(park_run or 0.0), 2),
            "home_run_environment_score": round(clamp(hr_env or 0.0), 2),
            "weather_run_modifier": round(clamp(weather_run or 0.0), 2),
            "pitcher_prop_weather_modifier": round(clamp(100.0 - (weather_run or 50.0)), 2),
            "batter_prop_weather_modifier": round(clamp(hr_env or weather_run or 0.0), 2),
            "umpire_zone_modifier": round(clamp(umpire_zone or 0.0), 2),
            "total_market_modifier": round(clamp(total_market or 0.0), 2),
            "roof_weather_uncertainty_reduced": bool(roof_closed),
            "confidence_cap_reason": cap_reason,
            "missing_inputs": compact_list(missing_fields(source, PARK_WEATHER_UMPIRE_INPUTS), limit=30),
            "no_bet_reasons": compact_list(no_bet, limit=10),
            "umpire_tendency_fabricated": False,
        },
        source_payload=source,
    )

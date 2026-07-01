from __future__ import annotations

from typing import Any

from .football_impact_schema import (
    clamp,
    compact_list,
    finalize_football_response,
    missing_fields,
    safe_float,
    score_from_range,
    weighted_average,
)


AVAILABILITY_INPUTS = (
    "injury_status",
    "practice_status",
    "snap_share_recent",
    "snap_share_trend",
    "route_share_recent",
    "route_share_trend",
    "carry_share_recent",
    "carry_share_trend",
    "target_share_recent",
    "target_share_trend",
    "offensive_line_continuity",
    "defensive_line_continuity",
    "starting_qb_status",
    "backup_qb_quality_proxy",
    "depth_chart_change",
    "short_week",
    "rest_days",
    "travel_distance",
    "altitude",
    "weather_risk",
    "wind_mph",
    "precipitation_risk",
    "temperature",
)


def _injury_risk(status: Any, practice_status: Any = None) -> tuple[float, str | None]:
    raw = str(status or "").strip().lower().replace("-", "_").replace(" ", "_")
    practice = str(practice_status or "").strip().lower().replace("-", "_").replace(" ", "_")
    if raw in {"out", "doubtful", "ir", "injured_reserve"}:
        return 95.0, "player_unavailable_or_doubtful"
    if raw in {"questionable", "game_time_decision"}:
        return 70.0, "injury_uncertainty_caps_confidence"
    if raw in {"probable", "limited"} or practice in {"limited", "dnp", "did_not_practice"}:
        return 42.0, "limited_practice_or_probable_status"
    if raw in {"healthy", "available", "active", ""}:
        return 8.0, None
    return 35.0, "unclear_injury_status"


def _qb_status_risk(status: Any) -> tuple[float, list[str]]:
    raw = str(status or "").strip().lower().replace("-", "_").replace(" ", "_")
    if raw in {"out", "backup_starting", "backup", "doubtful"}:
        return 92.0, ["starting_qb_change_market_wide_risk"]
    if raw in {"questionable", "game_time_decision"}:
        return 74.0, ["starting_qb_uncertainty_market_wide_risk"]
    if raw in {"healthy", "active", "confirmed"}:
        return 5.0, []
    return (35.0, ["starting_qb_status_unclear"]) if raw else (0.0, [])


def evaluate_football_availability_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    injury_risk, injury_reason = _injury_risk(source.get("injury_status"), source.get("practice_status"))
    qb_risk, qb_flags = _qb_status_risk(source.get("starting_qb_status"))
    snap = score_from_range(source.get("snap_share_recent"), low=0.10, high=0.95)
    route = score_from_range(source.get("route_share_recent"), low=0.05, high=0.95)
    carry = score_from_range(source.get("carry_share_recent"), low=0.04, high=0.70)
    target = score_from_range(source.get("target_share_recent"), low=0.03, high=0.32)
    snap_trend = safe_float(source.get("snap_share_trend"), 0.0) or 0.0
    route_trend = safe_float(source.get("route_share_trend"), 0.0) or 0.0
    trend_stability = clamp(100.0 - (abs(snap_trend) + abs(route_trend)) * 220.0)
    snap_stability = weighted_average(((snap, 0.7), (trend_stability, 0.55)))
    role_stability = weighted_average(((snap_stability, 0.7), (route, 0.35), (carry, 0.25), (target, 0.25)))
    depth_change_raw = str(source.get("depth_chart_change") or source.get("depth_chart_status") or "").strip().lower().replace(" ", "_")
    depth_chart_risk = 78.0 if depth_change_raw in {"starter_out", "demotion", "rotation_uncertain", "new_starter"} else 35.0 if depth_change_raw else 0.0
    ol_continuity = score_from_range(source.get("offensive_line_continuity"), low=0.0, high=100.0)
    dl_continuity = score_from_range(source.get("defensive_line_continuity"), low=0.0, high=100.0)
    rest_days = safe_float(source.get("rest_days"))
    rest_score = score_from_range(rest_days, low=3.0, high=8.0) if rest_days is not None else None
    short_week_penalty = 28.0 if str(source.get("short_week")).strip().lower() in {"1", "true", "yes"} else 0.0
    travel_risk = score_from_range(source.get("travel_distance"), low=250.0, high=2500.0)
    altitude_risk = score_from_range(source.get("altitude"), low=500.0, high=5200.0)
    rest_travel_risk = weighted_average(
        (
            (100.0 - rest_score if rest_score is not None else None, 0.55),
            (short_week_penalty, 0.55),
            (travel_risk, 0.35),
            (altitude_risk, 0.2),
        )
    )
    wind = safe_float(source.get("wind_mph"), 0.0) or 0.0
    weather_risk = score_from_range(source.get("weather_risk"), low=0.0, high=100.0) or 0.0
    wind_risk = score_from_range(wind, low=8.0, high=24.0) or 0.0
    precip = score_from_range(source.get("precipitation_risk"), low=0.0, high=100.0) or 0.0
    temp = safe_float(source.get("temperature"))
    temp_risk = 0.0
    if temp is not None:
        temp_risk = max(score_from_range(25.0 - temp, low=0.0, high=35.0) or 0.0, score_from_range(temp - 85.0, low=0.0, high=25.0) or 0.0)
    weather_adjustment = weighted_average(((weather_risk, 0.35), (wind_risk, 0.85), (precip, 0.45), (temp_risk, 0.2)))
    availability = weighted_average(
        (
            (100.0 - injury_risk, 0.9),
            (100.0 - qb_risk, 0.75),
            (100.0 - depth_chart_risk, 0.35),
            (snap_stability, 0.5),
            (role_stability, 0.4),
            (ol_continuity, 0.25),
            (dl_continuity, 0.2),
            (100.0 - (rest_travel_risk or 0.0), 0.35),
        )
    )
    cap_reason = injury_reason
    if qb_flags:
        cap_reason = qb_flags[0]
    elif (snap_stability or 100.0) < 45.0:
        cap_reason = "snap_share_instability_caps_prop_confidence"
    elif (weather_adjustment or 0.0) >= 65.0:
        cap_reason = "weather_wind_caps_passing_kicking_total_confidence"

    flags = compact_list(
        [
            injury_reason,
            *qb_flags,
            "snap_share_instability" if (snap_stability or 100.0) < 45.0 else None,
            "short_week_rest_travel_risk" if (rest_travel_risk or 0.0) >= 45.0 else None,
            "wind_impacts_passing_kicking_totals" if wind >= 15.0 else None,
            "depth_chart_change_role_risk" if depth_chart_risk >= 65.0 else None,
            "offensive_line_continuity_risk" if ol_continuity is not None and ol_continuity < 45.0 else None,
        ],
        limit=12,
    )
    no_bet = compact_list(
        [
            injury_reason if injury_risk >= 70.0 else None,
            *qb_flags,
            "snap_or_route_role_instability" if (snap_stability or 100.0) < 45.0 or (role_stability or 100.0) < 45.0 else None,
            "severe_wind_weather_caps_market_confidence" if (weather_adjustment or 0.0) >= 65.0 else None,
        ],
        limit=12,
    )

    return finalize_football_response(
        {
            "availability_score": round(clamp(availability or 0.0), 2),
            "snap_stability_score": round(clamp(snap_stability or 0.0), 2),
            "role_stability_score": round(clamp(role_stability or 0.0), 2),
            "injury_risk_score": round(clamp(injury_risk), 2),
            "depth_chart_risk_score": round(clamp(depth_chart_risk), 2),
            "rest_travel_risk_score": round(clamp(rest_travel_risk or 0.0), 2),
            "weather_adjustment_score": round(clamp(weather_adjustment or 0.0), 2),
            "wind_risk_score": round(clamp(wind_risk), 2),
            "starting_qb_market_risk_score": round(clamp(qb_risk), 2),
            "confidence_cap_reason": cap_reason,
            "market_wide_risk_flags": flags,
            "no_bet_reasons": no_bet,
            "missing_inputs": compact_list(missing_fields(source, AVAILABILITY_INPUTS), limit=35),
        },
        source_payload=source,
    )

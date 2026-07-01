from __future__ import annotations

from typing import Any

from .tennis_impact_common import boolish, clamp, compact_list, finalize_tennis_response, missing_fields, percent_score, score_from_range, weighted_average


AVAILABILITY_INPUTS = (
    "injury_status",
    "medical_timeout_recent",
    "retirement_history",
    "withdrawal_risk",
    "recent_match_minutes",
    "recent_sets_played",
    "recent_tiebreaks_played",
    "matches_last_7_days",
    "matches_last_14_days",
    "back_to_back_match",
    "rest_days",
    "travel_distance",
    "time_zone_change",
    "altitude_change",
    "surface_change_recent",
    "tournament_change_recent",
    "five_set_match_recent",
    "heat_fatigue_risk",
    "cramping_history",
    "age",
    "workload_risk_proxy",
)


def _injury(value: Any) -> tuple[float, str | None]:
    raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if raw in {"out", "withdrawn", "retired", "injured", "major_injury"}:
        return 95.0, "injury_retirement_uncertainty_caps_all_markets"
    if raw in {"questionable", "limited", "uncertain", "illness", "day_to_day"}:
        return 70.0, "injury_uncertainty_caps_all_markets"
    if raw in {"healthy", "active", "available", ""}:
        return 5.0, None
    return 35.0, "unknown_injury_status"


def evaluate_tennis_availability_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    injury, injury_reason = _injury(source.get("injury_status"))
    retirement = max(
        percent_score(source.get("withdrawal_risk")) or 0.0,
        percent_score(source.get("retirement_history")) or 0.0,
        80.0 if boolish(source.get("medical_timeout_recent")) else 0.0,
    )
    fatigue = weighted_average(
        (
            (score_from_range(source.get("recent_match_minutes"), low=60.0, high=240.0), 0.35),
            (score_from_range(source.get("recent_sets_played"), low=2.0, high=9.0), 0.3),
            (score_from_range(source.get("recent_tiebreaks_played"), low=0.0, high=4.0), 0.2),
            (score_from_range(source.get("workload_risk_proxy"), low=0.0, high=100.0), 0.35),
            (70.0 if boolish(source.get("five_set_match_recent")) else None, 0.35),
            (percent_score(source.get("heat_fatigue_risk")), 0.25),
            (65.0 if boolish(source.get("cramping_history")) else None, 0.25),
        )
    )
    schedule = weighted_average(
        (
            (score_from_range(source.get("matches_last_7_days"), low=1.0, high=5.0), 0.35),
            (score_from_range(source.get("matches_last_14_days"), low=2.0, high=9.0), 0.25),
            (70.0 if boolish(source.get("back_to_back_match")) else None, 0.35),
            (score_from_range(source.get("rest_days"), low=0.0, high=6.0, inverse=True), 0.25),
        )
    )
    travel = weighted_average(
        (
            (score_from_range(source.get("travel_distance"), low=300.0, high=6500.0), 0.35),
            (score_from_range(source.get("time_zone_change"), low=0.0, high=8.0), 0.35),
            (score_from_range(source.get("altitude_change"), low=0.0, high=5000.0), 0.2),
        )
    )
    transition = weighted_average(((65.0 if boolish(source.get("surface_change_recent")) else None, 0.45), (45.0 if boolish(source.get("tournament_change_recent")) else None, 0.25)))
    availability = weighted_average(((100.0 - injury, 0.65), (100.0 - retirement, 0.75), (100.0 - (fatigue or 0.0), 0.35), (100.0 - (schedule or 0.0), 0.25), (100.0 - (travel or 0.0), 0.2), (100.0 - (transition or 0.0), 0.2)))
    no_bet: list[str] = []
    cap = injury_reason
    if retirement >= 55:
        no_bet.append("retirement_risk_hard_warning")
        cap = "retirement_risk_caps_all_markets"
    if boolish(source.get("five_set_match_recent")):
        no_bet.append("recent_five_set_match_affects_fatigue")
    if transition:
        no_bet.append("surface_change_creates_timing_risk")
    if fatigue and fatigue >= 65:
        no_bet.append("fatigue_load_increases_volatility")
    return finalize_tennis_response(
        {
            "availability_score": round(clamp(availability or 0.0), 2),
            "injury_risk_score": round(clamp(injury), 2),
            "retirement_risk_score": round(clamp(retirement), 2),
            "fatigue_score": round(clamp(fatigue or 0.0), 2),
            "schedule_load_score": round(clamp(schedule or 0.0), 2),
            "travel_adjustment_score": round(clamp(travel or 0.0), 2),
            "surface_transition_risk_score": round(clamp(transition or 0.0), 2),
            "confidence_cap_reason": cap,
            "injury_status_fabricated": False,
            "retirement_risk_fabricated": False,
            "missing_inputs": compact_list(missing_fields(source, AVAILABILITY_INPUTS), limit=35),
            "no_bet_reasons": compact_list(no_bet, limit=12),
        },
        source_payload=source,
    )

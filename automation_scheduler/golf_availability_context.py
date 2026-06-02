from __future__ import annotations

from typing import Any

from .golf_impact_common import boolish, clamp, compact_list, finalize_golf_response, missing_fields, percent_score, score_from_range, weighted_average


AVAILABILITY_INPUTS = (
    "injury_status",
    "withdrawal_risk",
    "recent_withdrawal",
    "illness_context",
    "swing_change_context",
    "equipment_change_context",
    "caddie_change_context",
    "travel_distance",
    "time_zone_change",
    "consecutive_weeks_played",
    "previous_week_rounds_played",
    "previous_week_contention",
    "major_after_effect",
    "rest_days",
    "altitude_context",
    "heat_fatigue_risk",
)


def _injury(value: Any) -> tuple[float, str | None]:
    raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if raw in {"withdrawn", "out", "injured", "major_injury"}:
        return 95.0, "injury_or_withdrawal_uncertainty_caps_all_markets"
    if raw in {"questionable", "uncertain", "limited", "illness", "day_to_day"}:
        return 68.0, "injury_uncertainty_caps_all_markets"
    if raw in {"healthy", "active", "available", ""}:
        return 5.0, None
    return 35.0, "unknown_injury_status"


def evaluate_golf_availability_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    injury_risk, injury_reason = _injury(source.get("injury_status") or source.get("illness_context"))
    withdrawal = max(percent_score(source.get("withdrawal_risk")) or 0.0, 85.0 if boolish(source.get("recent_withdrawal")) else 0.0)
    travel = weighted_average(((score_from_range(source.get("travel_distance"), low=300.0, high=6500.0), 0.35), (score_from_range(source.get("time_zone_change"), low=0.0, high=8.0), 0.35), (score_from_range(source.get("consecutive_weeks_played"), low=1.0, high=6.0), 0.45), (score_from_range(source.get("rest_days"), low=1.0, high=10.0, inverse=True), 0.25)))
    schedule = weighted_average(((score_from_range(source.get("previous_week_rounds_played"), low=0.0, high=4.0), 0.25), (65.0 if boolish(source.get("previous_week_contention")) else 0.0, 0.3), (45.0 if boolish(source.get("major_after_effect")) else 0.0, 0.2)))
    changes = weighted_average(((55.0 if source.get("swing_change_context") not in (None, "", False) else None, 0.35), (45.0 if source.get("equipment_change_context") not in (None, "", False) else None, 0.25), (45.0 if source.get("caddie_change_context") not in (None, "", False) else None, 0.25)))
    heat_altitude = weighted_average(((percent_score(source.get("heat_fatigue_risk")), 0.35), (percent_score(source.get("altitude_context")), 0.2)))
    availability = weighted_average(((100.0 - injury_risk, 0.65), (100.0 - withdrawal, 0.75), (100.0 - (travel or 0.0), 0.3), (100.0 - (schedule or 0.0), 0.25), (100.0 - (changes or 0.0), 0.2), (100.0 - (heat_altitude or 0.0), 0.15)))
    no_bet: list[str] = []
    cap_reason = injury_reason
    if withdrawal >= 60:
        no_bet.append("withdrawal_risk_hard_warning")
        cap_reason = "withdrawal_risk_caps_all_markets"
    if changes:
        no_bet.append("swing_equipment_caddie_change_uncertainty_modifier_only")
    if travel and travel >= 65:
        no_bet.append("travel_fatigue_increases_volatility")
    return finalize_golf_response(
        {
            "availability_score": round(clamp(availability or 0.0), 2),
            "withdrawal_risk_score": round(clamp(withdrawal), 2),
            "injury_risk_score": round(clamp(injury_risk), 2),
            "travel_fatigue_score": round(clamp(travel or 0.0), 2),
            "schedule_load_score": round(clamp(schedule or 0.0), 2),
            "change_uncertainty_score": round(clamp(changes or 0.0), 2),
            "confidence_cap_reason": cap_reason,
            "injury_status_fabricated": False,
            "withdrawal_risk_fabricated": False,
            "missing_inputs": compact_list(missing_fields(source, AVAILABILITY_INPUTS), limit=30),
            "no_bet_reasons": compact_list(no_bet, limit=12),
        },
        source_payload=source,
    )

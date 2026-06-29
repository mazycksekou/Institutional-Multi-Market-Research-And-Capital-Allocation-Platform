from __future__ import annotations

from typing import Any

from .soccer_impact_common import boolish, clamp, compact_list, finalize_soccer_response, missing_fields, score_from_range, weighted_average


LINEUP_FIELDS = ("confirmed_lineup", "starting_xi_stability", "starting_goalkeeper_confirmed", "minutes_projection", "rotation_risk", "days_rest")


def evaluate_soccer_lineup_availability_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    confirmed_lineup = boolish(source.get("confirmed_lineup"))
    projected_lineup = boolish(source.get("projected_lineup"))
    keeper_confirmed = boolish(source.get("starting_goalkeeper_confirmed") if "starting_goalkeeper_confirmed" in source else source.get("confirmed_starter"))
    lineup_certainty = weighted_average(((95.0 if confirmed_lineup else 62.0 if projected_lineup else 28.0, 0.55), (score_from_range(source.get("starting_xi_stability"), low=0, high=1), 0.45))) or 0.0
    injury_risk = weighted_average(((80.0 if source.get("key_attacker_absent") else 15.0, 0.35), (80.0 if source.get("key_defender_absent") else 15.0, 0.35), (score_from_range(source.get("injury_statuses"), low=0, high=1), 0.25), (score_from_range(source.get("suspension_context"), low=0, high=1), 0.25)))
    rotation = weighted_average(((score_from_range(source.get("rotation_risk"), low=0, high=1), 0.45), (score_from_range(source.get("fixture_congestion"), low=0, high=1), 0.35), (80.0 if boolish(source.get("midweek_match")) else 20.0, 0.25), (score_from_range(source.get("cup_rotation_context"), low=0, high=1), 0.25))) or 0.0
    minutes_conf = weighted_average(((score_from_range(source.get("minutes_projection"), low=0, high=90), 0.55), (score_from_range(source.get("substitution_risk"), low=0, high=1, inverse=True), 0.45), (100.0 - rotation, 0.25))) or 0.0
    rest_travel = weighted_average(((score_from_range(source.get("days_rest") if source.get("days_rest") is not None else source.get("rest_days"), low=2, high=8, inverse=True), 0.35), (score_from_range(source.get("travel_distance"), low=0, high=5000), 0.25), (score_from_range(source.get("time_zone_change"), low=0, high=4), 0.2), (score_from_range(source.get("altitude"), low=0, high=7000), 0.15), (70.0 if boolish(source.get("international_break_return")) else 20.0, 0.25))) or 0.0
    priority_risk = weighted_average(((score_from_range(source.get("competition_priority"), low=0, high=1, inverse=True), 0.45), (score_from_range(source.get("fixture_priority"), low=0, high=1, inverse=True), 0.35), (score_from_range(source.get("cup_rotation_context"), low=0, high=1), 0.35))) or 0.0
    tactical_continuity = weighted_average(((lineup_certainty, 0.45), (100.0 - rotation, 0.35), (score_from_range(source.get("starting_xi_stability"), low=0, high=1), 0.35))) or 0.0
    availability = weighted_average(((lineup_certainty, 0.35), (100.0 - (injury_risk or 0.0), 0.3), (100.0 - rotation, 0.2), (100.0 - rest_travel, 0.15))) or 0.0
    no_bet = []
    if not confirmed_lineup:
        no_bet.append("confirmed_lineup_missing_caps_player_props_tactical_confidence")
    if not keeper_confirmed:
        no_bet.append("confirmed_goalkeeper_missing_caps_team_total_confidence")
    if rotation >= 65:
        no_bet.append("rotation_risk_affects_player_and_team_markets")
    if injury_risk and injury_risk >= 60:
        no_bet.append("injury_or_suspension_context_affects_market_confidence")
    confidence_reason = "confirmed_lineup_missing_caps_player_tactical_confidence" if not confirmed_lineup else "goalkeeper_confirmation_missing_caps_team_total_confidence" if not keeper_confirmed else "rotation_or_fixture_congestion_cap" if rotation >= 65 else None
    return finalize_soccer_response(
        {
            "lineup_certainty_score": round(clamp(lineup_certainty), 2),
            "availability_score": round(clamp(availability), 2),
            "rotation_risk_score": round(clamp(rotation), 2),
            "minutes_projection_confidence": round(clamp(minutes_conf), 2),
            "tactical_continuity_score": round(clamp(tactical_continuity), 2),
            "rest_travel_risk_score": round(clamp(rest_travel), 2),
            "competition_priority_risk": round(clamp(priority_risk), 2),
            "confidence_cap_reason": confidence_reason,
            "missing_inputs": compact_list(missing_fields(source, LINEUP_FIELDS), limit=20),
            "no_bet_reasons": compact_list(no_bet, limit=25),
            "lineup_fabricated": False,
            "injury_status_fabricated": False,
            "confirmed_goalkeeper_fabricated": False,
        },
        source_payload=source,
    )

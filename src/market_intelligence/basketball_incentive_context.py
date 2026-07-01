from __future__ import annotations

from typing import Any

from .basketball_player_impact_common import (
    boolish,
    clamp,
    compact_list,
    finalize_safe_response,
    missing_fields,
    present_fields,
    safe_float,
    score_from_range,
    weighted_average,
)


INCENTIVE_INPUTS = (
    "contract_year",
    "upcoming_free_agent",
    "extension_eligible",
    "bonus_thresholds",
    "award_eligibility",
    "all_nba_incentive",
    "games_played_incentive",
    "minutes_incentive",
    "points_incentive",
    "rebounds_incentive",
    "assists_incentive",
    "threes_incentive",
    "defensive_award_incentive",
    "playoff_race_context",
    "seeding_motivation",
    "trade_showcase_risk",
    "public_narrative_pressure",
    "coach_statement_context",
    "team_motivation_context",
)


def _threshold_pressure(value: Any) -> float | None:
    if value in (None, "", []):
        return None
    if isinstance(value, dict):
        distance = safe_float(value.get("distance_to_threshold"))
        if distance is not None:
            return clamp(100.0 - abs(distance) * 20.0)
        return 65.0
    if isinstance(value, list):
        return clamp(min(len(value), 4) * 22.0)
    if boolish(value):
        return 62.0
    return 0.0


def evaluate_incentive_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    present = present_fields(source, INCENTIVE_INPUTS)
    missing = missing_fields(source, INCENTIVE_INPUTS)
    if not present:
        return finalize_safe_response(
            {
                "incentive_context_score": 0.0,
                "incentive_usage_pressure": 0.0,
                "incentive_minutes_pressure": 0.0,
                "incentive_stat_chase_risk": 0.0,
                "incentive_team_alignment_score": 0.0,
                "incentive_market_relevance": "unknown",
                "incentive_warning_flags": ["incentive_data_unknown"],
                "incentive_status": "unknown",
                "incentive_missing_inputs": list(INCENTIVE_INPUTS),
            },
            source_payload=source,
        )

    contract_pressure = weighted_average(
        (
            (75.0 if boolish(source.get("contract_year")) else 0.0, 0.5),
            (80.0 if boolish(source.get("upcoming_free_agent")) else 0.0, 0.65),
            (68.0 if boolish(source.get("extension_eligible")) else 0.0, 0.45),
            (_threshold_pressure(source.get("bonus_thresholds")), 0.7),
            (_threshold_pressure(source.get("award_eligibility")), 0.55),
            (_threshold_pressure(source.get("all_nba_incentive")), 0.7),
        )
    ) or 0.0
    minutes_pressure = weighted_average(
        (
            (_threshold_pressure(source.get("games_played_incentive")), 0.7),
            (_threshold_pressure(source.get("minutes_incentive")), 0.8),
            (score_from_range(source.get("seeding_motivation"), low=0.0, high=100.0), 0.5),
            (score_from_range(source.get("team_motivation_context"), low=0.0, high=100.0), 0.45),
        )
    ) or 0.0
    stat_pressure = weighted_average(
        (
            (_threshold_pressure(source.get("points_incentive")), 0.75),
            (_threshold_pressure(source.get("rebounds_incentive")), 0.6),
            (_threshold_pressure(source.get("assists_incentive")), 0.6),
            (_threshold_pressure(source.get("threes_incentive")), 0.55),
            (_threshold_pressure(source.get("defensive_award_incentive")), 0.55),
            (score_from_range(source.get("public_narrative_pressure"), low=0.0, high=100.0), 0.35),
            (score_from_range(source.get("trade_showcase_risk"), low=0.0, high=100.0), 0.45),
        )
    ) or 0.0
    trade_showcase_score = score_from_range(source.get("trade_showcase_risk"), low=0.0, high=100.0)
    team_alignment = weighted_average(
        (
            (score_from_range(source.get("playoff_race_context"), low=0.0, high=100.0), 0.65),
            (score_from_range(source.get("seeding_motivation"), low=0.0, high=100.0), 0.6),
            (score_from_range(source.get("team_motivation_context"), low=0.0, high=100.0), 0.55),
            ((100.0 - trade_showcase_score) if trade_showcase_score is not None else None, 0.35),
        )
    ) or 0.0
    total = weighted_average(
        (
            (contract_pressure, 0.4),
            (minutes_pressure, 0.55),
            (stat_pressure, 0.6),
            (team_alignment, 0.35),
        )
    ) or 0.0

    flags: list[str] = []
    if stat_pressure >= 65.0:
        flags.append("stat_chase_risk")
    if minutes_pressure >= 65.0:
        flags.append("minutes_incentive_pressure")
    if contract_pressure >= 65.0:
        flags.append("contract_or_award_pressure")
    if team_alignment < 35.0 and (stat_pressure >= 55.0 or contract_pressure >= 60.0):
        flags.append("player_incentive_may_conflict_with_team_market")
    if not flags:
        flags.append("incentive_context_modifier_only")

    if stat_pressure >= 55.0 and team_alignment < 45.0:
        relevance = "props_high_team_markets_lower_confidence"
    elif stat_pressure >= 55.0:
        relevance = "props"
    elif team_alignment >= 60.0:
        relevance = "team_markets"
    else:
        relevance = "low"

    return finalize_safe_response(
        {
            "incentive_context_score": round(clamp(total), 2),
            "incentive_usage_pressure": round(clamp(max(contract_pressure, stat_pressure)), 2),
            "incentive_minutes_pressure": round(clamp(minutes_pressure), 2),
            "incentive_stat_chase_risk": round(clamp(stat_pressure), 2),
            "incentive_team_alignment_score": round(clamp(team_alignment), 2),
            "incentive_market_relevance": relevance,
            "incentive_warning_flags": compact_list(flags, limit=10),
            "incentive_status": "partial" if len(present) < 5 else "ok",
            "incentive_missing_inputs": compact_list(missing, limit=25),
        },
        source_payload=source,
    )

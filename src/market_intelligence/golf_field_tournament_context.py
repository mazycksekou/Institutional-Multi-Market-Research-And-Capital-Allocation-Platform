from __future__ import annotations

from typing import Any

from .golf_impact_common import boolish, clamp, compact_list, finalize_golf_response, missing_fields, percent_score, score_from_range, weighted_average


FIELD_TOURNAMENT_INPUTS = (
    "field_size",
    "field_strength",
    "world_ranking_field_strength_proxy",
    "top_20_field_count",
    "cut_rule",
    "cut_line_projection",
    "no_cut_event",
    "limited_field_event",
    "major_championship",
    "elevated_event",
    "opposite_field_event",
    "team_event",
    "match_play_event",
    "stableford_event",
    "defending_champion",
    "debut_in_event",
    "home_country_context",
    "travel_distance",
    "time_zone_change",
    "previous_week_finish",
    "consecutive_weeks_played",
)


def evaluate_golf_field_tournament_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    strength = weighted_average(((percent_score(source.get("field_strength")), 0.55), (percent_score(source.get("world_ranking_field_strength_proxy")), 0.45), (score_from_range(source.get("top_20_field_count"), low=0.0, high=25.0), 0.35)))
    format_score = weighted_average(
        (
            (90.0 if boolish(source.get("major_championship")) else None, 0.25),
            (75.0 if boolish(source.get("elevated_event")) else None, 0.2),
            (30.0 if boolish(source.get("opposite_field_event")) else None, 0.15),
            (35.0 if boolish(source.get("team_event")) else None, 0.2),
            (35.0 if boolish(source.get("match_play_event")) else None, 0.2),
            (35.0 if boolish(source.get("stableford_event")) else None, 0.2),
            (score_from_range(source.get("field_size"), low=60.0, high=156.0), 0.2),
        )
    )
    cut_rule_score = 100.0 if boolish(source.get("no_cut_event")) else 65.0 if source.get("cut_rule") not in (None, "") else 25.0
    travel = weighted_average(((score_from_range(source.get("travel_distance"), low=300.0, high=6500.0), 0.35), (score_from_range(source.get("time_zone_change"), low=0.0, high=8.0), 0.35), (score_from_range(source.get("consecutive_weeks_played"), low=1.0, high=6.0), 0.45), (score_from_range(source.get("previous_week_finish"), low=60.0, high=1.0), 0.15)))
    cut_risk = weighted_average(((100.0 - cut_rule_score, 0.45), (strength, 0.3), (travel, 0.25)))
    top_finish = weighted_average(((100.0 - (strength or 50.0), 0.35), (format_score, 0.25), (100.0 - (travel or 0.0), 0.2)))
    outright = weighted_average(((100.0 - (strength or 50.0), 0.35), (format_score, 0.25), (100.0 - (travel or 0.0), 0.15)))
    no_bet: list[str] = []
    if boolish(source.get("no_cut_event")):
        no_bet.append("no_cut_event_disables_make_miss_cut_logic")
    if boolish(source.get("match_play_event")) or boolish(source.get("team_event")) or boolish(source.get("stableford_event")):
        no_bet.append("unsupported_format_requires_market_specific_review")
    if source.get("field_strength") in (None, "") and source.get("world_ranking_field_strength_proxy") in (None, ""):
        no_bet.append("field_strength_missing_caps_outright_top_finish_confidence")
    if travel and travel >= 65:
        no_bet.append("travel_consecutive_start_fatigue_volatility")
    return finalize_golf_response(
        {
            "field_strength_score": round(clamp(strength or 0.0), 2),
            "tournament_format_score": round(clamp(format_score or 0.0), 2),
            "cut_rule_context_score": round(clamp(cut_rule_score), 2),
            "cut_risk_modifier": round(clamp(cut_risk or 0.0), 2),
            "top_finish_market_modifier": round(clamp(top_finish or 0.0), 2),
            "outright_market_modifier": round(clamp(outright or 0.0), 2),
            "travel_fatigue_risk_score": round(clamp(travel or 0.0), 2),
            "unsupported_format": boolish(source.get("match_play_event")) or boolish(source.get("team_event")) or boolish(source.get("stableford_event")),
            "missing_inputs": compact_list(missing_fields(source, FIELD_TOURNAMENT_INPUTS), limit=30),
            "no_bet_reasons": compact_list(no_bet, limit=12),
        },
        source_payload=source,
    )

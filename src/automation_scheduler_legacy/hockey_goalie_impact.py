from __future__ import annotations

from typing import Any

from .hockey_impact_common import (
    boolish,
    clamp,
    compact_list,
    finalize_hockey_response,
    missing_fields,
    score_centered,
    score_from_range,
    weighted_average,
)


GOALIE_FIELDS = (
    "confirmed_starter",
    "save_percentage",
    "expected_goals_against",
    "goals_saved_above_expected_proxy",
    "team_defensive_xg_against",
    "opponent_shot_volume",
)


def evaluate_hockey_goalie_impact(
    row: dict[str, Any] | None = None,
    *,
    goalie_level_allowed: bool = False,
) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    if not source:
        return finalize_hockey_response(
            {
                "goalie_level_allowed": False,
                "goalie_impact_score": 0.0,
                "starter_certainty_score": 0.0,
                "goalie_prop_relevance": 0.0,
                "team_market_goalie_modifier": 0.0,
                "total_market_goalie_modifier": 0.0,
                "missing_goalie_inputs": list(GOALIE_FIELDS),
                "no_bet_reasons": ["missing_goalie_context_caps_goalie_team_markets"],
                "gsax_fabricated": False,
            },
            source_payload=source,
        )
    confirmed = boolish(source.get("confirmed_starter") if "confirmed_starter" in source else source.get("confirmed_goalie"))
    projected = boolish(source.get("projected_starter") if "projected_starter" in source else source.get("projected_goalie"))
    starter_certainty = 95.0 if confirmed else 62.0 if projected else 28.0
    save_score = score_centered(source.get("save_percentage"), center=0.905, span=0.045)
    recent_save_score = score_centered(source.get("recent_save_percentage"), center=0.905, span=0.055)
    gsax_score = score_centered(source.get("goals_saved_above_expected_proxy"), center=0.0, span=18.0)
    high_danger = score_centered(source.get("high_danger_save_percentage"), center=0.81, span=0.08)
    rebound_control = score_from_range(source.get("rebound_control_proxy"), low=0, high=1)
    shot_quality = weighted_average(
        (
            (gsax_score, 0.75),
            (high_danger, 0.55),
            (rebound_control, 0.35),
            (score_from_range(source.get("expected_goals_against"), low=1.6, high=4.0, inverse=True), 0.35),
            (save_score, 0.2),
        )
    )
    workload_fatigue = weighted_average(
        (
            (score_from_range(source.get("workload_recent_starts"), low=0, high=8), 0.35),
            (score_from_range(source.get("shots_faced_recent"), low=22, high=42), 0.35),
            (80.0 if boolish(source.get("back_to_back_start")) else 20.0, 0.4),
            (score_from_range(source.get("rest_days"), low=0, high=5, inverse=True), 0.3),
        )
    )
    fatigue_safe = 100.0 - clamp(workload_fatigue or 0.0)
    goalie_impact = weighted_average(((starter_certainty, 0.3), (shot_quality, 0.45), (fatigue_safe, 0.15), (save_score, 0.1))) or 0.0
    goalie_prop_relevance = weighted_average(
        (
            (starter_certainty, 0.45),
            (score_from_range(source.get("opponent_shot_volume"), low=24, high=40), 0.45),
            (score_from_range(source.get("team_defensive_xg_against"), low=1.6, high=4.0), 0.25),
            (100.0 - clamp(workload_fatigue or 0.0), 0.2),
        )
    )
    team_modifier = weighted_average(((starter_certainty, 0.45), (shot_quality, 0.65), (fatigue_safe, 0.25))) or 0.0
    total_modifier = weighted_average(
        (
            (100.0 - clamp(shot_quality or 0.0), 0.35),
            (score_from_range(source.get("opponent_xg"), low=1.8, high=4.2), 0.35),
            (score_from_range(source.get("team_high_danger_against"), low=5, high=17), 0.25),
            (clamp(workload_fatigue or 0.0), 0.2),
        )
    )
    missing = missing_fields(source, GOALIE_FIELDS)
    no_bet = []
    if not confirmed:
        no_bet.append("goalie_starter_unconfirmed_caps_goalie_team_total_markets")
    if source.get("goals_saved_above_expected_proxy") in (None, ""):
        no_bet.append("gsax_missing_not_inferred_from_save_percentage")
    if source.get("recent_save_percentage") not in (None, "") and source.get("goals_saved_above_expected_proxy") in (None, ""):
        no_bet.append("recent_save_percentage_volatile_without_shot_quality_adjustment")
    if boolish(source.get("back_to_back_start")):
        no_bet.append("back_to_back_goalie_start_fatigue_warning")
    injury = str(source.get("injury_status") or source.get("goalie_injury_status") or "").lower()
    if injury in {"questionable", "doubtful", "out", "injured"}:
        no_bet.append("goalie_injury_uncertainty_hard_warning")

    return finalize_hockey_response(
        {
            "goalie_level_allowed": bool(goalie_level_allowed),
            "goalie_impact_score": round(clamp(goalie_impact), 2),
            "starter_certainty_score": round(clamp(starter_certainty), 2),
            "shot_quality_adjusted_score": round(clamp(shot_quality or 0.0), 2),
            "workload_fatigue_score": round(clamp(workload_fatigue or 0.0), 2),
            "high_danger_resilience_score": round(clamp(high_danger or 0.0), 2),
            "rebound_control_score": round(clamp(rebound_control or 0.0), 2),
            "goalie_prop_relevance": round(clamp(goalie_prop_relevance or 0.0), 2),
            "team_market_goalie_modifier": round(clamp(team_modifier), 2),
            "total_market_goalie_modifier": round(clamp(total_modifier or 0.0), 2),
            "missing_goalie_inputs": compact_list(missing, limit=25),
            "no_bet_reasons": compact_list(no_bet, limit=20),
            "confidence_cap_reason": "goalie_unconfirmed_or_gsax_missing" if no_bet else None,
            "confirmed_starter": confirmed,
            "gsax_fabricated": False,
        },
        source_payload=source,
    )

from __future__ import annotations

from typing import Any

from .baseball_impact_common import clamp, compact_list, finalize_baseball_response, missing_fields, score_from_range, weighted_average


DEFENSE_BASERUNNING_INPUTS = (
    "outs_above_average_proxy",
    "defensive_runs_saved_proxy",
    "arm_strength_proxy",
    "range_score_proxy",
    "catcher_pop_time_proxy",
    "catcher_throwing_score",
    "catcher_framing_proxy",
    "passed_ball_wild_pitch_risk",
    "team_defensive_alignment_proxy",
    "sprint_speed",
    "stolen_base_attempt_rate",
    "stolen_base_success_rate",
    "pitcher_hold_runner_score",
    "team_aggressiveness_proxy",
    "extra_base_taken_rate",
)


def evaluate_baseball_defense_baserunning_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    defense = weighted_average(
        (
            (score_from_range(source.get("outs_above_average_proxy"), low=-20.0, high=20.0), 0.65),
            (score_from_range(source.get("defensive_runs_saved_proxy"), low=-20.0, high=20.0), 0.55),
            (score_from_range(source.get("arm_strength_proxy"), low=0.0, high=100.0), 0.25),
            (score_from_range(source.get("range_score_proxy"), low=0.0, high=100.0), 0.35),
            (score_from_range(source.get("team_defensive_alignment_proxy"), low=0.0, high=100.0), 0.25),
        )
    )
    catcher = weighted_average(((score_from_range(source.get("catcher_framing_proxy"), low=-10.0, high=10.0), 0.55), (score_from_range(source.get("catcher_pop_time_proxy"), low=2.15, high=1.82), 0.35), (score_from_range(source.get("catcher_throwing_score"), low=0.0, high=100.0), 0.35), (score_from_range(source.get("passed_ball_wild_pitch_risk"), low=0.0, high=100.0, inverse=True), 0.25)))
    baserun = weighted_average(((score_from_range(source.get("sprint_speed"), low=25.0, high=30.5), 0.45), (score_from_range(source.get("stolen_base_attempt_rate"), low=0.01, high=0.16), 0.55), (score_from_range(source.get("stolen_base_success_rate"), low=0.60, high=0.88), 0.45), (score_from_range(source.get("team_aggressiveness_proxy"), low=0.0, high=100.0), 0.25), (score_from_range(source.get("extra_base_taken_rate"), low=0.28, high=0.48), 0.25)))
    steal_rel = weighted_average(((baserun, 0.55), (score_from_range(source.get("pitcher_hold_runner_score"), low=0.0, high=100.0, inverse=True), 0.45), (100.0 - (catcher or 50.0), 0.35)))
    pitcher_support = weighted_average(((defense, 0.65), (catcher, 0.35)))
    total_mod = weighted_average(((100.0 - (defense or 50.0), 0.45), (baserun, 0.25), (100.0 - (catcher or 50.0), 0.2)))
    no_bet = []
    if source.get("stolen_base_attempt_rate") not in (None, "") and (source.get("pitcher_hold_runner_score") in (None, "") or source.get("catcher_pop_time_proxy") in (None, "")):
        no_bet.append("stolen_base_props_need_runner_pitcher_catcher_context")
        no_bet.append("stolen_base_context_incomplete")
    return finalize_baseball_response(
        {
            "defense_impact_score": round(clamp(defense or 0.0), 2),
            "baserunning_impact_score": round(clamp(baserun or 0.0), 2),
            "catcher_run_prevention_score": round(clamp(catcher or 0.0), 2),
            "stolen_base_relevance_score": round(clamp(steal_rel or 0.0), 2),
            "pitcher_support_modifier": round(clamp(pitcher_support or 0.0), 2),
            "total_market_modifier": round(clamp(total_mod or 0.0), 2),
            "missing_inputs": compact_list(missing_fields(source, DEFENSE_BASERUNNING_INPUTS), limit=25),
            "no_bet_reasons": compact_list(no_bet, limit=10),
            "defense_is_standalone_edge": False,
        },
        source_payload=source,
    )

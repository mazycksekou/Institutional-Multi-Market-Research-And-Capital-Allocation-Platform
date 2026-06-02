from __future__ import annotations

from typing import Any

from .football_impact_schema import (
    clamp,
    compact_list,
    finalize_football_response,
    missing_fields,
    score_centered,
    score_from_range,
    weighted_average,
)


MATCHUP_INPUTS = (
    "qb_pressure_to_sack_rate",
    "opponent_pressure_rate",
    "qb_blitz_efficiency",
    "opponent_blitz_rate",
    "qb_man_efficiency",
    "qb_zone_efficiency",
    "opponent_man_coverage_rate",
    "opponent_zone_coverage_rate",
    "wr_cb_advantage",
    "te_lb_s_advantage",
    "ol_pressure_allowed_proxy",
    "dl_pressure_rate",
    "run_block_success_proxy",
    "defensive_run_stop_rate",
    "box_count",
    "rb_box_adjusted_efficiency",
    "coverage_shell_pass_risk",
    "red_zone_offense_score",
    "red_zone_defense_score",
    "pace_score",
    "opponent_pace_score",
    "explosive_offense_rate",
    "explosive_prevention_rate",
    "special_teams_field_position_score",
)


def evaluate_football_matchup_context(row: dict[str, Any] | None = None, *, market_type: str | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    qb_pressure_risk = weighted_average(
        (
            (score_from_range(source.get("qb_pressure_to_sack_rate"), low=0.08, high=0.28), 0.75),
            (score_from_range(source.get("opponent_pressure_rate"), low=0.22, high=0.48), 0.85),
            (score_from_range(source.get("ol_pressure_allowed_proxy"), low=0.08, high=0.42), 0.65),
            (score_from_range(source.get("dl_pressure_rate"), low=0.22, high=0.48), 0.65),
        )
    )
    blitz_mismatch = weighted_average(
        (
            (score_from_range(source.get("opponent_blitz_rate"), low=0.12, high=0.48), 0.55),
            (score_centered(source.get("qb_blitz_efficiency"), center=0.0, span=0.35, ), 0.65),
        )
    )
    if blitz_mismatch is not None and source.get("qb_blitz_efficiency") not in (None, ""):
        qb_blitz_eff = score_centered(source.get("qb_blitz_efficiency"), center=0.0, span=0.35) or 50.0
        blitz_mismatch = clamp((score_from_range(source.get("opponent_blitz_rate"), low=0.12, high=0.48) or 0.0) * 0.6 + (100.0 - qb_blitz_eff) * 0.4)

    wr_cb = score_from_range(source.get("wr_cb_advantage"), low=-20.0, high=20.0)
    te_matchup = score_from_range(source.get("te_lb_s_advantage"), low=-20.0, high=20.0)
    pass_shell_risk = weighted_average(
        (
            (score_from_range(source.get("coverage_shell_pass_risk"), low=0.0, high=100.0), 0.65),
            (score_from_range(source.get("opponent_man_coverage_rate"), low=0.12, high=0.48), 0.2),
            (score_from_range(source.get("opponent_zone_coverage_rate"), low=0.32, high=0.78), 0.2),
        )
    )
    run_mismatch = weighted_average(
        (
            (score_from_range(source.get("run_block_success_proxy"), low=0.32, high=0.58), 0.55),
            (score_from_range(source.get("defensive_run_stop_rate"), low=0.02, high=0.16, inverse=True), 0.45),
            (score_from_range(source.get("box_count"), low=5.0, high=8.5, inverse=True), 0.45),
            (score_centered(source.get("rb_box_adjusted_efficiency"), center=0.0, span=0.24), 0.55),
        )
    )
    red_zone = weighted_average(
        (
            (score_from_range(source.get("red_zone_offense_score"), low=0.0, high=100.0), 0.65),
            (score_from_range(source.get("red_zone_defense_score"), low=0.0, high=100.0, inverse=True), 0.65),
        )
    )
    pace = weighted_average(
        (
            (score_from_range(source.get("pace_score"), low=0.0, high=100.0), 0.5),
            (score_from_range(source.get("opponent_pace_score"), low=0.0, high=100.0), 0.5),
        )
    )
    explosive_matchup = weighted_average(
        (
            (score_from_range(source.get("explosive_offense_rate"), low=0.04, high=0.18), 0.55),
            (score_from_range(source.get("explosive_prevention_rate"), low=0.04, high=0.18, inverse=True), 0.55),
            (pass_shell_risk, 0.25),
        )
    )
    special_teams = score_from_range(source.get("special_teams_field_position_score"), low=0.0, high=100.0)

    advantage = weighted_average(
        (
            (100.0 - (qb_pressure_risk or 50.0), 0.45),
            (wr_cb, 0.55),
            (te_matchup, 0.25),
            (run_mismatch, 0.55),
            (red_zone, 0.45),
            (pace, 0.25),
            (explosive_matchup, 0.45),
            (special_teams, 0.2),
        )
    )
    risk = weighted_average(
        (
            (qb_pressure_risk, 0.8),
            (blitz_mismatch, 0.45),
            (pass_shell_risk, 0.45),
            (100.0 - (run_mismatch or 50.0), 0.4),
            (100.0 - (red_zone or 50.0), 0.25),
        )
    )

    mismatch_reasons = []
    no_bet_reasons = []
    market_notes = []
    if (qb_pressure_risk or 0.0) >= 68.0:
        mismatch_reasons.append("qb_vs_pressure_disadvantage")
        no_bet_reasons.append("pressure_mismatch_requires_sack_turnover_market_review")
        market_notes.extend(["sacks", "interceptions", "passing_yards", "spread"])
    if wr_cb is not None and wr_cb >= 68.0:
        mismatch_reasons.append("wr_vs_cb_advantage")
        market_notes.extend(["receiving_yards", "receptions", "longest_reception"])
    if run_mismatch is not None and run_mismatch <= 35.0:
        mismatch_reasons.append("ol_vs_dl_run_game_disadvantage")
        no_bet_reasons.append("ol_dl_mismatch_caps_rushing_confidence")
        market_notes.extend(["rushing_yards", "sacks", "spread"])
    if (explosive_matchup or 0.0) >= 70.0:
        mismatch_reasons.append("explosive_offense_vs_prevention_advantage")
        market_notes.extend(["total", "team_total", "longest_reception"])
    if market_type:
        market_notes.append(str(market_type))
    spread_relevance = weighted_average(((advantage, 0.65), (100.0 - (risk or 0.0), 0.45), (red_zone, 0.25)))
    total_relevance = weighted_average(((pace, 0.55), (explosive_matchup, 0.65), (red_zone, 0.45), (100.0 - (qb_pressure_risk or 0.0), 0.25)))
    player_prop_relevance = weighted_average(((wr_cb, 0.55), (te_matchup, 0.25), (run_mismatch, 0.45), (100.0 - (qb_pressure_risk or 0.0), 0.35)))

    return finalize_football_response(
        {
            "matchup_advantage_score": round(clamp(advantage or 0.0), 2),
            "matchup_risk_score": round(clamp(risk or 0.0), 2),
            "mismatch_reasons": compact_list(mismatch_reasons, limit=12),
            "no_bet_reasons": compact_list(no_bet_reasons, limit=12),
            "market_specific_matchup_notes": compact_list(market_notes, limit=15),
            "qb_pressure_risk_score": round(clamp(qb_pressure_risk or 0.0), 2),
            "wr_cb_matchup_score": round(clamp(wr_cb or 0.0), 2),
            "ol_dl_run_matchup_score": round(clamp(run_mismatch or 0.0), 2),
            "red_zone_matchup_score": round(clamp(red_zone or 0.0), 2),
            "pace_matchup_score": round(clamp(pace or 0.0), 2),
            "explosive_matchup_score": round(clamp(explosive_matchup or 0.0), 2),
            "spread_relevance": round(clamp(spread_relevance or 0.0), 2),
            "total_relevance": round(clamp(total_relevance or 0.0), 2),
            "player_prop_relevance": round(clamp(player_prop_relevance or 0.0), 2),
            "missing_inputs": compact_list(missing_fields(source, MATCHUP_INPUTS), limit=35),
        },
        source_payload=source,
    )

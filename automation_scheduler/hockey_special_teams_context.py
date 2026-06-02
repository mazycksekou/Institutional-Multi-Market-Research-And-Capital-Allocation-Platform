from __future__ import annotations

from typing import Any

from .hockey_impact_common import clamp, compact_list, finalize_hockey_response, missing_fields, score_from_range, weighted_average


SPECIAL_TEAMS_FIELDS = (
    "power_play_percentage",
    "penalty_kill_percentage",
    "power_play_xg_rate",
    "penalty_kill_xg_against_rate",
    "opponent_penalty_rate",
)


def evaluate_hockey_special_teams_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    power_play = weighted_average(
        (
            (score_from_range(source.get("power_play_percentage"), low=0.10, high=0.35), 0.35),
            (score_from_range(source.get("power_play_xg_rate"), low=0.25, high=1.25), 0.75),
            (score_from_range(source.get("power_play_shot_rate"), low=2.0, high=9.0), 0.45),
            (score_from_range(source.get("penalties_drawn_rate"), low=1.5, high=5.0), 0.25),
        )
    )
    penalty_kill = weighted_average(
        (
            (score_from_range(source.get("penalty_kill_percentage"), low=0.68, high=0.90), 0.35),
            (score_from_range(source.get("penalty_kill_xg_against_rate"), low=0.25, high=1.25, inverse=True), 0.75),
            (score_from_range(source.get("penalty_kill_shot_against_rate"), low=2.0, high=9.0, inverse=True), 0.45),
            (score_from_range(source.get("penalties_taken_rate"), low=1.5, high=5.0, inverse=True), 0.25),
        )
    )
    opponent_penalty_env = score_from_range(source.get("opponent_penalty_rate"), low=1.5, high=5.5)
    referee_penalty = score_from_range(source.get("referee_penalty_tendency_proxy"), low=0, high=1)
    special_edge = weighted_average(((power_play, 0.55), (penalty_kill, 0.35), (opponent_penalty_env, 0.25))) or 0.0
    volatility = weighted_average(
        (
            (score_from_range(source.get("opponent_penalty_rate"), low=1.5, high=5.5), 0.35),
            (score_from_range(source.get("penalties_taken_rate"), low=1.5, high=5.5), 0.35),
            (100.0 if source.get("referee_penalty_tendency_proxy") in (None, "") else 35.0, 0.25),
        )
    )
    player_ppp = weighted_average(
        (
            (power_play, 0.55),
            (score_from_range(source.get("power_play_unit_role"), low=0, high=1), 0.45),
            (score_from_range(source.get("special_teams_time_on_ice"), low=0, high=6), 0.35),
            (opponent_penalty_env, 0.25),
        )
    )
    total_modifier = weighted_average(((power_play, 0.3), (100.0 - (penalty_kill or 0.0), 0.25), (opponent_penalty_env, 0.25), (volatility, 0.2))) or 0.0
    team_total_modifier = weighted_average(((power_play, 0.55), (opponent_penalty_env, 0.25), (volatility, 0.12))) or 0.0
    missing = missing_fields(source, SPECIAL_TEAMS_FIELDS)
    no_bet = []
    if source.get("referee_penalty_tendency_proxy") in (None, ""):
        no_bet.append("referee_penalty_tendency_missing_not_fabricated")
    if (volatility or 0.0) >= 65.0:
        no_bet.append("special_teams_penalty_environment_volatile")

    return finalize_hockey_response(
        {
            "power_play_score": round(clamp(power_play or 0.0), 2),
            "penalty_kill_score": round(clamp(penalty_kill or 0.0), 2),
            "special_teams_edge_score": round(clamp(special_edge), 2),
            "special_teams_volatility_score": round(clamp(volatility or 0.0), 2),
            "player_power_play_prop_relevance": round(clamp(player_ppp or 0.0), 2),
            "total_market_modifier": round(clamp(total_modifier), 2),
            "team_total_modifier": round(clamp(team_total_modifier), 2),
            "penalty_environment_fabricated": False,
            "missing_inputs": compact_list(missing, limit=20),
            "no_bet_reasons": compact_list(no_bet, limit=20),
        },
        source_payload=source,
    )

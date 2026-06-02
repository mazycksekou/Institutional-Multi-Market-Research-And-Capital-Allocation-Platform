from __future__ import annotations

from typing import Any

from .basketball_player_impact_common import (
    clamp,
    compact_list,
    finalize_safe_response,
    missing_fields,
    percent_score,
    safe_float,
    score_from_range,
    weighted_average,
)


MARKET_RELEVANCE_INPUTS = (
    "projected_minutes",
    "usage_rate",
    "shot_attempt_rate",
    "touches",
    "drives",
    "paint_touches",
    "three_point_attempt_rate",
    "potential_assists",
    "time_of_possession",
    "rebound_chances",
    "contested_rebound_chances",
    "catch_and_shoot_attempts",
    "pull_up_attempts",
    "deflections",
    "opponent_rim_attempt_rate",
    "opponent_turnover_rate",
    "opponent_three_point_allowed_profile",
    "lineup_net_rating",
    "lineup_pace",
    "opponent_pace",
    "game_total",
    "implied_team_total",
)


def _score(payload: dict[str, Any], key: str) -> float:
    return clamp(payload.get(key, 0.0) or 0.0)


def _market_status(score: float, *, avoid_threshold: float = 34.0, review_threshold: float = 62.0) -> str:
    if score >= review_threshold:
        return "review"
    if score <= avoid_threshold:
        return "avoid"
    return "watch"


def evaluate_market_relevance(
    row: dict[str, Any] | None = None,
    *,
    possession: dict[str, Any] | None = None,
    tracking: dict[str, Any] | None = None,
    role: dict[str, Any] | None = None,
    lineup: dict[str, Any] | None = None,
    availability: dict[str, Any] | None = None,
    incentive: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    possession = possession or {}
    tracking = tracking or {}
    role = role or {}
    lineup = lineup or {}
    availability = availability or {}
    incentive = incentive or {}

    minutes = _score(availability, "projected_minutes_confidence") or score_from_range(source.get("projected_minutes"), low=8.0, high=38.0) or 0.0
    availability_score = _score(availability, "availability_score")
    minutes_stability = _score(availability, "minutes_stability_score")
    foul_safety = 100.0 - _score(availability, "foul_trouble_risk")
    blowout_safety = 100.0 - _score(lineup, "blowout_minutes_risk")
    possession_score = _score(possession, "possession_impact_score")
    offensive_possession = _score(possession, "offensive_possession_impact")
    defensive_possession = _score(possession, "defensive_possession_impact")
    tracking_score = _score(tracking, "tracking_opportunity_score")
    touch_score = _score(tracking, "touch_opportunity_score")
    creation_score = _score(tracking, "creation_opportunity_score")
    assist_score = _score(tracking, "assist_opportunity_score")
    rebound_score = _score(tracking, "rebound_opportunity_score")
    shooting_score = _score(tracking, "shooting_opportunity_score")
    rim_pressure = _score(tracking, "rim_pressure_score")
    spacing = _score(tracking, "spacing_gravity_score")
    defensive_tracking = _score(tracking, "defensive_tracking_score")
    role_efficiency = _score(role, "role_adjusted_efficiency_score")
    offensive_role = _score(role, "offensive_role_score")
    defensive_role = _score(role, "defensive_role_score")
    lineup_fit = _score(lineup, "lineup_fit_score")
    matchup_fit = _score(lineup, "matchup_fit_score")
    pace = _score(lineup, "pace_context_score")
    game_script = _score(lineup, "game_script_fit_score")
    usage = score_from_range(source.get("usage_rate"), low=8.0, high=34.0) or 0.0
    shot_attempts = score_from_range(source.get("shot_attempt_rate"), low=4.0, high=28.0) or 0.0
    drives = score_from_range(source.get("drives"), low=0.0, high=24.0) or 0.0
    paint = score_from_range(source.get("paint_touches"), low=0.0, high=20.0) or 0.0
    threes_rate = score_from_range(source.get("three_point_attempt_rate"), low=0.0, high=0.65) or score_from_range(source.get("three_point_attempt_rate"), low=0.0, high=65.0) or 0.0
    potential_assists = score_from_range(source.get("potential_assists"), low=0.0, high=18.0) or 0.0
    time_on_ball = score_from_range(source.get("time_of_possession"), low=0.5, high=9.0) or 0.0
    teammate_shot_quality = percent_score(source.get("teammate_shot_quality")) or percent_score(source.get("lineup_spacing_score")) or 0.0
    opponent_miss_env = score_from_range(source.get("opponent_missed_shot_environment"), low=0.0, high=100.0) or (100.0 - matchup_fit if matchup_fit else 0.0)
    lineup_size = score_from_range(source.get("lineup_size_score"), low=0.0, high=100.0) or 50.0
    opponent_rim_attempts = score_from_range(source.get("opponent_rim_attempt_rate"), low=0.0, high=0.48) or score_from_range(source.get("opponent_rim_attempt_rate"), low=0.0, high=48.0) or 0.0
    opponent_turnover = score_from_range(source.get("opponent_turnover_rate"), low=0.08, high=0.22) or 0.0
    opponent_three_allowed = percent_score(source.get("opponent_three_point_allowed_profile")) or 0.0
    incentive_usage = _score(incentive, "incentive_usage_pressure")
    incentive_minutes = _score(incentive, "incentive_minutes_pressure")
    stat_chase = _score(incentive, "incentive_stat_chase_risk")
    team_alignment = _score(incentive, "incentive_team_alignment_score")
    team_market_penalty = 18.0 if incentive.get("incentive_market_relevance") == "props_high_team_markets_lower_confidence" else 0.0

    points = weighted_average(
        (
            (minutes, 1.2),
            (minutes_stability, 0.9),
            (usage, 1.1),
            (shot_attempts, 1.0),
            (touch_score, 0.7),
            (creation_score, 0.75),
            (drives, 0.45),
            (paint, 0.35),
            (threes_rate, 0.35),
            (matchup_fit, 0.55),
            (blowout_safety, 0.75),
            (incentive_usage, 0.35),
            (incentive_minutes, 0.25),
        )
    ) or 0.0
    assists = weighted_average(
        (
            (minutes, 1.1),
            (time_on_ball, 0.95),
            (potential_assists, 1.1),
            (assist_score, 1.0),
            (touch_score, 0.65),
            (teammate_shot_quality, 0.65),
            (pace, 0.45),
            (matchup_fit, 0.35),
            (blowout_safety, 0.55),
        )
    ) or 0.0
    rebounds = weighted_average(
        (
            (minutes, 1.15),
            (rebound_score, 1.15),
            (score_from_range(source.get("rebound_chances"), low=0.0, high=22.0), 0.9),
            (score_from_range(source.get("contested_rebound_chances"), low=0.0, high=12.0), 0.6),
            (opponent_miss_env, 0.5),
            (lineup_size, 0.35),
            (pace, 0.35),
            (blowout_safety, 0.45),
        )
    ) or 0.0
    threes = weighted_average(
        (
            (minutes, 0.95),
            (threes_rate, 1.1),
            (score_from_range(source.get("catch_and_shoot_attempts"), low=0.0, high=12.0), 0.85),
            (score_from_range(source.get("pull_up_attempts"), low=0.0, high=12.0), 0.75),
            (shooting_score, 0.8),
            (opponent_three_allowed, 0.65),
            (pace, 0.35),
            (teammate_shot_quality, 0.4),
            (blowout_safety, 0.4),
        )
    ) or 0.0
    blocks_steals = weighted_average(
        (
            (minutes, 1.0),
            (defensive_role, 0.75),
            (defensive_tracking, 0.85),
            (opponent_rim_attempts, 0.6),
            (opponent_turnover, 0.65),
            (score_from_range(source.get("deflections"), low=0.0, high=8.0), 0.6),
            (percent_score(source.get("help_defense_impact")), 0.5),
            (foul_safety, 0.8),
        )
    ) or 0.0
    spread = weighted_average(
        (
            (possession_score, 1.1),
            (offensive_possession, 0.55),
            (defensive_possession, 0.55),
            (lineup_fit, 1.0),
            (availability_score, 0.85),
            (minutes_stability, 0.65),
            (matchup_fit, 0.55),
            (lineup.get("closing_lineup_probability"), 0.45),
            (team_alignment, 0.25),
        )
    ) or 0.0
    spread = clamp(spread - team_market_penalty)
    total = weighted_average(
        (
            (pace, 1.0),
            (offensive_possession, 0.7),
            (100.0 - defensive_possession if defensive_possession else 0.0, 0.45),
            (possession.get("foul_impact_score"), 0.35),
            (possession.get("transition_impact_score"), 0.55),
            (spacing, 0.45),
            (rim_pressure, 0.35),
            (game_script, 0.5),
        )
    ) or 0.0
    team_total = weighted_average(
        (
            (offensive_possession, 0.8),
            (lineup_fit, 0.55),
            (pace, 0.65),
            (matchup_fit, 0.55),
            (creation_score, 0.45),
            (spacing, 0.35),
            (team_alignment, 0.25),
        )
    ) or 0.0
    team_total = clamp(team_total - team_market_penalty)
    pra = weighted_average(((points, 1.0), (rebounds, 0.75), (assists, 0.75), (minutes_stability, 0.45))) or 0.0
    sgp = weighted_average(((points, 0.5), (assists, 0.45), (rebounds, 0.45), (minutes_stability, 0.6), (pace, 0.3), (blowout_safety, 0.45))) or 0.0

    market_scores = {
        "spread": round(clamp(spread), 2),
        "total": round(clamp(total), 2),
        "team_total": round(clamp(team_total), 2),
        "points_prop": round(clamp(points), 2),
        "assists_prop": round(clamp(assists), 2),
        "rebounds_prop": round(clamp(rebounds), 2),
        "threes_prop": round(clamp(threes), 2),
        "blocks_steals_prop": round(clamp(blocks_steals), 2),
        "pra_prop": round(clamp(pra), 2),
        "sgp_correlation": round(clamp(sgp), 2),
    }
    markets_to_avoid = [market for market, score in market_scores.items() if _market_status(score) == "avoid"]
    review_candidates = [market for market, score in sorted(market_scores.items(), key=lambda item: item[1], reverse=True) if _market_status(score) == "review"]
    if stat_chase >= 65.0:
        review_candidates = compact_list([market for market in review_candidates if market.endswith("_prop") or market in {"pra_prop", "sgp_correlation"}] + review_candidates)
    missing = missing_fields(source, MARKET_RELEVANCE_INPUTS)

    return finalize_safe_response(
        {
            "market_relevance_scores": market_scores,
            "spread_relevance_score": market_scores["spread"],
            "total_relevance_score": market_scores["total"],
            "team_total_relevance_score": market_scores["team_total"],
            "points_prop_relevance_score": market_scores["points_prop"],
            "assists_prop_relevance_score": market_scores["assists_prop"],
            "rebounds_prop_relevance_score": market_scores["rebounds_prop"],
            "threes_prop_relevance_score": market_scores["threes_prop"],
            "blocks_steals_relevance_score": market_scores["blocks_steals_prop"],
            "pra_relevance_score": market_scores["pra_prop"],
            "sgp_correlation_relevance_score": market_scores["sgp_correlation"],
            "recommended_market_focus": review_candidates[:5] or [market for market, _ in sorted(market_scores.items(), key=lambda item: item[1], reverse=True)[:3]],
            "markets_to_avoid": markets_to_avoid[:8],
            "market_relevance_missing_inputs": compact_list(missing, limit=30),
        },
        source_payload=source,
    )

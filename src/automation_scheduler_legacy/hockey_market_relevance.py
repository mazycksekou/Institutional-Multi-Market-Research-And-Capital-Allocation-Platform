from __future__ import annotations

from typing import Any

from .hockey_impact_common import (
    FIRST_PERIOD_MARKETS,
    GOALIE_PROP_MARKETS,
    SKATER_PROP_MARKETS,
    SPECIAL_TEAMS_MARKETS,
    TEAM_MARKETS,
    clamp,
    compact_list,
    finalize_hockey_response,
    normalize_hockey_market,
    weighted_average,
)


HOCKEY_MARKETS = tuple(TEAM_MARKETS | SKATER_PROP_MARKETS | GOALIE_PROP_MARKETS)


def _score(payload: dict[str, Any] | None, key: str) -> float:
    if not isinstance(payload, dict):
        return 0.0
    return clamp(payload.get(key, 0.0) or 0.0)


def _top_links(scores: dict[str, float], threshold: float = 58.0) -> list[str]:
    return [market for market, score in sorted(scores.items(), key=lambda item: item[1], reverse=True) if score >= threshold][:10]


def evaluate_hockey_market_relevance(
    row: dict[str, Any] | None = None,
    *,
    market_type: str | None = None,
    possession_impact: dict[str, Any] | None = None,
    skater_impact: dict[str, Any] | None = None,
    goalie_impact: dict[str, Any] | None = None,
    line_pair_context: dict[str, Any] | None = None,
    special_teams_context: dict[str, Any] | None = None,
    transition_context: dict[str, Any] | None = None,
    matchup_context: dict[str, Any] | None = None,
    availability_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    market = normalize_hockey_market(market_type or source.get("market_type") or "moneyline")
    possession_impact = possession_impact or {}
    skater_impact = skater_impact or {}
    goalie_impact = goalie_impact or {}
    line_pair_context = line_pair_context or {}
    special_teams_context = special_teams_context or {}
    transition_context = transition_context or {}
    matchup_context = matchup_context or {}
    availability_context = availability_context or {}
    incentive_context = incentive_context or {}

    possession = _score(possession_impact, "possession_score")
    shot_volume = _score(possession_impact, "shot_volume_score")
    xg_quality = _score(possession_impact, "xg_quality_score")
    high_danger = _score(possession_impact, "high_danger_score")
    first_period = _score(possession_impact, "first_period_pressure_score")
    pace = _score(possession_impact, "pace_volume_score")
    total_signal = _score(possession_impact, "total_signal_score")
    team_total_signal = _score(possession_impact, "team_total_signal_score")
    skater_market = _score(skater_impact, "skater_market_relevance")
    shot_gen = _score(skater_impact, "shot_generation_score")
    scoring = _score(skater_impact, "scoring_quality_score")
    playmaking = _score(skater_impact, "playmaking_score")
    blocked = _score(skater_impact, "blocked_shot_relevance_score")
    pp_role = _score(skater_impact, "special_teams_role_score")
    goalie_score = _score(goalie_impact, "goalie_impact_score")
    goalie_prop = _score(goalie_impact, "goalie_prop_relevance")
    goalie_team = _score(goalie_impact, "team_market_goalie_modifier")
    goalie_total = _score(goalie_impact, "total_market_goalie_modifier")
    line_quality = _score(line_pair_context, "line_quality_score")
    line_stability = _score(line_pair_context, "line_stability_score")
    pair_quality = _score(line_pair_context, "pair_quality_score")
    prop_volume = _score(line_pair_context, "prop_volume_modifier")
    special_edge = _score(special_teams_context, "special_teams_edge_score")
    pp_prop = _score(special_teams_context, "player_power_play_prop_relevance")
    special_volatility = _score(special_teams_context, "special_teams_volatility_score")
    transition = _score(transition_context, "transition_score")
    rush = _score(transition_context, "rush_attack_score")
    matchup_adv = _score(matchup_context, "matchup_advantage_score")
    matchup_risk = _score(matchup_context, "matchup_risk_score")
    availability = _score(availability_context, "availability_score")
    fatigue = _score(availability_context, "fatigue_risk_score")
    goalie_certainty = _score(availability_context, "goalie_certainty_score")
    role_stability = _score(availability_context, "role_stability_score")
    incentive_modifier = incentive_context.get("market_relevance_modifier") if isinstance(incentive_context.get("market_relevance_modifier"), dict) else {}

    scores = {
        "player_shots_on_goal": weighted_average(((shot_gen, 0.65), (prop_volume, 0.45), (pp_role, 0.25), (shot_volume, 0.25), (line_stability, 0.35), (100.0 - matchup_risk, 0.15))) or 0.0,
        "player_goals": weighted_average(((scoring, 0.55), (high_danger, 0.35), (pp_role, 0.25), (goalie_score and 100.0 - goalie_score, 0.2), (line_quality, 0.25), (special_edge, 0.18))) or 0.0,
        "player_assists": weighted_average(((playmaking, 0.55), (line_quality, 0.35), (pp_role, 0.3), (xg_quality, 0.2), (line_stability, 0.25))) or 0.0,
        "player_points": weighted_average(((scoring, 0.35), (playmaking, 0.35), (line_quality, 0.3), (pp_role, 0.25), (xg_quality, 0.2))) or 0.0,
        "player_power_play_points": weighted_average(((pp_prop, 0.65), (pp_role, 0.45), (special_edge, 0.35), (special_volatility and 100.0 - special_volatility, 0.15))) or 0.0,
        "player_blocked_shots": weighted_average(((blocked, 0.65), (pair_quality, 0.25), (shot_volume, 0.15), (role_stability, 0.25))) or 0.0,
        "anytime_goal": weighted_average(((scoring, 0.45), (high_danger, 0.35), (pp_role, 0.25), (team_total_signal, 0.2), (line_stability, 0.2))) or 0.0,
        "goalie_saves": weighted_average(((goalie_prop, 0.55), (goalie_certainty, 0.55), (shot_volume, 0.35), (pace, 0.25), (100.0 - fatigue, 0.15))) or 0.0,
        "goalie_goals_allowed": weighted_average(((goalie_certainty, 0.35), (goalie_total, 0.45), (xg_quality, 0.35), (high_danger, 0.3), (special_edge, 0.25))) or 0.0,
        "goalie_win": weighted_average(((goalie_certainty, 0.45), (goalie_team, 0.45), (possession, 0.25), (availability, 0.25))) or 0.0,
        "goalie_shutout": weighted_average(((goalie_certainty, 0.45), (goalie_score, 0.5), (pair_quality, 0.25), (100.0 - total_signal, 0.25))) or 0.0,
        "moneyline": weighted_average(((possession, 0.35), (xg_quality, 0.35), (goalie_team, 0.42), (special_edge, 0.18), (availability, 0.25), (matchup_adv, 0.22))) or 0.0,
        "three_way_moneyline": weighted_average(((possession, 0.35), (xg_quality, 0.32), (goalie_team, 0.42), (availability, 0.22), (matchup_adv, 0.22))) or 0.0,
        "regulation_moneyline": weighted_average(((possession, 0.35), (xg_quality, 0.35), (goalie_team, 0.38), (special_edge, 0.18), (pace, 0.18))) or 0.0,
        "puckline": weighted_average(((possession, 0.3), (xg_quality, 0.35), (high_danger, 0.22), (goalie_team, 0.34), (transition, 0.16), (matchup_adv, 0.2))) or 0.0,
        "total": weighted_average(((total_signal, 0.55), (pace, 0.35), (goalie_total, 0.38), (special_edge, 0.22), (fatigue, 0.16), (high_danger, 0.25))) or 0.0,
        "team_total": weighted_average(((team_total_signal, 0.55), (xg_quality, 0.35), (special_edge, 0.25), (goalie_score and 100.0 - goalie_score, 0.2), (line_quality, 0.2))) or 0.0,
        "first_period_moneyline": weighted_average(((first_period, 0.55), (possession, 0.28), (goalie_team, 0.3), (availability, 0.18))) or 0.0,
        "first_period_total": weighted_average(((first_period, 0.65), (pace, 0.32), (goalie_total, 0.25), (special_volatility, 0.15))) or 0.0,
        "first_period_team_total": weighted_average(((first_period, 0.55), (team_total_signal, 0.35), (special_edge, 0.18))) or 0.0,
    }
    player_adjustment = float(incentive_modifier.get("player_prop_relevance_adjustment", 0.0) or 0.0)
    team_adjustment = float(incentive_modifier.get("team_market_confidence_adjustment", 0.0) or 0.0)
    for player_market in SKATER_PROP_MARKETS | GOALIE_PROP_MARKETS:
        if player_market in scores:
            scores[player_market] += player_adjustment
    for team_market in TEAM_MARKETS:
        if team_market in scores:
            scores[team_market] += team_adjustment
    scores = {key: round(clamp(value), 2) for key, value in scores.items()}

    caps = {}
    no_bet = []
    if not line_pair_context.get("confirmed_lines", False) and market in SKATER_PROP_MARKETS:
        caps["skater_props"] = "confirmed_lines_missing_cap"
        no_bet.append("confirmed_lines_missing_caps_skater_props")
    if goalie_certainty < 55 and market in TEAM_MARKETS | GOALIE_PROP_MARKETS:
        caps["goalie_team_total_markets"] = "confirmed_goalie_missing_cap"
        no_bet.append("confirmed_goalie_missing_caps_goalie_team_markets")
    if special_volatility >= 65 and market in SPECIAL_TEAMS_MARKETS:
        caps["special_teams_markets"] = "special_teams_volatility_cap"
        no_bet.append("special_teams_volatility_requires_calibration")
    if fatigue >= 70:
        caps["fatigue_sensitive_markets"] = "back_to_back_or_three_in_four_cap"
        no_bet.append("fatigue_schedule_spot_caps_confidence")
    if market in FIRST_PERIOD_MARKETS and first_period <= 0 and total_signal >= 55:
        caps["first_period_markets"] = "full_game_context_not_first_period_context"
        no_bet.append("first_period_context_missing_full_game_signal_not_enough")

    strongest = _top_links(scores)
    weak = [key for key, value in scores.items() if value < 35.0][:10]
    selected_market_score = scores.get(market, 0.0)
    skater_prop_relevance = round(max((scores.get(key, 0.0) for key in SKATER_PROP_MARKETS), default=0.0), 2)
    goalie_prop_relevance = round(max((scores.get(key, 0.0) for key in GOALIE_PROP_MARKETS), default=0.0), 2)
    team_market_relevance = round(max((scores.get(key, 0.0) for key in TEAM_MARKETS), default=0.0), 2)
    special_teams_market_relevance = round(max((scores.get(key, 0.0) for key in SPECIAL_TEAMS_MARKETS), default=0.0), 2)

    return finalize_hockey_response(
        {
            "market_relevance_scores": scores,
            "strongest_market_links": compact_list(strongest, limit=10),
            "weak_market_links": compact_list(weak, limit=10),
            "no_bet_market_reasons": compact_list(no_bet, limit=20),
            "skater_prop_relevance": skater_prop_relevance,
            "goalie_prop_relevance": goalie_prop_relevance,
            "team_market_relevance": team_market_relevance,
            "special_teams_market_relevance": special_teams_market_relevance,
            "market_confidence_caps": caps,
            "selected_market_type": market,
            "selected_market_relevance_score": round(clamp(selected_market_score), 2),
            "edge_fabricated": False,
        },
        source_payload=source,
    )

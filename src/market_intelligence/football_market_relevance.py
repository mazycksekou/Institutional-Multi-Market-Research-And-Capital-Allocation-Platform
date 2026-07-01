from __future__ import annotations

from typing import Any

from .football_impact_schema import (
    PLAYER_PROP_MARKETS,
    TEAM_MARKETS,
    clamp,
    compact_list,
    finalize_football_response,
    normalize_football_market,
    weighted_average,
)


FOOTBALL_MARKETS = (
    "spread",
    "moneyline",
    "total",
    "team_total",
    "first_half_spread",
    "first_half_total",
    "passing_yards",
    "passing_tds",
    "interceptions",
    "rushing_yards",
    "rushing_attempts",
    "receiving_yards",
    "receptions",
    "anytime_td",
    "sacks",
    "tackles",
    "field_goals",
    "longest_reception",
    "longest_rush",
    "defensive_prop",
)


def _score(payload: dict[str, Any] | None, key: str) -> float:
    if not isinstance(payload, dict):
        return 0.0
    return clamp(payload.get(key, 0.0) or 0.0)


def _top_links(scores: dict[str, float], threshold: float = 58.0) -> list[str]:
    return [market for market, score in sorted(scores.items(), key=lambda item: item[1], reverse=True) if score >= threshold][:8]


def evaluate_football_market_relevance(
    row: dict[str, Any] | None = None,
    *,
    market_type: str | None = None,
    play_drive_impact: dict[str, Any] | None = None,
    role_impact: dict[str, Any] | None = None,
    personnel_context: dict[str, Any] | None = None,
    matchup_context: dict[str, Any] | None = None,
    availability_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    market = normalize_football_market(market_type or source.get("market_type") or "spread")
    play_drive_impact = play_drive_impact or {}
    role_impact = role_impact or {}
    personnel_context = personnel_context or {}
    matchup_context = matchup_context or {}
    availability_context = availability_context or {}
    incentive_context = incentive_context or {}

    play = _score(play_drive_impact, "play_impact_score")
    drive = _score(play_drive_impact, "drive_impact_score")
    pace = _score(play_drive_impact, "pace_volume_score")
    red_zone = _score(play_drive_impact, "red_zone_score")
    explosive = _score(play_drive_impact, "explosiveness_score")
    turnover_penalty = _score(play_drive_impact, "turnover_penalty")
    role = str(role_impact.get("role") or "unknown")
    role_impact_score = _score(role_impact, "role_impact_score")
    role_usage = _score(role_impact, "role_usage_score")
    role_efficiency = _score(role_impact, "role_efficiency_score")
    role_volatility = _score(role_impact, "role_volatility_score")
    personnel_fit = _score(personnel_context, "personnel_fit_score")
    formation_fit = _score(personnel_context, "formation_fit_score")
    personnel_stress = _score(personnel_context, "matchup_stress_score")
    matchup_adv = _score(matchup_context, "matchup_advantage_score")
    matchup_risk = _score(matchup_context, "matchup_risk_score")
    pressure_risk = _score(matchup_context, "qb_pressure_risk_score")
    wr_cb = _score(matchup_context, "wr_cb_matchup_score")
    ol_dl = _score(matchup_context, "ol_dl_run_matchup_score")
    availability = _score(availability_context, "availability_score")
    snap_stability = _score(availability_context, "snap_stability_score")
    weather = _score(availability_context, "weather_adjustment_score")
    wind = _score(availability_context, "wind_risk_score")
    qb_market_risk = _score(availability_context, "starting_qb_market_risk_score")
    incentive_behavior = _score(incentive_context, "incentive_behavior_score")
    stat_chase = _score(incentive_context, "stat_chase_risk")
    team_alignment = _score(incentive_context, "team_alignment_score")
    market_modifier = incentive_context.get("market_relevance_modifier") if isinstance(incentive_context.get("market_relevance_modifier"), dict) else {}
    weather_safe = 100.0 - weather
    wind_safe = 100.0 - wind

    scores = {
        "passing_yards": weighted_average(((role_impact_score if role == "QB" else 0.0, 0.8), (role_efficiency, 0.45), (pressure_risk and 100.0 - pressure_risk, 0.65), (wr_cb, 0.45), (weather_safe, 0.65), (pace, 0.35), (explosive, 0.35))) or 0.0,
        "passing_tds": weighted_average(((role_impact_score if role == "QB" else 0.0, 0.6), (red_zone, 0.7), (pressure_risk and 100.0 - pressure_risk, 0.45), (weather_safe, 0.55), (team_alignment, 0.25))) or 0.0,
        "interceptions": weighted_average(((pressure_risk, 0.8), (turnover_penalty, 0.7), (weather, 0.35), (matchup_risk, 0.45))) or 0.0,
        "rushing_yards": weighted_average(((role_impact_score if role == "RB" else 0.0, 0.75), (role_usage, 0.7), (ol_dl, 0.8), (formation_fit, 0.35), (weather, 0.15), (snap_stability, 0.35))) or 0.0,
        "rushing_attempts": weighted_average(((role_usage, 0.85), (ol_dl, 0.5), (team_alignment, 0.25), (weather, 0.15), (availability, 0.45))) or 0.0,
        "receiving_yards": weighted_average(((role_impact_score if role in {"WR", "TE"} else 0.0, 0.85), (role_usage, 0.85), (wr_cb, 0.65), (pressure_risk and 100.0 - pressure_risk, 0.3), (wind_safe, 0.6), (pace, 0.3))) or 0.0,
        "receptions": weighted_average(((role_usage, 0.95), (snap_stability, 0.6), (pressure_risk and 100.0 - pressure_risk, 0.2), (wind_safe, 0.3))) or 0.0,
        "anytime_td": weighted_average(((red_zone, 0.85), (role_usage, 0.55), (role_impact_score, 0.45), (team_alignment, 0.25), (stat_chase, 0.2))) or 0.0,
        "sacks": weighted_average(((pressure_risk, 0.85), (personnel_stress, 0.55), (matchup_risk, 0.55), (qb_market_risk, 0.3))) or 0.0,
        "tackles": weighted_average(((role_usage, 0.7), (snap_stability, 0.65), (pace, 0.3), (role_impact_score if role in {"LB", "CB", "S"} else 0.0, 0.5))) or 0.0,
        "field_goals": weighted_average(((drive, 0.35), (red_zone and 100.0 - red_zone, 0.45), (wind_safe, 0.85), (weather_safe, 0.55))) or 0.0,
        "longest_reception": weighted_average(((explosive, 0.55), (wr_cb, 0.75), (role_efficiency if role in {"WR", "TE"} else 0.0, 0.35), (wind_safe, 0.85))) or 0.0,
        "longest_rush": weighted_average(((role_efficiency if role == "RB" else 0.0, 0.45), (ol_dl, 0.75), (explosive, 0.35), (weather, 0.1))) or 0.0,
        "spread": weighted_average(((play, 0.55), (drive, 0.6), (matchup_adv, 0.45), (availability, 0.75), (100.0 - qb_market_risk, 0.85), (team_alignment, 0.35))) or 0.0,
        "moneyline": weighted_average(((drive, 0.65), (matchup_adv, 0.45), (availability, 0.8), (100.0 - qb_market_risk, 0.9), (team_alignment, 0.35))) or 0.0,
        "total": weighted_average(((pace, 0.75), (play, 0.45), (explosive, 0.5), (red_zone, 0.45), (weather_safe, 1.0), (100.0 - qb_market_risk, 0.45))) or 0.0,
        "team_total": weighted_average(((drive, 0.75), (red_zone, 0.65), (play, 0.45), (availability, 0.45), (weather_safe, 0.65), (team_alignment, 0.25))) or 0.0,
        "defensive_prop": weighted_average(((role_impact_score if role in {"DL", "EDGE", "LB", "CB", "S"} else 0.0, 0.65), (role_usage, 0.45), (matchup_risk, 0.45), (snap_stability, 0.45))) or 0.0,
    }
    scores["first_half_spread"] = weighted_average(((scores["spread"], 0.75), (play, 0.35), (100.0 - qb_market_risk, 0.55))) or 0.0
    scores["first_half_total"] = weighted_average(((scores["total"], 0.75), (pace, 0.35), (weather_safe, 0.55))) or 0.0
    player_adjustment = float(market_modifier.get("player_prop_relevance_adjustment", 0.0) or 0.0)
    team_adjustment = float(market_modifier.get("team_market_confidence_adjustment", 0.0) or 0.0)
    for player_market in PLAYER_PROP_MARKETS:
        if player_market in scores:
            scores[player_market] += player_adjustment
    for team_market in TEAM_MARKETS:
        if team_market in scores:
            scores[team_market] += team_adjustment
    scores = {key: round(clamp(value), 2) for key, value in scores.items()}
    no_bet = []
    if wind >= 65.0:
        no_bet.extend(["wind_caps_passing_kicking_total_markets"])
    if qb_market_risk >= 65.0:
        no_bet.extend(["backup_or_uncertain_qb_caps_team_markets"])
    if role_volatility >= 70.0 and market in PLAYER_PROP_MARKETS:
        no_bet.append("role_volatility_caps_player_prop_market")
    if matchup_context.get("no_bet_reasons"):
        no_bet.extend(list(matchup_context.get("no_bet_reasons") or [])[:5])
    if incentive_context.get("no_bet_reasons"):
        no_bet.extend(list(incentive_context.get("no_bet_reasons") or [])[:5])
    caps = {}
    if wind >= 65.0:
        caps.update({"passing_yards": "wind_cap", "field_goals": "wind_cap", "total": "wind_cap"})
    if qb_market_risk >= 65.0:
        caps.update({"spread": "starting_qb_uncertainty_cap", "moneyline": "starting_qb_uncertainty_cap", "team_total": "starting_qb_uncertainty_cap"})
    if role_volatility >= 70.0:
        caps["player_props"] = "role_volatility_cap"

    strongest = _top_links(scores, threshold=58.0)
    weak = [key for key, value in scores.items() if value < 35.0][:8]
    player_prop_relevance = round(max((scores.get(key, 0.0) for key in PLAYER_PROP_MARKETS if key in scores), default=0.0), 2)
    team_market_relevance = round(max((scores.get(key, 0.0) for key in TEAM_MARKETS if key in scores), default=0.0), 2)
    selected_market_score = scores.get(market, 0.0)
    if market in {"player_passing_prop"}:
        selected_market_score = max(scores["passing_yards"], scores["passing_tds"], scores["interceptions"])
    elif market in {"player_rushing_prop"}:
        selected_market_score = max(scores["rushing_yards"], scores["rushing_attempts"], scores["longest_rush"])
    elif market in {"player_receiving_prop"}:
        selected_market_score = max(scores["receiving_yards"], scores["receptions"], scores["longest_reception"])
    elif market == "sack_prop":
        selected_market_score = scores["sacks"]
    elif market == "interception_prop":
        selected_market_score = scores["interceptions"]

    return finalize_football_response(
        {
            "market_relevance_scores": scores,
            "strongest_market_links": compact_list(strongest, limit=10),
            "weak_market_links": compact_list(weak, limit=10),
            "no_bet_market_reasons": compact_list(no_bet, limit=15),
            "player_prop_relevance": player_prop_relevance,
            "team_market_relevance": team_market_relevance,
            "market_confidence_caps": caps,
            "selected_market_type": market,
            "selected_market_relevance_score": round(clamp(selected_market_score), 2),
            "weather_adjusted_markets": compact_list(["passing_yards", "field_goals", "total", "longest_reception"] if wind >= 45.0 else [], limit=10),
            "pressure_adjusted_markets": compact_list(["sacks", "interceptions", "passing_yards", "spread"] if pressure_risk >= 55.0 else [], limit=10),
            "edge_fabricated": False,
        },
        source_payload=source,
    )

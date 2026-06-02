from __future__ import annotations

from typing import Any

from .baseball_impact_common import BATTER_PROP_MARKETS, PITCHER_PROP_MARKETS, TEAM_MARKETS, clamp, compact_list, finalize_baseball_response, normalize_baseball_market, weighted_average


def _score(section: dict[str, Any] | None, key: str) -> float:
    return clamp((section or {}).get(key, 0.0) or 0.0)


def evaluate_baseball_market_relevance(
    row: dict[str, Any] | None = None,
    *,
    market_type: str = "moneyline",
    run_value_impact: dict[str, Any] | None = None,
    pitcher_impact: dict[str, Any] | None = None,
    batter_impact: dict[str, Any] | None = None,
    matchup_context: dict[str, Any] | None = None,
    lineup_context: dict[str, Any] | None = None,
    bullpen_context: dict[str, Any] | None = None,
    park_weather_umpire_context: dict[str, Any] | None = None,
    defense_baserunning_context: dict[str, Any] | None = None,
    availability_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    market = normalize_baseball_market(market_type)
    rv = run_value_impact or {}
    pit = pitcher_impact or {}
    bat = batter_impact or {}
    match = matchup_context or {}
    lineup = lineup_context or {}
    pen = bullpen_context or {}
    park = park_weather_umpire_context or {}
    defbase = defense_baserunning_context or {}
    avail = availability_context or {}
    incentive = incentive_context or {}
    weather_delay = _score(avail, "weather_delay_risk_score")
    pitch_limit_warning = "pitch_count_limit_hard_warning_for_outs_and_strikeouts" in (avail.get("no_bet_reasons") or []) or "pitch_count_limit_caps_outs_and_strikeout_props" in (pit.get("no_bet_reasons") or [])
    scores = {
        "pitcher_strikeouts": weighted_average(((_score(pit, "strikeout_skill_score"), 0.8), (_score(pit, "command_score"), 0.35), (_score(match, "pitcher_matchup_score"), 0.55), (_score(park, "umpire_zone_modifier"), 0.25), (100.0 - weather_delay, 0.35), (100.0 - _score(pit, "workload_fatigue_score"), 0.25))) or 0.0,
        "pitcher_outs_recorded": weighted_average(((_score(pit, "pitcher_impact_score"), 0.45), (_score(pit, "command_score"), 0.35), (100.0 - _score(pit, "workload_fatigue_score"), 0.55), (100.0 - _score(avail, "weather_delay_risk_score"), 0.45), (_score(pen, "bullpen_fatigue_score"), 0.15))) or 0.0,
        "pitcher_earned_runs": weighted_average(((100.0 - _score(pit, "contact_suppression_score"), 0.55), (_score(bat, "contact_quality_score"), 0.35), (_score(lineup, "lineup_quality_score"), 0.45), (_score(park, "total_market_modifier"), 0.45), (100.0 - _score(defbase, "pitcher_support_modifier"), 0.25))) or 0.0,
        "pitcher_hits_allowed": weighted_average(((100.0 - _score(pit, "contact_suppression_score"), 0.55), (_score(bat, "hit_probability_proxy"), 0.45), (_score(lineup, "lineup_quality_score"), 0.35))) or 0.0,
        "pitcher_walks_allowed": weighted_average(((100.0 - _score(pit, "command_score"), 0.65), (_score(park, "umpire_zone_modifier") and 100.0 - _score(park, "umpire_zone_modifier"), 0.25))) or 0.0,
        "pitcher_home_runs_allowed": weighted_average(((_score(pit, "home_run_risk_score"), 0.65), (_score(bat, "home_run_relevance_score"), 0.35), (_score(park, "home_run_environment_score"), 0.55))) or 0.0,
        "batter_hits": weighted_average(((_score(bat, "hit_probability_proxy"), 0.8), (_score(lineup, "plate_appearance_projection_confidence"), 0.5), (_score(match, "batter_matchup_score"), 0.35))) or 0.0,
        "batter_total_bases": weighted_average(((_score(bat, "total_bases_relevance_score"), 0.75), (_score(bat, "contact_quality_score"), 0.35), (_score(match, "batter_matchup_score"), 0.35), (_score(park, "home_run_environment_score"), 0.35))) or 0.0,
        "batter_home_runs": weighted_average(((_score(bat, "home_run_relevance_score"), 0.8), (_score(pit, "home_run_risk_score"), 0.45), (_score(park, "home_run_environment_score"), 0.65), (_score(match, "batter_matchup_score"), 0.25))) or 0.0,
        "batter_rbis": weighted_average(((_score(lineup, "plate_appearance_projection_confidence"), 0.45), (_score(lineup, "lineup_quality_score"), 0.4), (_score(bat, "contact_quality_score"), 0.35), (_score(rv, "team_total_signal_score"), 0.35))) or 0.0,
        "batter_runs": weighted_average(((_score(lineup, "plate_appearance_projection_confidence"), 0.45), (_score(bat, "plate_discipline_score"), 0.35), (_score(lineup, "run_environment_modifier"), 0.45))) or 0.0,
        "batter_stolen_bases": weighted_average(((_score(bat, "stolen_base_relevance_score"), 0.45), (_score(defbase, "stolen_base_relevance_score"), 0.85), (_score(lineup, "plate_appearance_projection_confidence"), 0.2))) or 0.0,
        "batter_walks": weighted_average(((_score(bat, "plate_discipline_score"), 0.55), (100.0 - _score(pit, "command_score"), 0.35), (_score(park, "umpire_zone_modifier") and 100.0 - _score(park, "umpire_zone_modifier"), 0.25))) or 0.0,
        "batter_strikeouts": weighted_average(((_score(bat, "strikeout_risk_score"), 0.6), (_score(pit, "strikeout_skill_score"), 0.55), (_score(match, "pitcher_matchup_score"), 0.35), (_score(park, "umpire_zone_modifier"), 0.2))) or 0.0,
        "moneyline": weighted_average(((_score(rv, "full_game_signal_score"), 0.6), (_score(pit, "pitcher_impact_score"), 0.35), (_score(pen, "full_game_market_modifier"), 0.45), (_score(lineup, "lineup_quality_score"), 0.35), (_score(defbase, "defense_impact_score"), 0.2), (_score(avail, "availability_score"), 0.35))) or 0.0,
        "runline": weighted_average(((_score(rv, "full_game_signal_score"), 0.55), (_score(lineup, "run_environment_modifier"), 0.45), (_score(pen, "full_game_market_modifier"), 0.35), (_score(match, "team_matchup_score"), 0.35))) or 0.0,
        "team_total": weighted_average(((_score(rv, "team_total_signal_score"), 0.65), (_score(lineup, "lineup_quality_score"), 0.45), (_score(park, "total_market_modifier"), 0.45), (100.0 - _score(pit, "pitcher_impact_score"), 0.25))) or 0.0,
        "total": weighted_average(((_score(rv, "total_signal_score"), 0.65), (_score(park, "total_market_modifier"), 0.55), (_score(pen, "total_risk_modifier"), 0.35), (_score(lineup, "run_environment_modifier"), 0.35), (100.0 - _score(defbase, "defense_impact_score"), 0.2))) or 0.0,
        "first_five_moneyline": weighted_average(((_score(rv, "first_five_signal_score"), 0.75), (_score(pit, "pitcher_impact_score"), 0.55), (_score(match, "first_five_relevance"), 0.35), (_score(lineup, "lineup_quality_score"), 0.25))) or 0.0,
        "first_five_runline": weighted_average(((_score(rv, "first_five_signal_score"), 0.7), (_score(match, "first_five_relevance"), 0.4), (_score(lineup, "run_environment_modifier"), 0.25))) or 0.0,
        "first_five_total": weighted_average(((_score(rv, "total_signal_score"), 0.45), (_score(rv, "first_five_signal_score"), 0.45), (_score(park, "total_market_modifier"), 0.4), (_score(pit, "home_run_risk_score"), 0.2))) or 0.0,
    }
    scores = {key: round(clamp(value), 2) for key, value in scores.items()}
    caps = []
    no_bet = []
    if pitch_limit_warning:
        caps.extend(["pitcher_strikeouts", "pitcher_outs_recorded"])
        no_bet.append("pitch_count_limit_caps_pitcher_props")
    if weather_delay >= 60:
        caps.extend(["pitcher_strikeouts", "pitcher_outs_recorded"])
        no_bet.append("weather_delay_risk_caps_pitcher_props")
    if "lineup_unconfirmed_caps_batter_prop_confidence" in (lineup.get("no_bet_reasons") or []):
        caps.extend(list(BATTER_PROP_MARKETS))
        no_bet.append("unconfirmed_lineup_caps_batter_props")
    if "bullpen_availability_missing_caps_full_game_confidence" in (pen.get("no_bet_reasons") or []):
        caps.extend(["moneyline", "runline", "total", "team_total"])
    selected = scores.get(market, 0.0)
    strongest = [key for key, value in sorted(scores.items(), key=lambda item: item[1], reverse=True) if value >= 58][:10]
    weak = [key for key, value in scores.items() if value < 35][:10]
    pitcher_relevance = {key: scores.get(key, 0.0) for key in PITCHER_PROP_MARKETS}
    batter_relevance = {key: scores.get(key, 0.0) for key in BATTER_PROP_MARKETS}
    team_relevance = {key: scores.get(key, 0.0) for key in TEAM_MARKETS}
    return finalize_baseball_response(
        {
            "market_relevance_scores": scores,
            "strongest_market_links": strongest,
            "weak_market_links": weak,
            "no_bet_market_reasons": compact_list(no_bet, limit=12),
            "pitcher_prop_relevance": pitcher_relevance,
            "batter_prop_relevance": batter_relevance,
            "team_market_relevance": team_relevance,
            "pitcher_prop_relevance_score": round(max(pitcher_relevance.values()), 2),
            "batter_prop_relevance_score": round(max(batter_relevance.values()), 2),
            "team_market_relevance_score": round(max(team_relevance.values()), 2),
            "selected_market_type": market,
            "selected_market_relevance_score": round(clamp(selected), 2),
            "market_confidence_caps": compact_list(caps, limit=20),
        },
        source_payload=row or {},
    )

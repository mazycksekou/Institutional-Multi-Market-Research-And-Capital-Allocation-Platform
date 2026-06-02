from __future__ import annotations

from typing import Any

from .tennis_impact_common import (
    CORRECT_SCORE_MARKETS,
    HANDICAP_MARKETS,
    MATCH_MARKETS,
    PLAYER_PROP_MARKETS,
    SET_MARKETS,
    TIEBREAK_MARKETS,
    TOTAL_MARKETS,
    clamp,
    compact_list,
    finalize_tennis_response,
    normalize_tennis_market,
    weighted_average,
)


def _score(section: dict[str, Any] | None, key: str) -> float:
    return clamp((section or {}).get(key, 0.0) or 0.0)


def evaluate_tennis_market_relevance(
    row: dict[str, Any] | None = None,
    *,
    market_type: str = "moneyline",
    serve_impact: dict[str, Any] | None = None,
    return_impact: dict[str, Any] | None = None,
    surface_context: dict[str, Any] | None = None,
    format_markov_context: dict[str, Any] | None = None,
    matchup_context: dict[str, Any] | None = None,
    pressure_tiebreak_context: dict[str, Any] | None = None,
    availability_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
    calibration: dict[str, Any] | None = None,
) -> dict[str, Any]:
    market = normalize_tennis_market(market_type)
    serve = serve_impact or {}
    ret = return_impact or {}
    surface = surface_context or {}
    fmt = format_markov_context or {}
    match = matchup_context or {}
    pressure = pressure_tiebreak_context or {}
    avail = availability_context or {}
    incentive = incentive_context or {}
    cal = calibration or {}
    calibration_status = cal.get("calibration_status", "insufficient_data")
    calibration_score = 35.0 if calibration_status == "insufficient_data" else 65.0 if calibration_status == "partial_calibration" else 85.0
    availability = _score(avail, "availability_score") or 50.0
    retirement = _score(avail, "retirement_risk_score")
    serve_return = weighted_average(((_score(serve, "serve_impact_score"), 0.45), (_score(ret, "return_impact_score"), 0.45)))
    total_hold = weighted_average(((_score(serve, "hold_stability_score"), 0.45), (_score(serve, "ace_pressure_score"), 0.25), (_score(surface, "total_games_surface_modifier"), 0.25), (_score(fmt, "tiebreak_relevance_score"), 0.25)))
    break_pressure = weighted_average(((_score(ret, "break_threat_score"), 0.45), (_score(ret, "second_serve_attack_score"), 0.25), (_score(pressure, "break_point_pressure_score"), 0.25)))
    tiebreak = weighted_average(((_score(fmt, "tiebreak_relevance_score"), 0.45), (_score(pressure, "tiebreak_likelihood_modifier"), 0.35), (_score(surface, "tiebreak_surface_modifier"), 0.3), (_score(serve, "ace_pressure_score"), 0.25)))
    match_core = weighted_average(((serve_return, 0.4), (_score(surface, "surface_fit_score"), 0.25), (_score(match, "moneyline_relevance"), 0.25), (availability, 0.3), (calibration_score, 0.2), (_score(incentive, "incentive_behavior_score"), 0.08)))
    handicap = weighted_average(((_score(fmt, "game_handicap_relevance_score"), 0.35), (serve_return, 0.3), (break_pressure, 0.25), (_score(match, "handicap_relevance"), 0.2), (100.0 - _score(pressure, "close_set_volatility_score"), 0.15)))
    total_games = weighted_average(((total_hold, 0.45), (100.0 - (break_pressure or 0.0), 0.2), (_score(fmt, "total_games_relevance_score"), 0.35), (tiebreak, 0.25), (_score(match, "total_games_relevance"), 0.15), (100.0 - retirement, 0.15)))
    set_market = weighted_average(((_score(fmt, "set_market_relevance_score"), 0.4), (_score(pressure, "first_set_pressure_score"), 0.25), (serve_return, 0.25), (availability, 0.2)))
    correct_score = weighted_average(((_score(fmt, "correct_score_relevance_score"), 0.45), (calibration_score, 0.25), (100.0 - retirement, 0.3)))
    scores = {
        "moneyline": match_core or 0.0,
        "match_winner": match_core or 0.0,
        "set_handicap": weighted_average(((handicap, 0.4), (_score(fmt, "set_market_relevance_score"), 0.25))) or 0.0,
        "game_handicap": handicap or 0.0,
        "total_games": total_games or 0.0,
        "total_sets": weighted_average(((set_market, 0.35), (total_games, 0.25), (_score(fmt, "total_games_relevance_score"), 0.25))) or 0.0,
        "correct_score": correct_score or 0.0,
        "set_betting": set_market or 0.0,
        "first_set_winner": weighted_average(((set_market, 0.35), (_score(pressure, "first_set_pressure_score"), 0.35), (_score(fmt, "set_market_relevance_score"), 0.2))) or 0.0,
        "first_set_total_games": weighted_average(((total_games, 0.35), (tiebreak, 0.25), (_score(pressure, "first_set_pressure_score"), 0.2))) or 0.0,
        "first_set_handicap": handicap or 0.0,
        "first_set_correct_score": correct_score * 0.85 if correct_score else 0.0,
        "player_to_win_a_set": set_market or 0.0,
        "player_to_win_2_0": correct_score or 0.0,
        "player_to_win_2_1": correct_score or 0.0,
        "player_to_win_3_0": correct_score or 0.0,
        "player_to_win_3_1": correct_score or 0.0,
        "player_to_win_3_2": correct_score or 0.0,
        "match_tiebreak_yes_no": tiebreak or 0.0,
        "first_set_tiebreak_yes_no": weighted_average(((tiebreak, 0.45), (_score(pressure, "first_set_pressure_score"), 0.25), (_score(fmt, "tiebreak_relevance_score"), 0.25))) or 0.0,
        "aces": weighted_average(((_score(serve, "ace_prop_relevance"), 0.55), (_score(surface, "tiebreak_surface_modifier"), 0.25), (100.0 - _score(ret, "return_impact_score"), 0.2))) or 0.0,
        "double_faults": weighted_average(((_score(serve, "double_fault_prop_relevance"), 0.55), (_score(pressure, "close_set_volatility_score"), 0.25), (_score(surface, "altitude_conditions_score"), 0.1))) or 0.0,
        "first_serve_percentage": _score(serve, "first_serve_score"),
        "first_serve_points_won": _score(serve, "first_serve_score"),
        "second_serve_points_won": _score(serve, "second_serve_resilience_score"),
        "service_games_won": _score(serve, "hold_stability_score"),
        "return_games_won": _score(ret, "break_threat_score"),
        "break_points_created": _score(ret, "break_prop_relevance"),
        "break_points_converted": _score(ret, "break_point_conversion_score"),
        "break_points_saved": _score(serve, "break_point_save_score"),
        "total_points_won": serve_return or 0.0,
        "games_won": weighted_average(((handicap, 0.35), (_score(fmt, "game_handicap_relevance_score"), 0.3), (serve_return, 0.2))) or 0.0,
        "sets_won": set_market or 0.0,
    }
    scores = {key: round(clamp(value), 2) for key, value in scores.items()}
    caps: list[str] = []
    no_bet: list[str] = []
    if calibration_status == "insufficient_data":
        caps.extend(["correct_score", "match_tiebreak_yes_no", "first_set_tiebreak_yes_no"])
        no_bet.append("calibration_missing_caps_high_variance_tennis_markets")
    if "best_of_missing_caps_correct_score_total_sets" in (fmt.get("no_bet_reasons") or []):
        caps.extend(["correct_score", "total_sets"])
        no_bet.append("best_of_missing_caps_correct_score_total_sets")
    if retirement >= 45:
        caps.append(market)
        no_bet.append("retirement_risk_caps_market_review")
    if "court_speed_missing_no_court_speed_claim" in (surface.get("no_bet_reasons") or []) and market in TIEBREAK_MARKETS | TOTAL_MARKETS:
        caps.append(market)
    selected = scores.get(market, 0.0)
    strongest = [key for key, value in sorted(scores.items(), key=lambda item: item[1], reverse=True) if value >= 58][:10]
    weak = [key for key, value in scores.items() if value < 35][:10]
    return finalize_tennis_response(
        {
            "market_relevance_scores": scores,
            "strongest_market_links": strongest,
            "weak_market_links": weak,
            "no_bet_market_reasons": compact_list(no_bet, limit=12),
            "moneyline_relevance": {key: scores.get(key, 0.0) for key in MATCH_MARKETS},
            "handicap_relevance": {key: scores.get(key, 0.0) for key in HANDICAP_MARKETS},
            "total_games_relevance": {key: scores.get(key, 0.0) for key in TOTAL_MARKETS},
            "set_market_relevance": {key: scores.get(key, 0.0) for key in SET_MARKETS | CORRECT_SCORE_MARKETS},
            "tiebreak_relevance": {key: scores.get(key, 0.0) for key in TIEBREAK_MARKETS},
            "player_prop_relevance": {key: scores.get(key, 0.0) for key in PLAYER_PROP_MARKETS},
            "selected_market_type": market,
            "selected_market_relevance_score": round(clamp(selected), 2),
            "market_confidence_caps": compact_list(caps, limit=20),
        },
        source_payload=row or {},
    )

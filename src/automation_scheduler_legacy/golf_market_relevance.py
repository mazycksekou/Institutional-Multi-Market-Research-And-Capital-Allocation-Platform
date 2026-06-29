from __future__ import annotations

from typing import Any

from .golf_impact_common import (
    CUT_MARKETS,
    MATCHUP_MARKETS,
    OUTRIGHT_MARKETS,
    PLAYER_PROP_MARKETS,
    ROUND_MARKETS,
    SCORE_MARKETS,
    TOP_FINISH_MARKETS,
    clamp,
    compact_list,
    finalize_golf_response,
    normalize_golf_market,
    weighted_average,
)


def _score(section: dict[str, Any] | None, key: str) -> float:
    return clamp((section or {}).get(key, 0.0) or 0.0)


def evaluate_golf_market_relevance(
    row: dict[str, Any] | None = None,
    *,
    market_type: str = "top_20",
    strokes_gained_impact: dict[str, Any] | None = None,
    off_tee_impact: dict[str, Any] | None = None,
    approach_impact: dict[str, Any] | None = None,
    short_game_putting_context: dict[str, Any] | None = None,
    course_fit_context: dict[str, Any] | None = None,
    weather_wave_context: dict[str, Any] | None = None,
    field_tournament_context: dict[str, Any] | None = None,
    availability_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
    calibration: dict[str, Any] | None = None,
) -> dict[str, Any]:
    market = normalize_golf_market(market_type)
    sg = strokes_gained_impact or {}
    ott = off_tee_impact or {}
    app = approach_impact or {}
    short = short_game_putting_context or {}
    course = course_fit_context or {}
    weather = weather_wave_context or {}
    field = field_tournament_context or {}
    avail = availability_context or {}
    incentive = incentive_context or {}
    cal = calibration or {}
    calibration_status = cal.get("calibration_status", "insufficient_data")
    calibration_score = 35.0 if calibration_status == "insufficient_data" else 65.0 if calibration_status == "partial_calibration" else 85.0
    volatility = max(_score(sg, "volatility_score"), _score(short, "putting_volatility_score"))
    availability = _score(avail, "availability_score") or 50.0
    course_fit = _score(course, "course_fit_score")
    field_mod = _score(field, "field_strength_score")
    scores = {
        "outright_winner": weighted_average(((_score(sg, "strokes_gained_score"), 0.55), (_score(sg, "tee_to_green_score"), 0.45), (_score(app, "approach_score"), 0.35), (_score(short, "putting_score"), 0.18), (course_fit, 0.35), (100.0 - field_mod if field_mod else None, 0.25), (100.0 - volatility, 0.25), (_score(weather, "market_confidence_modifier"), 0.15), (calibration_score, 0.3))) or 0.0,
        "top_5": weighted_average(((_score(sg, "strokes_gained_score"), 0.55), (_score(sg, "tee_to_green_score"), 0.45), (course_fit, 0.3), (100.0 - volatility, 0.25), (calibration_score, 0.2))) or 0.0,
        "top_10": weighted_average(((_score(sg, "strokes_gained_score"), 0.55), (_score(sg, "tee_to_green_score"), 0.45), (course_fit, 0.35), (_score(sg, "cut_made_profile_score"), 0.2), (100.0 - volatility, 0.2))) or 0.0,
        "top_20": weighted_average(((_score(sg, "strokes_gained_score"), 0.55), (_score(sg, "tee_to_green_score"), 0.45), (course_fit, 0.35), (_score(sg, "cut_made_profile_score"), 0.35), (availability, 0.25))) or 0.0,
        "top_30": weighted_average(((_score(sg, "strokes_gained_score"), 0.45), (_score(sg, "cut_made_profile_score"), 0.45), (course_fit, 0.25), (availability, 0.25))) or 0.0,
        "top_40": weighted_average(((_score(sg, "strokes_gained_score"), 0.4), (_score(sg, "cut_made_profile_score"), 0.55), (availability, 0.25))) or 0.0,
        "make_cut": weighted_average(((_score(sg, "tee_to_green_score"), 0.45), (_score(sg, "cut_made_profile_score"), 0.65), (_score(sg, "birdie_bogey_score"), 0.35), (course_fit, 0.25), (availability, 0.35), (100.0 - _score(field, "cut_risk_modifier"), 0.25))) or 0.0,
        "miss_cut": weighted_average(((100.0 - _score(sg, "cut_made_profile_score"), 0.65), (_score(field, "cut_risk_modifier"), 0.45), (100.0 - availability, 0.35), (volatility, 0.25))) or 0.0,
        "tournament_matchup": weighted_average(((_score(sg, "strokes_gained_score"), 0.45), (_score(sg, "tee_to_green_score"), 0.45), (course_fit, 0.35), (100.0 - volatility, 0.25), (availability, 0.25))) or 0.0,
        "round_matchup": weighted_average(((_score(sg, "strokes_gained_score"), 0.35), (_score(weather, "round_score_modifier"), 0.45), (_score(sg, "scoring_score"), 0.35), (100.0 - volatility, 0.15))) or 0.0,
        "first_round_leader": weighted_average(((_score(sg, "scoring_score"), 0.35), (_score(weather, "wave_draw_score"), 0.45), (_score(weather, "round_score_modifier"), 0.35), (_score(short, "putting_score"), 0.25), (volatility, 0.25), (calibration_score, 0.1))) or 0.0,
        "top_nationality": 0.0,
        "top_region": 0.0,
        "round_score": weighted_average(((_score(sg, "scoring_score"), 0.45), (_score(weather, "scoring_condition_modifier"), 0.45), (course_fit, 0.25), (100.0 - volatility, 0.2))) or 0.0,
        "total_score": weighted_average(((_score(sg, "scoring_score"), 0.5), (course_fit, 0.35), (_score(weather, "scoring_condition_modifier"), 0.25), (_score(sg, "cut_made_profile_score"), 0.2))) or 0.0,
        "birdies_or_better": weighted_average(((_score(sg, "birdie_bogey_score"), 0.5), (_score(app, "scoring_opportunity_score"), 0.35), (_score(short, "putting_score"), 0.25), (_score(course, "distance_bucket_fit_score"), 0.2))) or 0.0,
        "bogeys_or_worse": weighted_average(((100.0 - _score(sg, "birdie_bogey_score"), 0.45), (_score(field, "cut_risk_modifier"), 0.2), (_score(course, "hazard_risk_score"), 0.25), (volatility, 0.2))) or 0.0,
        "fairways_hit": weighted_average(((_score(ott, "accuracy_score"), 0.55), (100.0 - _score(ott, "dispersion_risk_score"), 0.25), (_score(ott, "course_off_tee_fit_score"), 0.25))) or 0.0,
        "greens_in_regulation": weighted_average(((_score(app, "approach_score"), 0.55), (_score(app, "gir_relevance_score"), 0.55), (_score(course, "architecture_fit_score"), 0.2))) or 0.0,
        "driving_distance": weighted_average(((_score(ott, "distance_advantage_score"), 0.75), (_score(ott, "course_off_tee_fit_score"), 0.25), (_score(weather, "wind_fit_score"), 0.15))) or 0.0,
        "longest_drive": weighted_average(((_score(ott, "distance_advantage_score"), 0.75), (_score(weather, "wind_fit_score"), 0.2), (100.0 - _score(ott, "dispersion_risk_score"), 0.15))) or 0.0,
        "putts": weighted_average(((_score(short, "putting_score"), 0.45), (_score(short, "grass_fit_score"), 0.25), (100.0 - _score(app, "gir_relevance_score"), 0.2))) or 0.0,
        "three_putts": weighted_average(((_score(short, "three_putt_risk_score"), 0.7), (_score(short, "putting_volatility_score"), 0.35), (_score(course, "grass_surface_fit_score"), 0.15))) or 0.0,
        "eagles": weighted_average(((_score(sg, "birdie_bogey_score"), 0.35), (_score(ott, "distance_advantage_score"), 0.35), (_score(course, "architecture_fit_score"), 0.25))) or 0.0,
        "holes_in_one": weighted_average(((_score(app, "approach_score"), 0.25), (_score(sg, "volatility_score"), 0.2), (_score(course, "distance_bucket_fit_score"), 0.15))) or 0.0,
    }
    scores["top_nationality"] = scores["top_20"]
    scores["top_region"] = scores["top_20"]
    scores = {key: round(clamp(value), 2) for key, value in scores.items()}
    caps: list[str] = []
    no_bet: list[str] = []
    if calibration_status == "insufficient_data":
        caps.extend(["outright_winner", "first_round_leader"])
        no_bet.append("calibration_missing_caps_high_variance_markets")
    if not field_mod and market in OUTRIGHT_MARKETS | TOP_FINISH_MARKETS:
        caps.append(market)
        no_bet.append("field_strength_missing_caps_outright_top_finish")
    if "no_cut_event_disables_make_miss_cut_logic" in (field.get("no_bet_reasons") or []) and market in CUT_MARKETS:
        caps.append(market)
        no_bet.append("no_cut_event_no_cut_market_review")
    if "tee_time_wave_missing_no_wave_draw_claim" in (weather.get("no_bet_reasons") or []) and market in ROUND_MARKETS:
        caps.append(market)
        no_bet.append("missing_wave_caps_round_market")
    selected = scores.get(market, 0.0)
    strongest = [key for key, value in sorted(scores.items(), key=lambda item: item[1], reverse=True) if value >= 58][:10]
    weak = [key for key, value in scores.items() if value < 35][:10]
    return finalize_golf_response(
        {
            "market_relevance_scores": scores,
            "strongest_market_links": strongest,
            "weak_market_links": weak,
            "no_bet_market_reasons": compact_list(no_bet, limit=12),
            "outright_relevance": {key: scores.get(key, 0.0) for key in OUTRIGHT_MARKETS},
            "top_finish_relevance": {key: scores.get(key, 0.0) for key in TOP_FINISH_MARKETS},
            "cut_market_relevance": {key: scores.get(key, 0.0) for key in CUT_MARKETS},
            "matchup_relevance": {key: scores.get(key, 0.0) for key in MATCHUP_MARKETS},
            "round_market_relevance": {key: scores.get(key, 0.0) for key in ROUND_MARKETS | {"round_score", "total_score"}},
            "player_prop_relevance": {key: scores.get(key, 0.0) for key in PLAYER_PROP_MARKETS | SCORE_MARKETS},
            "selected_market_type": market,
            "selected_market_relevance_score": round(clamp(selected), 2),
            "market_confidence_caps": compact_list(caps, limit=20),
        },
        source_payload=row or {},
    )

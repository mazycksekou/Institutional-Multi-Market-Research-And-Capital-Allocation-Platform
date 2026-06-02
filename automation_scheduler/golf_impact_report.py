from __future__ import annotations

from typing import Any

from .golf_approach_impact import evaluate_golf_approach_impact
from .golf_availability_context import evaluate_golf_availability_context
from .golf_course_fit_context import evaluate_golf_course_fit_context
from .golf_data_availability import evaluate_golf_data_availability
from .golf_field_tournament_context import evaluate_golf_field_tournament_context
from .golf_impact_calibration import evaluate_golf_impact_calibration
from .golf_impact_common import ALLOWED_GOLF_REVIEW_STATUSES, FORBIDDEN_GOLF_ACTIONS, CUT_MARKETS, OUTRIGHT_MARKETS, PLAYER_PROP_MARKETS, clamp, compact_list, finalize_golf_response, normalize_golf_market, normalize_golf_sport, weighted_average
from .golf_impact_readiness import build_golf_impact_readiness
from .golf_impact_red_team import evaluate_golf_impact_red_team
from .golf_incentive_context import evaluate_golf_incentive_context
from .golf_market_relevance import evaluate_golf_market_relevance
from .golf_off_tee_impact import evaluate_golf_off_tee_impact
from .golf_short_game_putting_context import evaluate_golf_short_game_putting_context
from .golf_strokes_gained_impact import evaluate_golf_strokes_gained_impact
from .golf_weather_wave_context import evaluate_golf_weather_wave_context


def _merge(*items: dict[str, Any] | None) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for item in items:
        if isinstance(item, dict):
            row.update(item)
    return row


def _combine_missing(*sections: dict[str, Any]) -> list[str]:
    values: list[Any] = []
    for section in sections:
        if isinstance(section, dict):
            values.extend(section.get("missing_inputs") or [])
    return compact_list(values, limit=100)


def _recommend(*, tier: int, market: str, selected_relevance: float, calibration_status: str, no_bet: list[str], red_team_adjustment: str, unsupported_format: bool) -> str:
    if tier == 0:
        return "DATA_INSUFFICIENT"
    if unsupported_format and market not in {"tournament_matchup", "round_matchup"}:
        return "DATA_INSUFFICIENT"
    if red_team_adjustment == "NO_BET" or any(reason in no_bet for reason in ("withdrawal_risk_hard_warning", "cut_rule_context_confusion", "outright_longshot_overconfidence")):
        return "NO_BET"
    if market in CUT_MARKETS and any("no_cut_event" in str(reason) for reason in no_bet):
        return "NO_BET"
    if calibration_status == "insufficient_data":
        if selected_relevance >= 55 and tier >= 2:
            return "WATCHLIST_REVIEW"
        return "CALIBRATION_ONLY"
    if tier >= 3 and selected_relevance >= 65 and calibration_status == "calibration_ready" and not no_bet:
        return "ACTIVE_REVIEW"
    if market in PLAYER_PROP_MARKETS:
        return "PLAYER_PROP_REVIEW_ONLY"
    if market in OUTRIGHT_MARKETS:
        return "OUTRIGHT_REVIEW_ONLY"
    if market in CUT_MARKETS:
        return "CUT_MARKET_REVIEW_ONLY"
    return "WATCHLIST_REVIEW"


def build_golf_impact_diagnostics(
    *,
    sport: str = "golf",
    market_type: str = "top_20",
    tournament_context: dict[str, Any] | None = None,
    player_context: dict[str, Any] | None = None,
    strokes_gained_context: dict[str, Any] | None = None,
    off_tee_context: dict[str, Any] | None = None,
    approach_context: dict[str, Any] | None = None,
    around_green_context: dict[str, Any] | None = None,
    putting_context: dict[str, Any] | None = None,
    course_context: dict[str, Any] | None = None,
    weather_context: dict[str, Any] | None = None,
    wave_context: dict[str, Any] | None = None,
    field_context: dict[str, Any] | None = None,
    form_context: dict[str, Any] | None = None,
    availability_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
    calibration_context: dict[str, Any] | None = None,
    simulation_context: dict[str, Any] | None = None,
    tracking_context: dict[str, Any] | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    normalized_sport = normalize_golf_sport(sport)
    market = normalize_golf_market(market_type)
    source_payload = {
        "sport": sport,
        "market_type": market_type,
        "tournament_context": tournament_context or {},
        "player_context": player_context or {},
        "strokes_gained_context": strokes_gained_context or {},
        "off_tee_context": off_tee_context or {},
        "approach_context": approach_context or {},
        "around_green_context": around_green_context or {},
        "putting_context": putting_context or {},
        "course_context": course_context or {},
        "weather_context": weather_context or {},
        "wave_context": wave_context or {},
        "field_context": field_context or {},
        "form_context": form_context or {},
        "availability_context": availability_context or {},
        "incentive_context": incentive_context or {},
        "calibration_context": calibration_context or {},
        "simulation_context": simulation_context or {},
        "tracking_context": tracking_context or {},
        "dry_run": dry_run,
    }
    all_row = _merge(
        tournament_context,
        player_context,
        strokes_gained_context,
        off_tee_context,
        approach_context,
        around_green_context,
        putting_context,
        course_context,
        weather_context,
        wave_context,
        field_context,
        form_context,
        availability_context,
        incentive_context,
        calibration_context,
        simulation_context,
        tracking_context,
    )
    data = evaluate_golf_data_availability(
        normalized_sport,
        market_type=market,
        tournament_context=tournament_context,
        player_context=player_context,
        strokes_gained_context=strokes_gained_context,
        off_tee_context=off_tee_context,
        approach_context=approach_context,
        around_green_context=around_green_context,
        putting_context=putting_context,
        course_context=course_context,
        weather_context=weather_context,
        wave_context=wave_context,
        field_context=field_context,
        form_context=form_context,
        availability_context=availability_context,
        incentive_context=incentive_context,
        calibration_context=calibration_context,
        simulation_context=simulation_context,
        tracking_context=tracking_context,
    )
    tier = int(data.get("data_tier", 0) or 0)
    sg = evaluate_golf_strokes_gained_impact(all_row, data_tier=tier)
    off_tee = evaluate_golf_off_tee_impact(all_row, course_fit_allowed=bool(data.get("course_fit_allowed")))
    approach = evaluate_golf_approach_impact(all_row, course_fit_allowed=bool(data.get("course_fit_allowed")))
    short_putt = evaluate_golf_short_game_putting_context(all_row)
    course = evaluate_golf_course_fit_context(all_row)
    weather = evaluate_golf_weather_wave_context(all_row)
    field = evaluate_golf_field_tournament_context(all_row)
    availability = evaluate_golf_availability_context(all_row)
    incentive = evaluate_golf_incentive_context(all_row)
    skill_group = "APPROACH" if market in {"greens_in_regulation", "birdies_or_better"} else "PUTTING" if market in {"putts", "three_putts"} else "OFF_THE_TEE" if market in {"fairways_hit", "driving_distance", "longest_drive"} else "COURSE_FIT"
    calibration = evaluate_golf_impact_calibration(calibration_context or {}, sport=normalized_sport, market_type=market, skill_group=skill_group, data_tier=tier)
    market_rel = evaluate_golf_market_relevance(
        all_row,
        market_type=market,
        strokes_gained_impact=sg,
        off_tee_impact=off_tee,
        approach_impact=approach,
        short_game_putting_context=short_putt,
        course_fit_context=course,
        weather_wave_context=weather,
        field_tournament_context=field,
        availability_context=availability,
        incentive_context=incentive,
        calibration=calibration,
    )
    red_team = evaluate_golf_impact_red_team(
        market_type=market,
        data_availability=data,
        strokes_gained_impact=sg,
        off_tee_impact=off_tee,
        approach_impact=approach,
        short_game_putting_context=short_putt,
        course_fit_context=course,
        weather_wave_context=weather,
        field_tournament_context=field,
        availability_context=availability,
        incentive_context=incentive,
        calibration=calibration,
        source_payload=all_row,
    )
    no_bet = compact_list(
        [
            *(off_tee.get("no_bet_reasons") or []),
            *(approach.get("no_bet_reasons") or []),
            *(short_putt.get("no_bet_reasons") or []),
            *(course.get("no_bet_reasons") or []),
            *(weather.get("no_bet_reasons") or []),
            *(field.get("no_bet_reasons") or []),
            *(availability.get("no_bet_reasons") or []),
            *(incentive.get("no_bet_reasons") or []),
            *(market_rel.get("no_bet_market_reasons") or []),
            *(red_team.get("no_bet_reasons") or []),
        ],
        limit=50,
    )
    selected = float(market_rel.get("selected_market_relevance_score", 0.0) or 0.0)
    score = weighted_average(
        (
            (sg.get("strokes_gained_score"), 0.45),
            (approach.get("approach_score"), 0.25),
            (course.get("course_fit_score"), 0.25),
            (weather.get("market_confidence_modifier"), 0.15),
            (field.get("top_finish_market_modifier"), 0.15),
            (availability.get("availability_score"), 0.2),
            (selected, 0.3),
            (100.0 - red_team.get("downgrade_score", 0.0), 0.25),
        )
    )
    recommended = _recommend(
        tier=tier,
        market=market,
        selected_relevance=selected,
        calibration_status=str(calibration.get("calibration_status", "insufficient_data")),
        no_bet=no_bet,
        red_team_adjustment=str(red_team.get("recommended_action_adjustment", "NO_CHANGE")),
        unsupported_format=bool(field.get("unsupported_format")),
    )
    markets_to_review = [] if recommended in {"DATA_INSUFFICIENT", "NO_BET", "CALIBRATION_ONLY"} else compact_list([market, *(market_rel.get("strongest_market_links") or [])], limit=8)
    payload = {
        "ok": True,
        "status": "golf_strokes_gained_impact_complete",
        "sport": normalized_sport,
        "market_type": market,
        "data_tier": tier,
        "tier_name": data.get("tier_name"),
        "player_level_allowed": bool(data.get("player_level_allowed", False)),
        "course_fit_allowed": bool(data.get("course_fit_allowed", False)),
        "weather_wave_allowed": bool(data.get("weather_wave_allowed", False)),
        "simulation_allowed": bool(data.get("simulation_allowed", False)),
        "data_availability": data,
        "strokes_gained_impact": sg,
        "off_tee_impact": off_tee,
        "approach_impact": approach,
        "short_game_putting_context": short_putt,
        "course_fit_context": course,
        "weather_wave_context": weather,
        "field_tournament_context": field,
        "availability_context": availability,
        "incentive_context": incentive,
        "market_relevance": market_rel,
        "calibration": calibration,
        "calibration_status": calibration.get("calibration_status", "insufficient_data"),
        "red_team": red_team,
        "golf_impact_score": round(clamp(score or 0.0), 2),
        "recommended_review_status": recommended,
        "markets_to_review": markets_to_review,
        "no_bet_reasons": no_bet,
        "missing_inputs": _combine_missing(sg, off_tee, approach, short_putt, course, weather, field, availability, incentive),
        "next_data_to_collect": compact_list([*(data.get("next_data_to_collect") or []), *(calibration.get("next_required_data") or [])], limit=30),
        "allowed_review_statuses": list(ALLOWED_GOLF_REVIEW_STATUSES),
        "forbidden_recommendations_rejected": list(FORBIDDEN_GOLF_ACTIONS),
        "dry_run": True,
    }
    return finalize_golf_response(payload, source_payload=source_payload)


def build_golf_impact_readiness_report() -> dict[str, Any]:
    return build_golf_impact_readiness()

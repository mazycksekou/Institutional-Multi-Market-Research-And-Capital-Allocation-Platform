from __future__ import annotations

from typing import Any

from .tennis_availability_context import evaluate_tennis_availability_context
from .tennis_data_availability import evaluate_tennis_data_availability
from .tennis_format_markov_context import evaluate_tennis_format_markov_context
from .tennis_impact_calibration import evaluate_tennis_impact_calibration
from .tennis_impact_common import (
    ALLOWED_TENNIS_REVIEW_STATUSES,
    CORRECT_SCORE_MARKETS,
    FORBIDDEN_TENNIS_ACTIONS,
    PLAYER_PROP_MARKETS,
    TIEBREAK_MARKETS,
    clamp,
    compact_list,
    finalize_tennis_response,
    normalize_tennis_market,
    normalize_tennis_sport,
    weighted_average,
)
from .tennis_impact_readiness import build_tennis_impact_readiness
from .tennis_impact_red_team import evaluate_tennis_impact_red_team
from .tennis_incentive_context import evaluate_tennis_incentive_context
from .tennis_market_relevance import evaluate_tennis_market_relevance
from .tennis_matchup_context import evaluate_tennis_matchup_context
from .tennis_pressure_tiebreak_context import evaluate_tennis_pressure_tiebreak_context
from .tennis_return_impact import evaluate_tennis_return_impact
from .tennis_serve_impact import evaluate_tennis_serve_impact
from .tennis_surface_context import evaluate_tennis_surface_context


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
    return compact_list(values, limit=120)


def _recommend(*, tier: int, market: str, selected: float, calibration_status: str, no_bet: list[str], red_team_adjustment: str) -> str:
    if tier == 0:
        return "DATA_INSUFFICIENT"
    if red_team_adjustment == "NO_BET" or any(
        reason in no_bet
        for reason in (
            "retirement_risk_hard_warning",
            "retirement_risk_ignored",
            "correct_score_overconfidence",
            "best_of_format_confusion",
            "serve_placement_missing_but_claimed",
            "shot_pattern_missing_but_claimed",
            "court_speed_missing_but_claimed",
        )
    ):
        return "NO_BET"
    if calibration_status == "insufficient_data":
        if selected >= 55 and tier >= 2:
            return "WATCHLIST_REVIEW"
        return "CALIBRATION_ONLY"
    if tier >= 3 and selected >= 65 and calibration_status == "calibration_ready" and not no_bet:
        return "ACTIVE_REVIEW"
    if market in PLAYER_PROP_MARKETS:
        return "PLAYER_PROP_REVIEW_ONLY"
    if market in TIEBREAK_MARKETS:
        return "TIEBREAK_REVIEW_ONLY"
    if market in CORRECT_SCORE_MARKETS:
        return "MARKET_REVIEW_ONLY"
    return "SERVE_RETURN_REVIEW_ONLY" if tier >= 2 else "MARKET_REVIEW_ONLY"


def build_tennis_impact_diagnostics(
    *,
    sport: str = "tennis",
    market_type: str = "moneyline",
    match_context: dict[str, Any] | None = None,
    player_a_context: dict[str, Any] | None = None,
    player_b_context: dict[str, Any] | None = None,
    serve_context: dict[str, Any] | None = None,
    return_context: dict[str, Any] | None = None,
    surface_context: dict[str, Any] | None = None,
    format_context: dict[str, Any] | None = None,
    pressure_context: dict[str, Any] | None = None,
    tiebreak_context: dict[str, Any] | None = None,
    matchup_context: dict[str, Any] | None = None,
    conditions_context: dict[str, Any] | None = None,
    availability_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
    calibration_context: dict[str, Any] | None = None,
    point_context: dict[str, Any] | None = None,
    tracking_context: dict[str, Any] | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    normalized_sport = normalize_tennis_sport(sport)
    market = normalize_tennis_market(market_type)
    source_payload = {
        "sport": sport,
        "market_type": market_type,
        "match_context": match_context or {},
        "player_a_context": player_a_context or {},
        "player_b_context": player_b_context or {},
        "serve_context": serve_context or {},
        "return_context": return_context or {},
        "surface_context": surface_context or {},
        "format_context": format_context or {},
        "pressure_context": pressure_context or {},
        "tiebreak_context": tiebreak_context or {},
        "matchup_context": matchup_context or {},
        "conditions_context": conditions_context or {},
        "availability_context": availability_context or {},
        "incentive_context": incentive_context or {},
        "calibration_context": calibration_context or {},
        "point_context": point_context or {},
        "tracking_context": tracking_context or {},
        "dry_run": dry_run,
    }
    all_row = _merge(
        match_context,
        player_a_context,
        player_b_context,
        serve_context,
        return_context,
        surface_context,
        format_context,
        pressure_context,
        tiebreak_context,
        matchup_context,
        conditions_context,
        availability_context,
        incentive_context,
        calibration_context,
        point_context,
        tracking_context,
    )
    data = evaluate_tennis_data_availability(
        normalized_sport,
        market_type=market,
        match_context=match_context,
        player_a_context=player_a_context,
        player_b_context=player_b_context,
        serve_context=serve_context,
        return_context=return_context,
        surface_context=surface_context,
        format_context=format_context,
        pressure_context=pressure_context,
        tiebreak_context=tiebreak_context,
        matchup_context=matchup_context,
        conditions_context=conditions_context,
        availability_context=availability_context,
        incentive_context=incentive_context,
        calibration_context=calibration_context,
        point_context=point_context,
        tracking_context=tracking_context,
    )
    tier = int(data.get("data_tier", 0) or 0)
    serve = evaluate_tennis_serve_impact(all_row)
    ret = evaluate_tennis_return_impact(all_row)
    surface = evaluate_tennis_surface_context(all_row)
    fmt = evaluate_tennis_format_markov_context(all_row)
    matchup = evaluate_tennis_matchup_context(all_row)
    pressure = evaluate_tennis_pressure_tiebreak_context(all_row)
    availability = evaluate_tennis_availability_context(all_row)
    incentive = evaluate_tennis_incentive_context(all_row)
    calibration = evaluate_tennis_impact_calibration(
        calibration_context or {},
        sport=normalized_sport,
        market_type=market,
        tour=(match_context or {}).get("tour"),
        surface=(match_context or {}).get("surface") or (surface_context or {}).get("surface"),
        format_bucket=str((match_context or {}).get("best_of") or (format_context or {}).get("best_of") or ""),
        data_tier=tier,
    )
    market_rel = evaluate_tennis_market_relevance(
        all_row,
        market_type=market,
        serve_impact=serve,
        return_impact=ret,
        surface_context=surface,
        format_markov_context=fmt,
        matchup_context=matchup,
        pressure_tiebreak_context=pressure,
        availability_context=availability,
        incentive_context=incentive,
        calibration=calibration,
    )
    red_team = evaluate_tennis_impact_red_team(
        market_type=market,
        data_availability=data,
        serve_impact=serve,
        return_impact=ret,
        surface_context=surface,
        format_markov_context=fmt,
        matchup_context=matchup,
        pressure_tiebreak_context=pressure,
        availability_context=availability,
        incentive_context=incentive,
        calibration=calibration,
        source_payload=all_row,
    )
    no_bet = compact_list(
        [
            *(serve.get("no_bet_reasons") or []),
            *(ret.get("no_bet_reasons") or []),
            *(surface.get("no_bet_reasons") or []),
            *(fmt.get("no_bet_reasons") or []),
            *(matchup.get("no_bet_reasons") or []),
            *(pressure.get("no_bet_reasons") or []),
            *(availability.get("no_bet_reasons") or []),
            *(incentive.get("no_bet_reasons") or []),
            *(market_rel.get("no_bet_market_reasons") or []),
            *(red_team.get("no_bet_reasons") or []),
        ],
        limit=60,
    )
    selected = float(market_rel.get("selected_market_relevance_score", 0.0) or 0.0)
    score = weighted_average(
        (
            (serve.get("serve_impact_score"), 0.35),
            (ret.get("return_impact_score"), 0.35),
            (surface.get("surface_fit_score"), 0.18),
            (fmt.get("markov_context_score"), 0.2),
            (matchup.get("matchup_advantage_score"), 0.15),
            (pressure.get("pressure_score"), 0.12),
            (availability.get("availability_score"), 0.22),
            (selected, 0.3),
            (100.0 - red_team.get("downgrade_score", 0.0), 0.25),
        )
    )
    recommended = _recommend(
        tier=tier,
        market=market,
        selected=selected,
        calibration_status=str(calibration.get("calibration_status", "insufficient_data")),
        no_bet=no_bet,
        red_team_adjustment=str(red_team.get("recommended_action_adjustment", "NO_CHANGE")),
    )
    markets_to_review = [] if recommended in {"DATA_INSUFFICIENT", "NO_BET", "CALIBRATION_ONLY"} else compact_list([market, *(market_rel.get("strongest_market_links") or [])], limit=8)
    payload = {
        "ok": True,
        "status": "tennis_serve_return_impact_complete",
        "sport": normalized_sport,
        "market_type": market,
        "data_tier": tier,
        "tier_name": data.get("tier_name"),
        "player_level_allowed": bool(data.get("player_level_allowed", False)),
        "serve_return_allowed": bool(data.get("serve_return_allowed", False)),
        "surface_matchup_allowed": bool(data.get("surface_matchup_allowed", False)),
        "point_level_allowed": bool(data.get("point_level_allowed", False)),
        "tracking_level_allowed": bool(data.get("tracking_level_allowed", False)),
        "data_availability": data,
        "serve_impact": serve,
        "return_impact": ret,
        "surface_context": surface,
        "format_markov_context": fmt,
        "matchup_context": matchup,
        "pressure_tiebreak_context": pressure,
        "availability_context": availability,
        "incentive_context": incentive,
        "market_relevance": market_rel,
        "calibration": calibration,
        "calibration_status": calibration.get("calibration_status", "insufficient_data"),
        "red_team": red_team,
        "tennis_impact_score": round(clamp(score or 0.0), 2),
        "recommended_review_status": recommended,
        "markets_to_review": markets_to_review,
        "no_bet_reasons": no_bet,
        "missing_inputs": _combine_missing(serve, ret, surface, fmt, matchup, pressure, availability, incentive),
        "next_data_to_collect": compact_list([*(data.get("next_data_to_collect") or []), *(calibration.get("next_required_data") or [])], limit=30),
        "allowed_review_statuses": list(ALLOWED_TENNIS_REVIEW_STATUSES),
        "forbidden_recommendations_rejected": list(FORBIDDEN_TENNIS_ACTIONS),
        "dry_run": True,
    }
    return finalize_tennis_response(payload, source_payload=source_payload)


def build_tennis_impact_readiness_report() -> dict[str, Any]:
    return build_tennis_impact_readiness()

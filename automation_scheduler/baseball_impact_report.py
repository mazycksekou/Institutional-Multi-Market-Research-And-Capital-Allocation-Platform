from __future__ import annotations

from typing import Any

from .baseball_availability_context import evaluate_baseball_availability_context
from .baseball_batter_impact import evaluate_baseball_batter_impact
from .baseball_bullpen_context import evaluate_baseball_bullpen_context
from .baseball_data_availability import evaluate_baseball_data_availability
from .baseball_defense_baserunning_context import evaluate_baseball_defense_baserunning_context
from .baseball_impact_calibration import evaluate_baseball_impact_calibration
from .baseball_impact_common import (
    ALLOWED_BASEBALL_REVIEW_STATUSES,
    BATTER_PROP_MARKETS,
    FIRST_FIVE_MARKETS,
    FORBIDDEN_BASEBALL_ACTIONS,
    PITCHER_PROP_MARKETS,
    PLAYER_PROP_MARKETS,
    TEAM_MARKETS,
    clamp,
    compact_list,
    finalize_baseball_response,
    normalize_baseball_market,
    normalize_baseball_role,
    normalize_baseball_sport,
)
from .baseball_impact_red_team import evaluate_baseball_impact_red_team
from .baseball_incentive_context import evaluate_baseball_incentive_context
from .baseball_lineup_context import evaluate_baseball_lineup_context
from .baseball_market_relevance import evaluate_baseball_market_relevance
from .baseball_matchup_context import evaluate_baseball_matchup_context
from .baseball_park_weather_umpire_context import evaluate_baseball_park_weather_umpire_context
from .baseball_pitcher_impact import evaluate_baseball_pitcher_impact
from .baseball_run_value_impact import evaluate_baseball_run_value_impact


def _merge(*items: dict[str, Any] | None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for item in items:
        if isinstance(item, dict):
            out.update(item)
    return out


def _missing(*sections: dict[str, Any]) -> list[str]:
    values: list[Any] = []
    for section in sections:
        for key in ("missing_inputs", "missing_pitcher_inputs", "missing_batter_inputs", "missing_pitch_tracking_inputs", "missing_bat_tracking_inputs"):
            values.extend(section.get(key) or [])
    return compact_list(values, limit=80)


def _recommend(*, tier: int, market: str, selected_relevance: float, calibration_status: str, no_bet: list[str], pitcher_allowed: bool, batter_allowed: bool, red_team_adjustment: str) -> str:
    if tier <= 0:
        return "DATA_INSUFFICIENT"
    if market in PITCHER_PROP_MARKETS and not pitcher_allowed:
        return "DATA_INSUFFICIENT"
    if market in BATTER_PROP_MARKETS and not batter_allowed:
        return "DATA_INSUFFICIENT"
    if no_bet or red_team_adjustment == "NO_BET":
        return "NO_BET"
    if red_team_adjustment == "DATA_INSUFFICIENT":
        return "DATA_INSUFFICIENT"
    if calibration_status == "calibration_ready" and selected_relevance >= 70:
        return "ACTIVE_REVIEW"
    if calibration_status == "insufficient_data":
        return "CALIBRATION_ONLY"
    if market in PITCHER_PROP_MARKETS:
        return "PITCHER_PROP_REVIEW_ONLY" if selected_relevance >= 50 else "WATCHLIST_REVIEW"
    if market in BATTER_PROP_MARKETS:
        return "BATTER_PROP_REVIEW_ONLY" if selected_relevance >= 50 else "WATCHLIST_REVIEW"
    if market in TEAM_MARKETS:
        return "TEAM_MARKET_REVIEW_ONLY" if selected_relevance >= 50 else "MARKET_REVIEW_ONLY"
    return "WATCHLIST_REVIEW"


def build_baseball_impact_diagnostics(
    *,
    sport: str = "baseball_mlb",
    market_type: str = "moneyline",
    game_context: dict[str, Any] | None = None,
    team_context: dict[str, Any] | None = None,
    pitcher_context: dict[str, Any] | None = None,
    batter_context: dict[str, Any] | None = None,
    lineup_context: dict[str, Any] | None = None,
    bullpen_context: dict[str, Any] | None = None,
    catcher_context: dict[str, Any] | None = None,
    defense_context: dict[str, Any] | None = None,
    baserunning_context: dict[str, Any] | None = None,
    park_weather_context: dict[str, Any] | None = None,
    umpire_context: dict[str, Any] | None = None,
    availability_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
    calibration_context: dict[str, Any] | None = None,
    tracking_context: dict[str, Any] | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    normalized_sport = normalize_baseball_sport(sport)
    market = normalize_baseball_market(market_type)
    source_payload = {
        "sport": sport,
        "market_type": market_type,
        "game_context": game_context or {},
        "team_context": team_context or {},
        "pitcher_context": pitcher_context or {},
        "batter_context": batter_context or {},
        "lineup_context": lineup_context or {},
        "bullpen_context": bullpen_context or {},
        "catcher_context": catcher_context or {},
        "defense_context": defense_context or {},
        "baserunning_context": baserunning_context or {},
        "park_weather_context": park_weather_context or {},
        "umpire_context": umpire_context or {},
        "availability_context": availability_context or {},
        "incentive_context": incentive_context or {},
        "calibration_context": calibration_context or {},
        "tracking_context": tracking_context or {},
        "dry_run": dry_run,
    }
    data = evaluate_baseball_data_availability(
        normalized_sport,
        market_type=market,
        game_context=game_context,
        team_context=team_context,
        pitcher_context=pitcher_context,
        batter_context=batter_context,
        lineup_context=lineup_context,
        bullpen_context=bullpen_context,
        catcher_context=catcher_context,
        defense_context=defense_context,
        baserunning_context=baserunning_context,
        park_weather_context=park_weather_context,
        umpire_context=umpire_context,
        incentive_context=incentive_context,
        calibration_context=calibration_context,
        tracking_context=tracking_context,
    )
    tier = int(data.get("data_tier", 0) or 0)
    park_ump = _merge(park_weather_context, umpire_context)
    defense_base = _merge(defense_context, baserunning_context, catcher_context)
    availability_input = _merge(availability_context, pitcher_context, bullpen_context)
    run_input = _merge(team_context, pitcher_context, batter_context, bullpen_context, park_ump, umpire_context)
    pitcher_input = _merge(pitcher_context, availability_context, tracking_context)
    batter_input = _merge(batter_context, lineup_context, tracking_context)
    matchup_input = _merge(pitcher_context, batter_context, team_context, catcher_context, umpire_context)
    run_value = evaluate_baseball_run_value_impact(run_input, data_tier=tier)
    pitcher = evaluate_baseball_pitcher_impact(pitcher_input, pitcher_level_allowed=bool(data.get("pitcher_level_allowed")), data_tier=tier)
    batter = evaluate_baseball_batter_impact(batter_input, batter_level_allowed=bool(data.get("batter_level_allowed")), data_tier=tier)
    lineup = evaluate_baseball_lineup_context(lineup_context or {})
    bullpen = evaluate_baseball_bullpen_context(bullpen_context or {})
    park_weather_umpire = evaluate_baseball_park_weather_umpire_context(park_ump)
    defense_baserunning = evaluate_baseball_defense_baserunning_context(defense_base)
    availability = evaluate_baseball_availability_context(availability_input)
    incentive = evaluate_baseball_incentive_context(incentive_context or {})
    matchup = evaluate_baseball_matchup_context(matchup_input, market_type=market)
    market_relevance = evaluate_baseball_market_relevance(
        {"market_type": market},
        market_type=market,
        run_value_impact=run_value,
        pitcher_impact=pitcher,
        batter_impact=batter,
        matchup_context=matchup,
        lineup_context=lineup,
        bullpen_context=bullpen,
        park_weather_umpire_context=park_weather_umpire,
        defense_baserunning_context=defense_baserunning,
        availability_context=availability,
        incentive_context=incentive,
    )
    role = "UNKNOWN"
    if market in PITCHER_PROP_MARKETS or pitcher_context:
        role = str(pitcher.get("pitcher_role") or "STARTING_PITCHER")
    elif market in BATTER_PROP_MARKETS or batter_context:
        role = "BATTER"
    calibration = evaluate_baseball_impact_calibration(calibration_context or {}, sport=normalized_sport, market_type=market, role=role, data_tier=tier)
    red_team = evaluate_baseball_impact_red_team(
        market_type=market,
        data_availability=data,
        run_value_impact=run_value,
        pitcher_impact=pitcher,
        batter_impact=batter,
        matchup_context=matchup,
        lineup_context=lineup,
        bullpen_context=bullpen,
        park_weather_umpire_context=park_weather_umpire,
        availability_context=availability,
        incentive_context=incentive,
        calibration=calibration,
        source_payload=_merge(source_payload, game_context, team_context, pitcher_context, batter_context, lineup_context, park_weather_context, umpire_context, availability_context),
    )
    no_bet = compact_list(
        [
            *(pitcher.get("no_bet_reasons") or []),
            *(batter.get("no_bet_reasons") or []),
            *(matchup.get("no_bet_reasons") or []),
            *(lineup.get("no_bet_reasons") or []),
            *(bullpen.get("no_bet_reasons") or []),
            *(park_weather_umpire.get("no_bet_reasons") or []),
            *(defense_baserunning.get("no_bet_reasons") or []),
            *(availability.get("no_bet_reasons") or []),
            *(incentive.get("no_bet_reasons") or []),
            *(market_relevance.get("no_bet_market_reasons") or []),
            *(red_team.get("no_bet_reasons") or []),
        ],
        limit=35,
    )
    selected = float(market_relevance.get("selected_market_relevance_score", 0.0) or 0.0)
    action = _recommend(
        tier=tier,
        market=market,
        selected_relevance=selected,
        calibration_status=str(calibration.get("calibration_status") or "insufficient_data"),
        no_bet=no_bet,
        pitcher_allowed=bool(data.get("pitcher_level_allowed")),
        batter_allowed=bool(data.get("batter_level_allowed")),
        red_team_adjustment=str(red_team.get("recommended_action_adjustment") or "NO_CHANGE"),
    )
    if action not in ALLOWED_BASEBALL_REVIEW_STATUSES:
        action = "CALIBRATION_ONLY"
    score = (
        float(run_value.get("run_value_score", 0.0) or 0.0) * 0.24
        + float(pitcher.get("pitcher_impact_score", 0.0) or 0.0) * 0.18
        + float(batter.get("batter_impact_score", 0.0) or 0.0) * 0.18
        + float(matchup.get("matchup_advantage_score", 0.0) or 0.0) * 0.14
        + float(lineup.get("lineup_quality_score", 0.0) or 0.0) * 0.08
        + float(bullpen.get("bullpen_quality_score", 0.0) or 0.0) * 0.08
        + selected * 0.10
        - float(red_team.get("downgrade_score", 0.0) or 0.0) * 0.25
    )
    markets_to_review = [] if action in {"NO_BET", "DATA_INSUFFICIENT"} else market_relevance.get("strongest_market_links") or []
    missing = _missing(run_value, pitcher, batter, matchup, lineup, bullpen, park_weather_umpire, defense_baserunning, availability, incentive, red_team)
    next_data = compact_list([*(data.get("next_data_to_collect") or []), *(calibration.get("next_required_data") or []), *(red_team.get("missing_inputs") or [])], limit=35)
    payload = {
        "ok": True,
        "status": "baseball_player_impact_complete",
        "sport": normalized_sport,
        "market_type": market,
        "data_tier": tier,
        "data_availability": data,
        "run_value_impact": run_value,
        "pitcher_impact": pitcher,
        "batter_impact": batter,
        "matchup_context": matchup,
        "lineup_context": lineup,
        "bullpen_context": bullpen,
        "park_weather_umpire_context": park_weather_umpire,
        "defense_baserunning_context": defense_baserunning,
        "availability_context": availability,
        "incentive_context": incentive,
        "market_relevance": market_relevance,
        "calibration": calibration,
        "calibration_status": calibration.get("calibration_status", "insufficient_data"),
        "red_team": red_team,
        "baseball_impact_score": round(clamp(score), 2),
        "recommended_review_status": action,
        "markets_to_review": compact_list(markets_to_review, limit=12),
        "no_bet_reasons": no_bet,
        "missing_inputs": missing,
        "next_data_to_collect": next_data,
        "allowed_review_statuses": list(ALLOWED_BASEBALL_REVIEW_STATUSES),
        "forbidden_recommendations_rejected": list(FORBIDDEN_BASEBALL_ACTIONS),
        "dry_run": True,
    }
    return finalize_baseball_response(payload, source_payload=source_payload)

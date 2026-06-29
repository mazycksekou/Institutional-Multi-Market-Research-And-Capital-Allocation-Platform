from __future__ import annotations

from typing import Any

from .combat_availability_context import evaluate_combat_availability_context
from .combat_damage_durability_context import evaluate_combat_damage_durability_context
from .combat_data_availability import evaluate_combat_data_availability
from .combat_grappling_control_impact import evaluate_combat_grappling_control_impact
from .combat_impact_calibration import evaluate_combat_impact_calibration
from .combat_impact_common import ALLOWED_COMBAT_REVIEW_STATUSES, FORBIDDEN_COMBAT_ACTIONS, FIGHTER_PROP_MARKETS, METHOD_MARKETS, ROUND_TOTAL_MARKETS, clamp, compact_list, finalize_combat_response, normalize_combat_market, normalize_combat_sport, weighted_average
from .combat_impact_readiness import build_combat_impact_readiness
from .combat_impact_red_team import evaluate_combat_impact_red_team
from .combat_incentive_context import evaluate_combat_incentive_context
from .combat_market_relevance import evaluate_combat_market_relevance
from .combat_matchup_context import evaluate_combat_matchup_context
from .combat_pace_cardio_context import evaluate_combat_pace_cardio_context
from .combat_phase_control_context import evaluate_combat_phase_control_context
from .combat_ruleset_referee_judging_context import evaluate_combat_ruleset_referee_judging_context
from .combat_striking_impact import evaluate_combat_striking_impact


def _merge(*items: dict[str, Any] | None) -> dict[str, Any]:
    row: dict[str, Any] = {}
    for item in items:
        if isinstance(item, dict):
            row.update(item)
    return row


def _missing(*sections: dict[str, Any]) -> list[str]:
    out: list[Any] = []
    for section in sections:
        if isinstance(section, dict):
            out.extend(section.get("missing_inputs") or [])
    return compact_list(out, limit=100)


def _recommend(*, tier: int, market: str, calibration_status: str, selected: float, no_bet: list[str], red_team_adjustment: str, fighter_allowed: bool) -> str:
    if tier == 0 or not fighter_allowed:
        return "DATA_INSUFFICIENT"
    if red_team_adjustment == "NO_BET" or any("hard_warning" in str(reason) for reason in no_bet):
        return "NO_BET"
    if calibration_status == "insufficient_data":
        if selected >= 55 and tier >= 2:
            return "WATCHLIST_REVIEW"
        return "CALIBRATION_ONLY"
    if tier >= 3 and calibration_status == "calibration_ready" and selected >= 70 and not no_bet:
        return "ACTIVE_REVIEW"
    if market in FIGHTER_PROP_MARKETS:
        return "FIGHTER_PROP_REVIEW_ONLY"
    if market in METHOD_MARKETS:
        return "METHOD_MARKET_REVIEW_ONLY"
    if market in ROUND_TOTAL_MARKETS:
        return "ROUND_TOTAL_REVIEW_ONLY"
    return "MARKET_REVIEW_ONLY"


def build_combat_impact_diagnostics(
    *,
    sport: str = "combat_sports",
    market_type: str = "moneyline",
    bout_context: dict[str, Any] | None = None,
    fighter_a_context: dict[str, Any] | None = None,
    fighter_b_context: dict[str, Any] | None = None,
    striking_context: dict[str, Any] | None = None,
    grappling_context: dict[str, Any] | None = None,
    phase_context: dict[str, Any] | None = None,
    damage_context: dict[str, Any] | None = None,
    pace_cardio_context: dict[str, Any] | None = None,
    matchup_context: dict[str, Any] | None = None,
    ruleset_context: dict[str, Any] | None = None,
    judging_referee_context: dict[str, Any] | None = None,
    availability_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
    calibration_context: dict[str, Any] | None = None,
    film_tracking_context: dict[str, Any] | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    normalized_sport = normalize_combat_sport(sport)
    market = normalize_combat_market(market_type)
    all_row = _merge(
        bout_context,
        fighter_a_context,
        fighter_b_context,
        striking_context,
        grappling_context,
        phase_context,
        damage_context,
        pace_cardio_context,
        matchup_context,
        ruleset_context,
        judging_referee_context,
        availability_context,
        incentive_context,
        calibration_context,
        film_tracking_context,
        {"sport": normalized_sport, "market_type": market},
    )
    source_payload = {
        "sport": sport,
        "market_type": market_type,
        "bout_context": bout_context or {},
        "fighter_a_context": fighter_a_context or {},
        "fighter_b_context": fighter_b_context or {},
        "striking_context": striking_context or {},
        "grappling_context": grappling_context or {},
        "phase_context": phase_context or {},
        "damage_context": damage_context or {},
        "pace_cardio_context": pace_cardio_context or {},
        "matchup_context": matchup_context or {},
        "ruleset_context": ruleset_context or {},
        "judging_referee_context": judging_referee_context or {},
        "availability_context": availability_context or {},
        "incentive_context": incentive_context or {},
        "calibration_context": calibration_context or {},
        "film_tracking_context": film_tracking_context or {},
        "dry_run": dry_run,
    }
    data = evaluate_combat_data_availability(
        normalized_sport,
        market_type=market,
        bout_context=bout_context,
        fighter_a_context=fighter_a_context,
        fighter_b_context=fighter_b_context,
        striking_context=striking_context,
        grappling_context=grappling_context,
        phase_context=phase_context,
        damage_context=damage_context,
        pace_cardio_context=pace_cardio_context,
        matchup_context=matchup_context,
        ruleset_context=ruleset_context,
        judging_referee_context=judging_referee_context,
        availability_context=availability_context,
        incentive_context=incentive_context,
        calibration_context=calibration_context,
        film_tracking_context=film_tracking_context,
    )
    tier = int(data.get("data_tier", 0) or 0)
    striking = evaluate_combat_striking_impact(all_row, data_tier=tier)
    grappling = evaluate_combat_grappling_control_impact(all_row, data_tier=tier)
    phase = evaluate_combat_phase_control_context(all_row)
    damage = evaluate_combat_damage_durability_context(all_row)
    pace = evaluate_combat_pace_cardio_context(all_row)
    matchup = evaluate_combat_matchup_context(all_row)
    availability = evaluate_combat_availability_context(all_row)
    rules = evaluate_combat_ruleset_referee_judging_context(all_row)
    incentive = evaluate_combat_incentive_context(all_row)
    calibration = evaluate_combat_impact_calibration(
        calibration_context or {},
        sport=normalized_sport,
        market_type=market,
        ruleset=(bout_context or {}).get("ruleset") or (ruleset_context or {}).get("ruleset"),
        weight_class=(bout_context or {}).get("weight_class"),
        scheduled_rounds=(bout_context or {}).get("scheduled_rounds") or (ruleset_context or {}).get("scheduled_rounds"),
        data_tier=tier,
    )
    market_rel = evaluate_combat_market_relevance(
        all_row,
        market_type=market,
        striking_impact=striking,
        grappling_control_impact=grappling,
        phase_control_context=phase,
        damage_durability_context=damage,
        pace_cardio_context=pace,
        matchup_context=matchup,
        availability_context=availability,
        ruleset_referee_judging_context=rules,
        incentive_context=incentive,
    )
    red_team = evaluate_combat_impact_red_team(
        market_type=market,
        data_availability=data,
        striking_impact=striking,
        grappling_control_impact=grappling,
        phase_control_context=phase,
        damage_durability_context=damage,
        pace_cardio_context=pace,
        matchup_context=matchup,
        availability_context=availability,
        ruleset_referee_judging_context=rules,
        incentive_context=incentive,
        market_relevance=market_rel,
        calibration=calibration,
        film_tracking_context=film_tracking_context or {},
        source_payload=all_row,
    )
    no_bet = compact_list(
        [
            *(striking.get("no_bet_reasons") or []),
            *(grappling.get("no_bet_reasons") or []),
            *(phase.get("no_bet_reasons") or []),
            *(damage.get("no_bet_reasons") or []),
            *(pace.get("no_bet_reasons") or []),
            *(matchup.get("no_bet_reasons") or []),
            *(availability.get("no_bet_reasons") or []),
            *(rules.get("no_bet_reasons") or []),
            *(incentive.get("no_bet_reasons") or []),
            *(market_rel.get("no_bet_market_reasons") or []),
            *(red_team.get("no_bet_reasons") or []),
        ],
        limit=60,
    )
    selected = float(market_rel.get("selected_market_relevance_score", 0.0) or 0.0)
    recommended = _recommend(
        tier=tier,
        market=market,
        calibration_status=str(calibration.get("calibration_status", "insufficient_data")),
        selected=selected,
        no_bet=no_bet,
        red_team_adjustment=str(red_team.get("recommended_action_adjustment", "NO_CHANGE")),
        fighter_allowed=bool(data.get("fighter_level_allowed", False)),
    )
    score = weighted_average(
        (
            (striking.get("striking_impact_score"), 0.18),
            (grappling.get("grappling_impact_score"), 0.18),
            (phase.get("phase_control_score"), 0.14),
            (100.0 - damage.get("durability_risk_score", 0.0), 0.12),
            (pace.get("cardio_score"), 0.1),
            (matchup.get("matchup_advantage_score"), 0.14),
            (availability.get("availability_score"), 0.12),
            (selected, 0.18),
            (100.0 - red_team.get("downgrade_score", 0.0), 0.16),
        )
    )
    markets_to_review = [] if recommended in {"DATA_INSUFFICIENT", "NO_BET", "CALIBRATION_ONLY"} else compact_list([market, *(market_rel.get("strongest_market_links") or [])], limit=12)
    payload = {
        "ok": True,
        "status": "combat_phase_control_impact_complete",
        "sport": normalized_sport,
        "market_type": market,
        "data_tier": tier,
        "tier_name": data.get("tier_name"),
        "fighter_level_allowed": bool(data.get("fighter_level_allowed", False)),
        "phase_control_allowed": bool(data.get("phase_control_allowed", False)),
        "damage_durability_allowed": bool(data.get("damage_durability_allowed", False)),
        "judging_referee_allowed": bool(data.get("judging_referee_allowed", False)),
        "data_availability": data,
        "striking_impact": striking,
        "grappling_control_impact": grappling,
        "phase_control_context": phase,
        "damage_durability_context": damage,
        "pace_cardio_context": pace,
        "matchup_context": matchup,
        "availability_context": availability,
        "ruleset_referee_judging_context": rules,
        "incentive_context": incentive,
        "market_relevance": market_rel,
        "calibration": calibration,
        "calibration_status": calibration.get("calibration_status", "insufficient_data"),
        "red_team": red_team,
        "combat_impact_score": round(clamp(score or 0.0), 2),
        "recommended_review_status": recommended,
        "markets_to_review": markets_to_review,
        "no_bet_reasons": no_bet,
        "missing_inputs": _missing(striking, grappling, phase, damage, pace, matchup, availability, rules),
        "next_data_to_collect": compact_list([*(data.get("next_data_to_collect") or []), *(calibration.get("next_required_data") or []), *(red_team.get("missing_inputs") or [])], limit=40),
        "allowed_review_statuses": list(ALLOWED_COMBAT_REVIEW_STATUSES),
        "forbidden_recommendations_rejected": list(FORBIDDEN_COMBAT_ACTIONS),
        "readiness": build_combat_impact_readiness(),
    }
    return finalize_combat_response(payload, source_payload=source_payload)

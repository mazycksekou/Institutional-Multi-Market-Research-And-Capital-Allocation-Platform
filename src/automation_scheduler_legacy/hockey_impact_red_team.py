from __future__ import annotations

from typing import Any

from .hockey_impact_common import GOALIE_PROP_MARKETS, SKATER_PROP_MARKETS, TEAM_MARKETS, clamp, compact_list, finalize_hockey_response


def evaluate_hockey_impact_red_team(
    *,
    data_availability: dict[str, Any] | None = None,
    possession_impact: dict[str, Any] | None = None,
    skater_impact: dict[str, Any] | None = None,
    goalie_impact: dict[str, Any] | None = None,
    line_pair_context: dict[str, Any] | None = None,
    special_teams_context: dict[str, Any] | None = None,
    transition_context: dict[str, Any] | None = None,
    matchup_context: dict[str, Any] | None = None,
    availability_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
    market_relevance: dict[str, Any] | None = None,
    calibration: dict[str, Any] | None = None,
    tracking_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = data_availability or {}
    possession = possession_impact or {}
    skater = skater_impact or {}
    goalie = goalie_impact or {}
    line_pair = line_pair_context or {}
    special = special_teams_context or {}
    transition = transition_context or {}
    matchup = matchup_context or {}
    available = availability_context or {}
    incentive = incentive_context or {}
    market = market_relevance or {}
    calibration = calibration or {}
    tracking = tracking_context or {}
    selected_market = str(market.get("selected_market_type") or "")
    reasons: list[str] = []
    missing: list[str] = []
    downgrade = 0.0

    if tracking and not data.get("tracking_level_allowed", False):
        reasons.append("tracking_metric_missing_but_claimed")
        downgrade += 18.0
    if transition.get("zone_entry_fabricated") or (tracking.get("claimed_zone_entries") and "zone_entry_context" in data.get("missing_field_groups", [])):
        reasons.append("zone_entry_exit_missing_but_claimed")
        downgrade += 18.0
    if goalie.get("gsax_fabricated") or (goalie.get("shot_quality_adjusted_score", 0.0) >= 60 and goalie.get("missing_goalie_inputs") and "goals_saved_above_expected_proxy" in goalie.get("missing_goalie_inputs", [])):
        reasons.append("goalie_gsax_missing_but_claimed")
        downgrade += 16.0
    if selected_market in SKATER_PROP_MARKETS and not line_pair.get("confirmed_lines", False):
        reasons.append("line_combination_unconfirmed_overconfidence")
        missing.append("confirmed_lines")
        downgrade += 14.0
    if selected_market in TEAM_MARKETS | GOALIE_PROP_MARKETS and goalie.get("starter_certainty_score", 0.0) < 55:
        reasons.append("confirmed_goalie_missing_overconfidence")
        missing.append("confirmed_goalie")
        downgrade += 18.0
    if available.get("fatigue_risk_score", 0.0) >= 70:
        reasons.append("rest_back_to_back_overfit")
        downgrade += 12.0
    if "recent_save_percentage_volatile_without_shot_quality_adjustment" in (goalie.get("no_bet_reasons") or []):
        reasons.append("recent_save_percentage_overfit")
        downgrade += 10.0
    if skater.get("shooting_percentage_regression_caution"):
        reasons.append("shooting_percentage_overfit")
        downgrade += 10.0
    if possession.get("insufficient_sample") and possession.get("xg_quality_score", 0.0) >= 60:
        reasons.append("small_sample_xg_overfit")
        downgrade += 14.0
    if special.get("special_teams_volatility_score", 0.0) >= 65 and calibration.get("calibration_status") == "insufficient_data":
        reasons.append("special_teams_volatility_overfit")
        downgrade += 12.0
    if "referee_penalty_tendency_missing_not_fabricated" in (special.get("no_bet_reasons") or []):
        reasons.append("penalty_environment_missing_overclaim")
        downgrade += 8.0
    if "line_pair_deployment_not_fabricated" in (matchup.get("no_bet_reasons") or []):
        reasons.append("matchup_deployment_overclaim")
        downgrade += 10.0
    if selected_market in SKATER_PROP_MARKETS and available.get("role_stability_score", 100.0) < 45:
        reasons.append("player_prop_role_instability")
        downgrade += 12.0
    if selected_market.startswith("first_period") and "first_period_context" in data.get("missing_field_groups", []) and possession.get("total_signal_score", 0.0) >= 55:
        reasons.append("first_period_full_game_context_confusion")
        downgrade += 12.0
    if calibration.get("calibration_status") == "insufficient_data":
        reasons.append("calibration_missing")
        missing.extend(calibration.get("next_required_data") or ["settled_outcomes"])
        downgrade += 14.0
    if possession.get("limited_proxy") and possession.get("possession_score", 0.0) >= 60:
        reasons.append("box_score_proxy_overclaim")
        downgrade += 10.0
    if incentive.get("narrative_overfit_risk") == "high":
        reasons.append("narrative_incentive_overfit")
        downgrade += 8.0

    no_bet = []
    if downgrade >= 35.0:
        no_bet.append("red_team_hard_block_overconfidence")
    if "confirmed_goalie_missing_overconfidence" in reasons:
        no_bet.append("unconfirmed_goalie_blocks_high_confidence_market_review")
    if "tracking_metric_missing_but_claimed" in reasons:
        no_bet.append("fake_tracking_claim_block")
    if "goalie_gsax_missing_but_claimed" in reasons:
        no_bet.append("fake_gsax_claim_block")

    if downgrade >= 35.0:
        adjustment = "NO_BET"
    elif downgrade >= 18.0:
        adjustment = "DATA_INSUFFICIENT"
    elif downgrade > 0.0:
        adjustment = "WATCHLIST_REVIEW"
    else:
        adjustment = "NO_CHANGE"
    return finalize_hockey_response(
        {
            "red_team_status": "downgrade" if downgrade else "pass_review_only",
            "downgrade_score": round(clamp(downgrade), 2),
            "recommended_action_adjustment": adjustment,
            "no_bet_reasons": compact_list(no_bet, limit=15),
            "red_team_reasons": compact_list(reasons or ["no_red_team_hard_block"], limit=25),
            "missing_inputs": compact_list(missing, limit=25),
            "confidence_cap_reason": "red_team_downgrade" if downgrade else None,
            "red_team_only": True,
        },
        source_payload={"data_availability": data, "tracking_context": tracking},
    )

from __future__ import annotations

from typing import Any

from src.market_intelligence.football_impact_common import clamp, compact_list, finalize_football_response, normalize_football_sport
from src.market_intelligence.football_impact_common import PLAYER_PROP_MARKETS


def evaluate_football_impact_red_team(
    *,
    sport: str = "americanfootball_nfl",
    data_availability: dict[str, Any] | None = None,
    play_drive_impact: dict[str, Any] | None = None,
    role_impact: dict[str, Any] | None = None,
    matchup_context: dict[str, Any] | None = None,
    availability_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
    market_relevance: dict[str, Any] | None = None,
    calibration: dict[str, Any] | None = None,
    tracking_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_sport = normalize_football_sport(sport)
    data = data_availability or {}
    play = play_drive_impact or {}
    role = role_impact or {}
    matchup = matchup_context or {}
    available = availability_context or {}
    incentive = incentive_context or {}
    market = market_relevance or {}
    calibration = calibration or {}
    tracking = tracking_context or {}

    reasons: list[str] = []
    missing: list[str] = []
    downgrade = 0.0

    if tracking and not data.get("tracking_level_allowed", False):
        reasons.append("tracking_metric_missing_but_claimed")
        downgrade += 18.0
    if normalized_sport == "americanfootball_ncaaf" and tracking:
        reasons.append("ncaaf_player_tracking_overclaim")
        downgrade += 18.0
    if available.get("confidence_cap_reason") in {"injury_uncertainty_caps_confidence", "player_unavailable_or_doubtful"}:
        reasons.append("injury_uncertainty_overconfidence")
        downgrade += 16.0
    if available.get("starting_qb_market_risk_score", 0.0) >= 65.0:
        reasons.append("backup_qb_market_risk")
        downgrade += 22.0
    if available.get("weather_adjustment_score", 0.0) >= 65.0 or available.get("wind_risk_score", 0.0) >= 65.0:
        reasons.append("weather_overfit")
        downgrade += 14.0
    if incentive.get("narrative_overfit_risk") == "high":
        reasons.append("narrative_incentive_overfit")
        downgrade += 12.0
    if play.get("insufficient_sample") and play.get("play_impact_score", 0.0) >= 60.0:
        reasons.append("small_sample_epa_overfit")
        downgrade += 16.0
    if play.get("garbage_time_adjusted") is False:
        reasons.append("garbage_time_distortion")
        downgrade += 8.0
    if play.get("limited_proxy_used") and play.get("play_impact_score", 0.0) >= 60.0:
        reasons.append("box_score_proxy_overclaim")
        downgrade += 12.0
    selected_market = str(market.get("selected_market_type") or "")
    is_player_market = selected_market in PLAYER_PROP_MARKETS
    if is_player_market and role.get("role_volatility_score", 0.0) >= 70.0:
        reasons.append("player_prop_role_instability")
        downgrade += 12.0
    if market.get("strongest_market_links") and market.get("weak_market_links"):
        if set(market.get("strongest_market_links") or []) & set(market.get("weak_market_links") or []):
            reasons.append("conflicting_market_links")
            downgrade += 8.0
    if calibration.get("calibration_status") == "insufficient_data":
        reasons.append("calibration_missing")
        missing.extend(calibration.get("next_required_data") or ["settled_outcomes"])
        downgrade += 14.0
    if is_player_market and not data.get("player_level_allowed", False) and market.get("player_prop_relevance", 0.0) >= 55.0:
        reasons.append("player_prop_without_player_participation_data")
        missing.extend(["snap_share", "route_share", "target_share", "carry_share"])
        downgrade += 14.0

    no_bet = []
    if downgrade >= 35.0:
        no_bet.append("red_team_hard_block_overconfidence")
    if "backup_qb_market_risk" in reasons:
        no_bet.append("backup_qb_market_risk")
    if "ncaaf_player_tracking_overclaim" in reasons:
        no_bet.append("ncaaf_tracking_not_supported_by_payload")

    if downgrade >= 35.0:
        adjustment = "NO_BET"
    elif downgrade >= 18.0:
        adjustment = "DATA_INSUFFICIENT"
    elif downgrade > 0.0:
        adjustment = "WATCHLIST_REVIEW"
    else:
        adjustment = "NO_CHANGE"

    return finalize_football_response(
        {
            "red_team_status": "downgrade" if downgrade else "pass_review_only",
            "downgrade_score": round(clamp(downgrade), 2),
            "recommended_action_adjustment": adjustment,
            "no_bet_reasons": compact_list(no_bet, limit=12),
            "red_team_reasons": compact_list(reasons or ["no_red_team_hard_block"], limit=20),
            "missing_inputs": compact_list(missing, limit=25),
            "confidence_cap_reason": "red_team_downgrade" if downgrade else None,
            "red_team_only": True,
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "auto_execution": False,
            "human_approval_required": True,
            "owner_approval_required": True,
        },
        source_payload={
            "sport": normalized_sport,
            "data_availability": data,
            "play_drive_impact": play,
            "role_impact": role,
            "tracking_context": tracking,
        },
    )

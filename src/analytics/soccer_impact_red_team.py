from __future__ import annotations

from typing import Any

from src.market_intelligence.soccer_impact_common import PLAYER_PROP_MARKETS, TEAM_MARKETS, clamp, compact_list, finalize_soccer_response


def evaluate_soccer_impact_red_team(
    *,
    data_availability: dict[str, Any] | None = None,
    possession_value_impact: dict[str, Any] | None = None,
    tactical_context: dict[str, Any] | None = None,
    pressing_transition_context: dict[str, Any] | None = None,
    player_role_impact: dict[str, Any] | None = None,
    lineup_availability_context: dict[str, Any] | None = None,
    set_piece_context: dict[str, Any] | None = None,
    goalkeeper_context: dict[str, Any] | None = None,
    referee_context: dict[str, Any] | None = None,
    matchup_context: dict[str, Any] | None = None,
    incentive_context: dict[str, Any] | None = None,
    market_relevance: dict[str, Any] | None = None,
    calibration: dict[str, Any] | None = None,
    tracking_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = data_availability or {}
    possession = possession_value_impact or {}
    tactical = tactical_context or {}
    pressing = pressing_transition_context or {}
    player = player_role_impact or {}
    lineup = lineup_availability_context or {}
    set_piece = set_piece_context or {}
    keeper = goalkeeper_context or {}
    referee = referee_context or {}
    matchup = matchup_context or {}
    incentive = incentive_context or {}
    market = market_relevance or {}
    calibration = calibration or {}
    tracking = tracking_context or {}
    selected_market = str(market.get("selected_market_type") or "")
    reasons: list[str] = []
    missing: list[str] = []
    downgrade = 0.0
    missing_groups = set(data.get("missing_field_groups") or [])
    if possession.get("xt_fabricated") or (tracking.get("claimed_xt") and "expected_threat_context" in missing_groups):
        reasons.append("xt_missing_but_claimed")
        downgrade += 18.0
    if possession.get("obv_vaep_fabricated") or (tracking.get("claimed_obv_vaep") and "obv_vaep_context" in missing_groups):
        reasons.append("obv_vaep_missing_but_claimed")
        downgrade += 18.0
    if tracking and not data.get("tracking_level_allowed", False):
        reasons.append("tracking_missing_but_claimed")
        downgrade += 18.0
    if tracking.get("claimed_pitch_control") and "tracking_context" in missing_groups:
        reasons.append("pitch_control_missing_but_claimed")
        downgrade += 18.0
    if tactical.get("formation_fabricated") or (tracking.get("claimed_formation") and "formation_context" in missing_groups):
        reasons.append("formation_missing_but_claimed")
        downgrade += 16.0
    if selected_market in PLAYER_PROP_MARKETS | TEAM_MARKETS and lineup.get("lineup_certainty_score", 100.0) < 55:
        reasons.append("confirmed_lineup_missing_overconfidence")
        missing.append("confirmed_lineup")
        downgrade += 14.0
    if selected_market in TEAM_MARKETS | {"saves", "goalkeeper_saves"} and keeper.get("starter_certainty_score", 100.0) < 55:
        reasons.append("goalkeeper_confirmation_missing_overconfidence")
        missing.append("confirmed_goalkeeper")
        downgrade += 16.0
    if referee.get("referee_tendency_fabricated") or (tracking.get("claimed_referee_tendency") and "referee_context" in missing_groups):
        reasons.append("referee_tendency_missing_but_claimed")
        downgrade += 14.0
    if set_piece.get("penalty_taker_fabricated") or (tracking.get("claimed_penalty_taker") and "penalty_taker_status" in str(set_piece.get("missing_inputs") or [])):
        reasons.append("penalty_taker_missing_but_claimed")
        downgrade += 12.0
    if set_piece.get("set_piece_role_fabricated") or (tracking.get("claimed_set_piece_role") and "set_piece_taker_status" in str(set_piece.get("missing_inputs") or [])):
        reasons.append("set_piece_role_missing_but_claimed")
        downgrade += 12.0
    if keeper.get("post_shot_xg_fabricated") or (keeper.get("shot_stopping_score", 0.0) >= 60 and "post_shot_xg_allowed" in (keeper.get("missing_goalkeeper_inputs") or [])):
        reasons.append("post_shot_xg_missing_but_claimed")
        downgrade += 14.0
    if possession.get("insufficient_sample") and possession.get("xg_quality_score", 0.0) >= 60:
        reasons.append("small_sample_xg_overfit")
        downgrade += 14.0
    if tracking.get("recent_form_claimed"):
        reasons.append("recent_form_overfit")
        downgrade += 8.0
    if possession.get("limited_proxy") and possession.get("territorial_dominance_score", 0.0) >= 60:
        reasons.append("possession_percentage_overfit")
        downgrade += 10.0
    if incentive.get("narrative_overfit_risk") == "high" or "weak_narrative_context" in (incentive.get("no_bet_reasons") or []):
        reasons.append("tactical_narrative_overfit")
        downgrade += 8.0
    if tracking.get("derby_narrative_claimed"):
        reasons.append("derby_narrative_overfit")
        downgrade += 8.0
    if referee.get("red_card_volatility_risk", 0.0) >= 65 and selected_market == "correct_score":
        reasons.append("red_card_volatility_ignored")
        downgrade += 12.0
    if selected_market == "correct_score" and calibration.get("calibration_status") != "calibration_ready":
        reasons.append("correct_score_overconfidence")
        downgrade += 18.0
    if selected_market.startswith("first_half") and "first_half_context" in missing_groups and possession.get("total_signal_score", 0.0) >= 55:
        reasons.append("first_half_full_game_context_confusion")
        downgrade += 12.0
    if calibration.get("calibration_status") == "insufficient_data":
        reasons.append("calibration_missing")
        missing.extend(calibration.get("next_required_data") or ["settled_outcomes"])
        downgrade += 14.0
    no_bet = []
    if downgrade >= 35:
        no_bet.append("red_team_hard_block_overconfidence")
    if "xt_missing_but_claimed" in reasons:
        no_bet.append("fake_xt_claim_block")
    if "obv_vaep_missing_but_claimed" in reasons:
        no_bet.append("fake_obv_vaep_claim_block")
    if "goalkeeper_confirmation_missing_overconfidence" in reasons:
        no_bet.append("unconfirmed_goalkeeper_blocks_high_confidence_market_review")
    adjustment = "NO_BET" if downgrade >= 35 else "DATA_INSUFFICIENT" if downgrade >= 18 else "WATCHLIST_REVIEW" if downgrade > 0 else "NO_CHANGE"
    return finalize_soccer_response(
        {
            "red_team_status": "downgrade" if downgrade else "pass_review_only",
            "downgrade_score": round(clamp(downgrade), 2),
            "recommended_action_adjustment": adjustment,
            "no_bet_reasons": compact_list(no_bet, limit=15),
            "red_team_reasons": compact_list(reasons or ["no_red_team_hard_block"], limit=30),
            "missing_inputs": compact_list(missing, limit=30),
            "confidence_cap_reason": "red_team_downgrade" if downgrade else None,
            "red_team_only": True,
        },
        source_payload={"data_availability": data, "tracking_context": tracking},
    )

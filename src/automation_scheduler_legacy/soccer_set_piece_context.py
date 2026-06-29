from __future__ import annotations

from typing import Any

from .soccer_impact_common import clamp, compact_list, finalize_soccer_response, missing_fields, score_from_range, weighted_average


SET_PIECE_FIELDS = ("set_piece_xg_for", "set_piece_xg_against", "corner_rate_for", "penalty_rate_for", "set_piece_taker_status", "penalty_taker_status")


def evaluate_soccer_set_piece_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    attack = weighted_average(((score_from_range(source.get("set_piece_xg_for"), low=0, high=0.9), 0.6), (score_from_range(source.get("corner_rate_for"), low=1, high=9), 0.25), (score_from_range(source.get("free_kick_shot_rate"), low=0, high=3), 0.25), (score_from_range(source.get("aerial_duel_strength"), low=0, high=1), 0.25)))
    defense = weighted_average(((score_from_range(source.get("set_piece_xg_against"), low=0, high=0.9, inverse=True), 0.55), (score_from_range(source.get("corner_rate_against"), low=1, high=9, inverse=True), 0.25), (score_from_range(source.get("opponent_set_piece_defense"), low=0, high=1, inverse=True), 0.25), (score_from_range(source.get("keeper_cross_claim_rate"), low=0, high=1), 0.2)))
    penalty_context = weighted_average(((score_from_range(source.get("penalty_rate_for"), low=0, high=0.5), 0.35), (score_from_range(source.get("referee_penalty_rate"), low=0, high=0.5), 0.35), (90.0 if source.get("penalty_taker_status") not in (None, "", "unknown") else 0.0, 0.35)))
    corner_context = weighted_average(((score_from_range(source.get("corner_rate_for"), low=1, high=9), 0.45), (score_from_range(source.get("corner_rate_against"), low=1, high=9), 0.2), (attack, 0.35)))
    aerial = weighted_average(((score_from_range(source.get("team_height_proxy"), low=0, high=1), 0.3), (score_from_range(source.get("aerial_duel_strength"), low=0, high=1), 0.45), (score_from_range(source.get("opponent_set_piece_defense"), low=0, high=1, inverse=True), 0.3)))
    player_goal_mod = weighted_average(((attack, 0.35), (penalty_context, 0.35), (aerial, 0.25), (90.0 if source.get("set_piece_taker_status") not in (None, "", "unknown") else 0.0, 0.2))) or 0.0
    total_mod = weighted_average(((attack, 0.3), (100.0 - (defense or 0.0), 0.25), (penalty_context, 0.25), (corner_context, 0.15))) or 0.0
    no_bet = []
    if source.get("penalty_taker_status") in (None, "", "unknown"):
        no_bet.append("penalty_taker_missing_not_fabricated")
    if source.get("set_piece_taker_status") in (None, "", "unknown"):
        no_bet.append("set_piece_role_missing_not_fabricated")
    if source.get("referee_penalty_rate") in (None, ""):
        no_bet.append("referee_penalty_tendency_missing_not_fabricated")
    return finalize_soccer_response(
        {
            "set_piece_attack_score": round(clamp(attack or 0.0), 2),
            "set_piece_defense_score": round(clamp(defense or 0.0), 2),
            "penalty_context_score": round(clamp(penalty_context or 0.0), 2),
            "corner_context_score": round(clamp(corner_context or 0.0), 2),
            "aerial_mismatch_score": round(clamp(aerial or 0.0), 2),
            "player_goal_prop_modifier": round(clamp(player_goal_mod), 2),
            "total_market_modifier": round(clamp(total_mod), 2),
            "team_total_modifier": round(clamp(weighted_average(((attack, 0.45), (penalty_context, 0.25), (aerial, 0.2))) or 0.0), 2),
            "set_piece_xg_separated": source.get("set_piece_xg_for") not in (None, ""),
            "penalty_taker_fabricated": False,
            "set_piece_role_fabricated": False,
            "referee_penalty_tendency_fabricated": False,
            "missing_inputs": compact_list(missing_fields(source, SET_PIECE_FIELDS), limit=20),
            "no_bet_reasons": compact_list(no_bet, limit=20),
        },
        source_payload=source,
    )

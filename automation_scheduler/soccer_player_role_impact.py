from __future__ import annotations

from typing import Any

from .soccer_impact_common import clamp, compact_list, finalize_soccer_response, missing_fields, normalize_soccer_role, score_centered, score_from_range, weighted_average


PLAYER_FIELDS = ("role", "minutes_projection", "shots", "non_penalty_xg", "progressive_passes", "tackles")


def evaluate_soccer_player_role_impact(row: dict[str, Any] | None = None, *, player_level_allowed: bool = False, data_tier: int = 0) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    if not source:
        return finalize_soccer_response(
            {
                "player_level_allowed": False,
                "role": "UNKNOWN",
                "player_impact_score": 0.0,
                "player_market_relevance": 0.0,
                "missing_player_inputs": list(PLAYER_FIELDS),
                "no_bet_reasons": ["missing_player_context"],
                "penalty_taker_fabricated": False,
                "set_piece_role_fabricated": False,
                "post_shot_xg_fabricated": False,
            }
        )
    role = normalize_soccer_role(source.get("role") or source.get("player_role") or source.get("position"))
    goalkeeper = role == "GOALKEEPER"
    attacking = weighted_average(
        (
            (score_from_range(source.get("non_penalty_xg"), low=0, high=0.8), 0.55),
            (score_from_range(source.get("shots"), low=0, high=5), 0.4),
            (score_from_range(source.get("shots_on_target"), low=0, high=2.5), 0.4),
            (score_from_range(source.get("touches_in_box"), low=0, high=10), 0.35),
            (score_from_range(source.get("carries_into_box"), low=0, high=6), 0.25),
            (score_from_range(source.get("big_chance_involvement"), low=0, high=3), 0.25),
        )
    )
    creative = weighted_average(
        (
            (score_from_range(source.get("expected_assists"), low=0, high=0.6), 0.45),
            (score_from_range(source.get("key_passes"), low=0, high=5), 0.4),
            (score_from_range(source.get("through_balls"), low=0, high=4), 0.25),
            (score_from_range(source.get("xT_created"), low=0, high=1.2), 0.45),
            (score_from_range(source.get("progressive_passes"), low=0, high=14), 0.35),
            (score_from_range(source.get("passes_into_penalty_area"), low=0, high=8), 0.35),
        )
    )
    defensive = weighted_average(
        (
            (score_from_range(source.get("tackles"), low=0, high=6), 0.35),
            (score_from_range(source.get("interceptions"), low=0, high=5), 0.35),
            (score_from_range(source.get("clearances"), low=0, high=8), 0.25),
            (score_from_range(source.get("aerial_duel_rate"), low=0, high=1), 0.25),
        )
    )
    pressing = weighted_average(((score_from_range(source.get("pressures"), low=0, high=45), 0.55), (score_from_range(source.get("counterpress_regains"), low=0, high=8), 0.45)))
    set_piece = weighted_average(((75.0 if source.get("set_piece_role") or source.get("set_piece_taker_status") not in (None, "", "unknown") else 0.0, 0.35), (90.0 if source.get("penalty_taker_status") not in (None, "", "unknown") else 0.0, 0.35), (score_from_range(source.get("set_piece_aerial_threat"), low=0, high=1), 0.3)))
    card_risk = weighted_average(((score_from_range(source.get("card_risk"), low=0, high=1), 0.5), (score_from_range(source.get("tactical_foul_rate"), low=0, high=1), 0.35), (score_from_range(source.get("player_card_risk"), low=0, high=1), 0.5)))
    minutes_stability = weighted_average(((score_from_range(source.get("minutes_projection"), low=0, high=90), 0.55), (score_from_range(source.get("substitution_risk"), low=0, high=1, inverse=True), 0.45), (score_from_range(source.get("role_security"), low=0, high=1), 0.35))) or 0.0
    shot_stopping = weighted_average(((score_centered(source.get("save_percentage"), center=0.70, span=0.18), 0.25), (score_centered(source.get("goals_prevented_proxy"), center=0, span=10), 0.55), (score_from_range(source.get("post_shot_xg_allowed"), low=0.2, high=2.5, inverse=True), 0.45)))
    distribution = weighted_average(((score_from_range(source.get("pass_completion_under_pressure"), low=0.3, high=0.95), 0.45), (score_from_range(source.get("long_distribution_accuracy"), low=0.1, high=0.75), 0.35), (score_from_range(source.get("sweeping_actions"), low=0, high=4), 0.2)))
    if goalkeeper:
        impact = weighted_average(((shot_stopping, 0.55), (distribution, 0.25), (minutes_stability, 0.2))) or 0.0
    else:
        role_weight_attack = 0.55 if role in {"WINGER", "FORWARD", "STRIKER"} else 0.25
        role_weight_creative = 0.55 if role in {"CENTRAL_MIDFIELDER", "ATTACKING_MIDFIELDER", "WINGER"} else 0.2
        role_weight_defense = 0.55 if role in {"CENTER_BACK", "FULLBACK", "WINGBACK", "DEFENSIVE_MIDFIELDER"} else 0.2
        impact = weighted_average(((attacking, role_weight_attack), (creative, role_weight_creative), (defensive, role_weight_defense), (pressing, 0.15), (minutes_stability, 0.25))) or 0.0
    no_bet = []
    if role == "UNKNOWN":
        no_bet.append("player_role_missing_not_inferred_from_name")
    if not player_level_allowed:
        no_bet.append("player_level_data_not_allowed_by_tier")
    if source.get("penalty_taker_status") in (None, "", "unknown"):
        no_bet.append("penalty_taker_missing_not_fabricated")
    if source.get("set_piece_taker_status") in (None, "", "unknown") and source.get("set_piece_role") in (None, "", "unknown"):
        no_bet.append("set_piece_role_missing_not_fabricated")
    if source.get("post_shot_xg_allowed") in (None, "") and goalkeeper:
        no_bet.append("post_shot_xg_missing_not_inferred_from_save_percentage")
    if minutes_stability < 55 and not goalkeeper:
        no_bet.append("minutes_or_substitution_risk_caps_player_props")
    return finalize_soccer_response(
        {
            "player_level_allowed": bool(player_level_allowed),
            "role": role,
            "player_impact_score": round(clamp(impact), 2),
            "attacking_threat_score": round(clamp(attacking or 0.0), 2),
            "creative_value_score": round(clamp(creative or 0.0), 2),
            "defensive_work_score": round(clamp(defensive or 0.0), 2),
            "pressing_value_score": round(clamp(pressing or 0.0), 2),
            "set_piece_role_score": round(clamp(set_piece or 0.0), 2),
            "card_risk_score": round(clamp(card_risk or 0.0), 2),
            "minutes_role_stability_score": round(clamp(minutes_stability), 2),
            "goalkeeper_shot_stopping_score": round(clamp(shot_stopping or 0.0), 2),
            "player_market_relevance": round(clamp(weighted_average(((impact, 0.55), (minutes_stability, 0.35), (set_piece, 0.1))) or 0.0), 2),
            "missing_player_inputs": compact_list(missing_fields(source, PLAYER_FIELDS), limit=25),
            "no_bet_reasons": compact_list(no_bet, limit=25),
            "penalty_taker_fabricated": False,
            "set_piece_role_fabricated": False,
            "post_shot_xg_fabricated": False,
        },
        source_payload=source,
    )

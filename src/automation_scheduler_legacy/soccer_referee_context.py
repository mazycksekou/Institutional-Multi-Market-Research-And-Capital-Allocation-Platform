from __future__ import annotations

from typing import Any

from .soccer_impact_common import clamp, compact_list, finalize_soccer_response, missing_fields, score_from_range, weighted_average


REFEREE_FIELDS = ("card_rate", "yellow_card_rate", "foul_rate", "penalty_rate", "red_card_rate")


def evaluate_soccer_referee_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    card = weighted_average(((score_from_range(source.get("card_rate"), low=1, high=8), 0.45), (score_from_range(source.get("yellow_card_rate"), low=1, high=7), 0.4), (score_from_range(source.get("team_card_rate"), low=0, high=5), 0.25), (score_from_range(source.get("player_card_risk"), low=0, high=1), 0.3)))
    penalty = weighted_average(((score_from_range(source.get("penalty_rate"), low=0, high=0.5), 0.55), (score_from_range(source.get("referee_penalty_rate"), low=0, high=0.5), 0.45), (score_from_range(source.get("team_foul_rate"), low=5, high=20), 0.15)))
    foul = weighted_average(((score_from_range(source.get("foul_rate"), low=10, high=35), 0.5), (score_from_range(source.get("team_foul_rate"), low=5, high=22), 0.35), (score_from_range(source.get("tactical_foul_rate"), low=0, high=1), 0.35)))
    red_vol = weighted_average(((score_from_range(source.get("red_card_rate"), low=0, high=0.5), 0.55), (card, 0.2), (score_from_range(source.get("derby_rivalry_intensity"), low=0, high=1), 0.25)))
    game_flow = weighted_average(((score_from_range(source.get("advantage_play_rate"), low=0, high=1), 0.35), (score_from_range(source.get("stoppage_time_proxy"), low=0, high=12), 0.25), (100.0 - (foul or 0.0), 0.35))) or 0.0
    total_modifier = weighted_average(((penalty, 0.3), (red_vol, 0.2), (game_flow, 0.2), (foul, 0.15))) or 0.0
    no_bet = []
    if source.get("referee_name") and not any(source.get(k) not in (None, "") for k in REFEREE_FIELDS):
        no_bet.append("referee_tendency_not_inferred_from_name")
    if missing_fields(source, REFEREE_FIELDS):
        no_bet.append("referee_context_missing_or_partial_modifier_only")
    if red_vol and red_vol >= 65:
        no_bet.append("red_card_volatility_reduces_scoreline_confidence")
    return finalize_soccer_response(
        {
            "referee_environment_score": round(clamp(weighted_average(((card, 0.3), (penalty, 0.3), (foul, 0.2), (game_flow, 0.2))) or 0.0), 2),
            "card_market_relevance": round(clamp(card or 0.0), 2),
            "penalty_market_relevance": round(clamp(penalty or 0.0), 2),
            "foul_market_relevance": round(clamp(foul or 0.0), 2),
            "game_flow_modifier": round(clamp(game_flow), 2),
            "total_market_modifier": round(clamp(total_modifier), 2),
            "red_card_volatility_risk": round(clamp(red_vol or 0.0), 2),
            "referee_context_standalone_edge": False,
            "referee_tendency_fabricated": False,
            "missing_inputs": compact_list(missing_fields(source, REFEREE_FIELDS), limit=20),
            "no_bet_reasons": compact_list(no_bet, limit=20),
        },
        source_payload=source,
    )

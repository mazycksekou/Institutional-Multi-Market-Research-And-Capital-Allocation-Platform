from __future__ import annotations

from typing import Any

from .soccer_impact_common import boolish, clamp, compact_list, finalize_soccer_response, missing_fields, score_centered, score_from_range, weighted_average


GOALKEEPER_FIELDS = ("confirmed_starter", "save_percentage", "post_shot_xg_allowed", "goals_prevented_proxy", "opponent_xg", "opponent_shot_volume")


def evaluate_soccer_goalkeeper_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    if not source:
        return finalize_soccer_response(
            {
                "goalkeeper_impact_score": 0.0,
                "starter_certainty_score": 0.0,
                "goalkeeper_prop_relevance": 0.0,
                "missing_goalkeeper_inputs": list(GOALKEEPER_FIELDS),
                "no_bet_reasons": ["missing_goalkeeper_context_caps_team_total_goalkeeper_markets"],
                "post_shot_xg_fabricated": False,
            }
        )
    confirmed = boolish(source.get("confirmed_starter") if "confirmed_starter" in source else source.get("starting_goalkeeper_confirmed"))
    projected = boolish(source.get("projected_starter"))
    certainty = 95.0 if confirmed else 62.0 if projected else 28.0
    shot_stopping = weighted_average(((score_centered(source.get("save_percentage"), center=0.70, span=0.18), 0.2), (score_centered(source.get("goals_prevented_proxy"), center=0, span=10), 0.55), (score_from_range(source.get("post_shot_xg_allowed"), low=0.2, high=2.5, inverse=True), 0.55), (score_from_range(source.get("errors_leading_to_shots"), low=0, high=4, inverse=True), 0.25)))
    cross_claim = weighted_average(((score_from_range(source.get("high_claim_rate"), low=0, high=1), 0.45), (score_from_range(source.get("cross_claim_rate"), low=0, high=1), 0.55), (score_from_range(source.get("opponent_cross_rate"), low=0, high=1, inverse=True), 0.15)))
    sweeping = weighted_average(((score_from_range(source.get("sweep_actions"), low=0, high=5), 0.45), (score_from_range(source.get("defensive_line_height_context"), low=0, high=1), 0.25)))
    distribution = weighted_average(((score_from_range(source.get("distribution_accuracy"), low=0.35, high=0.95), 0.45), (score_from_range(source.get("long_pass_accuracy"), low=0.1, high=0.75), 0.35)))
    impact = weighted_average(((certainty, 0.25), (shot_stopping, 0.45), (cross_claim, 0.12), (sweeping, 0.08), (distribution, 0.1))) or 0.0
    prop_relevance = weighted_average(((certainty, 0.45), (score_from_range(source.get("opponent_shot_volume"), low=5, high=20), 0.45), (score_from_range(source.get("opponent_xg"), low=0.4, high=2.8), 0.35))) or 0.0
    team_modifier = weighted_average(((certainty, 0.45), (shot_stopping, 0.55), (cross_claim, 0.15))) or 0.0
    total_modifier = weighted_average(((100.0 - (shot_stopping or 0.0), 0.35), (score_from_range(source.get("opponent_xg"), low=0.4, high=2.8), 0.35), (score_from_range(source.get("errors_leading_to_shots"), low=0, high=4), 0.2))) or 0.0
    no_bet = []
    if not confirmed:
        no_bet.append("goalkeeper_starter_unconfirmed_caps_team_total_goalkeeper_markets")
    if source.get("post_shot_xg_allowed") in (None, ""):
        no_bet.append("post_shot_xg_missing_not_inferred_from_save_percentage")
    if source.get("save_percentage") not in (None, "") and source.get("post_shot_xg_allowed") in (None, ""):
        no_bet.append("save_percentage_volatile_without_post_shot_xg")
    if source.get("errors_leading_to_shots"):
        no_bet.append("goalkeeper_errors_increase_scoreline_volatility")
    return finalize_soccer_response(
        {
            "goalkeeper_impact_score": round(clamp(impact), 2),
            "starter_certainty_score": round(clamp(certainty), 2),
            "shot_stopping_score": round(clamp(shot_stopping or 0.0), 2),
            "cross_claim_score": round(clamp(cross_claim or 0.0), 2),
            "sweeping_score": round(clamp(sweeping or 0.0), 2),
            "distribution_score": round(clamp(distribution or 0.0), 2),
            "goalkeeper_prop_relevance": round(clamp(prop_relevance), 2),
            "team_market_goalkeeper_modifier": round(clamp(team_modifier), 2),
            "total_market_goalkeeper_modifier": round(clamp(total_modifier), 2),
            "confirmed_starter": confirmed,
            "post_shot_xg_fabricated": False,
            "missing_goalkeeper_inputs": compact_list(missing_fields(source, GOALKEEPER_FIELDS), limit=20),
            "no_bet_reasons": compact_list(no_bet, limit=20),
        },
        source_payload=source,
    )

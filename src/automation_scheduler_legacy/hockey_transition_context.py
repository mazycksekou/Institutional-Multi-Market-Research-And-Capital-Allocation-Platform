from __future__ import annotations

from typing import Any

from .hockey_impact_common import clamp, compact_list, finalize_hockey_response, missing_fields, score_from_range, weighted_average


TRANSITION_FIELDS = (
    "controlled_entry_rate",
    "controlled_exit_rate",
    "rush_chances_for",
    "forecheck_pressure_rate",
    "puck_retrieval_rate",
)


def evaluate_hockey_transition_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    controlled_entry = weighted_average(
        (
            (score_from_range(source.get("controlled_entry_rate"), low=0.15, high=0.70), 0.5),
            (score_from_range(source.get("controlled_entry_success_rate"), low=0.25, high=0.85), 0.45),
            (score_from_range(source.get("dump_in_retrieval_rate"), low=0.20, high=0.70), 0.2),
        )
    )
    zone_exit = weighted_average(
        (
            (score_from_range(source.get("controlled_exit_rate"), low=0.20, high=0.75), 0.55),
            (score_from_range(source.get("failed_exit_rate"), low=0.05, high=0.35, inverse=True), 0.45),
            (score_from_range(source.get("defensive_zone_turnover_rate"), low=0.02, high=0.22, inverse=True), 0.35),
        )
    )
    rush_attack = weighted_average(
        (
            (score_from_range(source.get("rush_chances_for"), low=1, high=10), 0.45),
            (score_from_range(source.get("odd_man_rushes_for"), low=0, high=5), 0.45),
            (score_from_range(source.get("offensive_zone_possession_time_proxy"), low=0, high=1), 0.2),
        )
    )
    rush_defense_risk = weighted_average(
        (
            (score_from_range(source.get("rush_chances_against"), low=1, high=10), 0.45),
            (score_from_range(source.get("odd_man_rushes_against"), low=0, high=5), 0.45),
            (score_from_range(source.get("neutral_zone_turnover_rate"), low=0.02, high=0.25), 0.35),
        )
    )
    forecheck = weighted_average(
        (
            (score_from_range(source.get("forecheck_pressure_rate"), low=0.10, high=0.75), 0.55),
            (score_from_range(source.get("puck_retrieval_rate"), low=0.20, high=0.75), 0.45),
            (score_from_range(source.get("dump_in_retrieval_rate"), low=0.20, high=0.70), 0.25),
        )
    )
    transition_score = weighted_average(((controlled_entry, 0.32), (zone_exit, 0.28), (rush_attack, 0.2), (forecheck, 0.2))) or 0.0
    turnover_risk = weighted_average(((rush_defense_risk, 0.4), (score_from_range(source.get("failed_exit_rate"), low=0.05, high=0.35), 0.45), (score_from_range(source.get("neutral_zone_turnover_rate"), low=0.02, high=0.25), 0.35))) or 0.0
    market_modifier = weighted_average(((transition_score, 0.45), (rush_attack, 0.3), (100.0 - turnover_risk, 0.25))) or 0.0
    missing = missing_fields(source, TRANSITION_FIELDS)
    no_bet = []
    if missing:
        no_bet.append("transition_tracking_optional_missing_caps_advanced_confidence")
    if source.get("controlled_entry_rate") in (None, ""):
        no_bet.append("zone_entries_not_inferred_from_shots")
    if source.get("controlled_exit_rate") in (None, ""):
        no_bet.append("zone_exits_not_inferred_from_shots")

    return finalize_hockey_response(
        {
            "transition_score": round(clamp(transition_score), 2),
            "controlled_entry_score": round(clamp(controlled_entry or 0.0), 2),
            "zone_exit_score": round(clamp(zone_exit or 0.0), 2),
            "rush_attack_score": round(clamp(rush_attack or 0.0), 2),
            "rush_defense_risk": round(clamp(rush_defense_risk or 0.0), 2),
            "forecheck_score": round(clamp(forecheck or 0.0), 2),
            "turnover_risk_score": round(clamp(turnover_risk), 2),
            "market_relevance_modifier": round(clamp(market_modifier), 2),
            "transition_data_optional": True,
            "zone_entry_fabricated": False,
            "zone_exit_fabricated": False,
            "missing_inputs": compact_list(missing, limit=20),
            "no_bet_reasons": compact_list(no_bet, limit=20),
        },
        source_payload=source,
    )

from __future__ import annotations

from typing import Any

from .baseball_impact_common import boolish, clamp, compact_list, finalize_baseball_response, missing_fields, safe_float, score_from_range, weighted_average


LINEUP_INPUTS = (
    "confirmed_lineup",
    "projected_lineup",
    "lineup_slot",
    "leadoff_status",
    "heart_of_order_status",
    "protection_context",
    "lineup_handedness_balance",
    "team_k_rate",
    "team_bb_rate",
    "team_iso",
    "team_woba",
    "team_xwoba",
    "bench_quality_proxy",
    "pinch_hit_risk",
    "platoon_substitution_risk",
    "catcher_rest_day",
    "star_player_rest",
    "travel_day_lineup_risk",
)


def evaluate_baseball_lineup_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    confirmed = boolish(source.get("confirmed_lineup"))
    lineup_quality = weighted_average(
        (
            (score_from_range(source.get("team_woba"), low=0.285, high=0.360), 0.8),
            (score_from_range(source.get("team_xwoba"), low=0.285, high=0.365), 0.8),
            (score_from_range(source.get("team_iso"), low=0.120, high=0.230), 0.5),
            (score_from_range(source.get("team_bb_rate"), low=0.06, high=0.11), 0.3),
            (score_from_range(source.get("team_k_rate"), low=0.17, high=0.29, inverse=True), 0.35),
            (score_from_range(source.get("lineup_handedness_balance"), low=0.0, high=100.0), 0.25),
            (score_from_range(source.get("bench_quality_proxy"), low=0.0, high=100.0), 0.2),
        )
    )
    slot = safe_float(source.get("lineup_slot"))
    pa_conf = None
    if slot is not None:
        pa_conf = clamp(100.0 - max(0.0, slot - 1.0) * 8.5)
    pa_conf = weighted_average(((pa_conf, 0.75), (95.0 if confirmed else 42.0, 0.55), (100.0 - (score_from_range(source.get("pinch_hit_risk"), low=0.0, high=100.0) or 0.0), 0.25)))
    stability = weighted_average(
        (
            (95.0 if confirmed else 45.0 if source.get("projected_lineup") else 20.0, 0.75),
            (100.0 - (score_from_range(source.get("platoon_substitution_risk"), low=0.0, high=100.0) or 0.0), 0.45),
            (100.0 - (score_from_range(source.get("star_player_rest"), low=0.0, high=100.0) or 0.0), 0.45),
            (100.0 - (score_from_range(source.get("travel_day_lineup_risk"), low=0.0, high=100.0) or 0.0), 0.3),
        )
    )
    run_env = weighted_average(((lineup_quality, 0.75), (score_from_range(source.get("heart_of_order_status"), low=0.0, high=100.0), 0.25), (score_from_range(source.get("protection_context"), low=0.0, high=100.0), 0.2)))
    prop_volume = weighted_average(((pa_conf, 0.8), (stability, 0.45), (score_from_range(source.get("leadoff_status"), low=0.0, high=100.0), 0.25)))
    no_bet = []
    if not confirmed:
        no_bet.append("lineup_unconfirmed_caps_batter_prop_confidence")
        no_bet.append("unconfirmed_lineup_caps_batter_prop_confidence")
    if source.get("star_player_rest") not in (None, "") and score_from_range(source.get("star_player_rest"), low=0.0, high=100.0):
        if (score_from_range(source.get("star_player_rest"), low=0.0, high=100.0) or 0.0) >= 65:
            no_bet.append("star_player_rest_caps_team_and_prop_confidence")
    return finalize_baseball_response(
        {
            "lineup_quality_score": round(clamp(lineup_quality or 0.0), 2),
            "lineup_stability_score": round(clamp(stability or 0.0), 2),
            "plate_appearance_projection_confidence": round(clamp(pa_conf or 0.0), 2),
            "run_environment_modifier": round(clamp(run_env or 0.0), 2),
            "prop_volume_modifier": round(clamp(prop_volume or 0.0), 2),
            "confirmed_lineup": confirmed,
            "missing_inputs": compact_list(missing_fields(source, LINEUP_INPUTS), limit=25),
            "no_bet_reasons": compact_list(no_bet, limit=10),
        },
        source_payload=source,
    )

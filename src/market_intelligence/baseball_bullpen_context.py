from __future__ import annotations

from typing import Any

from .baseball_impact_common import boolish, clamp, compact_list, finalize_baseball_response, missing_fields, score_from_range, weighted_average


BULLPEN_INPUTS = (
    "bullpen_era_proxy",
    "bullpen_fip_proxy",
    "bullpen_xfip_proxy",
    "bullpen_xwoba_allowed",
    "bullpen_k_rate",
    "bullpen_bb_rate",
    "bullpen_hr_rate",
    "bullpen_recent_innings",
    "bullpen_recent_pitch_count",
    "back_to_back_relievers",
    "unavailable_relievers",
    "closer_available",
    "setup_available",
    "lefty_righty_balance",
    "high_leverage_usage",
    "inherited_runner_performance_proxy",
)


def _unavailable_count(value: Any) -> float:
    if isinstance(value, list):
        return float(len(value))
    if value in (None, "", False):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 1.0


def evaluate_baseball_bullpen_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    quality = weighted_average(
        (
            (score_from_range(source.get("bullpen_era_proxy"), low=3.0, high=5.4, inverse=True), 0.45),
            (score_from_range(source.get("bullpen_fip_proxy"), low=3.1, high=5.2, inverse=True), 0.55),
            (score_from_range(source.get("bullpen_xfip_proxy"), low=3.2, high=5.2, inverse=True), 0.45),
            (score_from_range(source.get("bullpen_xwoba_allowed"), low=0.285, high=0.370, inverse=True), 0.55),
            (score_from_range(source.get("bullpen_k_rate"), low=0.18, high=0.32), 0.3),
            (score_from_range(source.get("bullpen_bb_rate"), low=0.06, high=0.13, inverse=True), 0.3),
            (score_from_range(source.get("bullpen_hr_rate"), low=0.015, high=0.055, inverse=True), 0.3),
        )
    )
    unavailable = _unavailable_count(source.get("unavailable_relievers"))
    fatigue = weighted_average(
        (
            (score_from_range(source.get("bullpen_recent_innings"), low=2.0, high=9.0), 0.45),
            (score_from_range(source.get("bullpen_recent_pitch_count"), low=35.0, high=170.0), 0.55),
            (score_from_range(source.get("back_to_back_relievers"), low=0.0, high=4.0), 0.45),
            (score_from_range(unavailable, low=0.0, high=4.0), 0.55),
            (score_from_range(source.get("high_leverage_usage"), low=0.0, high=100.0), 0.25),
        )
    ) or 0.0
    high_lev = weighted_average(((100.0 if boolish(source.get("closer_available")) else 35.0 if source.get("closer_available") not in (None, "") else None, 0.55), (100.0 if boolish(source.get("setup_available")) else 40.0 if source.get("setup_available") not in (None, "") else None, 0.45), (100.0 - fatigue, 0.45), (score_from_range(source.get("lefty_righty_balance"), low=0.0, high=100.0), 0.25)))
    full_game = weighted_average(((quality, 0.65), (100.0 - fatigue, 0.55), (high_lev, 0.55)))
    split = round(clamp((full_game or 50.0) - 50.0), 2)
    total_risk = weighted_average(((100.0 - (quality or 50.0), 0.55), (fatigue, 0.65), (100.0 - (high_lev or 50.0), 0.35), (score_from_range(source.get("inherited_runner_performance_proxy"), low=0.0, high=100.0, inverse=True), 0.2)))
    no_bet = []
    if source.get("closer_available") in (None, "") or source.get("setup_available") in (None, ""):
        no_bet.append("bullpen_availability_missing_caps_full_game_confidence")
    if fatigue >= 70:
        no_bet.append("bullpen_fatigue_full_game_total_risk")
    return finalize_baseball_response(
        {
            "bullpen_quality_score": round(clamp(quality or 0.0), 2),
            "bullpen_fatigue_score": round(clamp(fatigue), 2),
            "high_leverage_availability_score": round(clamp(high_lev or 0.0), 2),
            "full_game_market_modifier": round(clamp(full_game or 0.0), 2),
            "first_five_vs_full_game_split": split,
            "full_game_market_modifier_context": "full_game_more_sensitive_than_first_five",
            "total_risk_modifier": round(clamp(total_risk or 0.0), 2),
            "missing_inputs": compact_list(missing_fields(source, BULLPEN_INPUTS), limit=25),
            "no_bet_reasons": compact_list(no_bet, limit=10),
        },
        source_payload=source,
    )

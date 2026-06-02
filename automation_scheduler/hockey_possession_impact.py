from __future__ import annotations

from typing import Any

from .hockey_impact_common import (
    clamp,
    compact_list,
    finalize_hockey_response,
    missing_fields,
    score_centered,
    score_from_range,
    weighted_average,
)


CORE_FIELDS = (
    "shots_for_per_game",
    "shots_against_per_game",
    "shot_attempts_for_per_game",
    "shot_attempts_against_per_game",
    "expected_goals_for_per_game",
    "expected_goals_against_per_game",
    "xg_share",
)


def evaluate_hockey_possession_impact(row: dict[str, Any] | None = None, *, data_tier: int = 0, market_type: str = "moneyline") -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    sample_size = source.get("sample_size") or source.get("games_sample_size") or source.get("games")
    insufficient_sample = sample_size is not None and (float(sample_size or 0) < 8)

    shot_volume = weighted_average(
        (
            (score_from_range(source.get("shots_for_per_game"), low=22, high=38), 0.7),
            (score_from_range(source.get("shots_against_per_game"), low=22, high=38, inverse=True), 0.55),
            (score_from_range(source.get("shot_attempts_for_per_game"), low=42, high=72), 0.45),
            (score_from_range(source.get("shot_attempts_against_per_game"), low=42, high=72, inverse=True), 0.35),
        )
    )
    possession = weighted_average(
        (
            (score_centered(source.get("shot_share"), center=0.5, span=0.18), 0.75),
            (score_centered(source.get("xg_share"), center=0.5, span=0.18), 0.85),
            (shot_volume, 0.45),
        )
    )
    xg_quality = weighted_average(
        (
            (score_from_range(source.get("expected_goals_for_per_game"), low=1.8, high=4.2), 0.75),
            (score_from_range(source.get("expected_goals_against_per_game"), low=1.8, high=4.2, inverse=True), 0.65),
            (score_centered(source.get("xg_share"), center=0.5, span=0.18), 0.9),
            (score_from_range(source.get("goals_for_per_game"), low=1.8, high=4.2), 0.2),
        )
    )
    high_danger = weighted_average(
        (
            (score_from_range(source.get("high_danger_chances_for"), low=6, high=18), 0.5),
            (score_from_range(source.get("high_danger_chances_against"), low=6, high=18, inverse=True), 0.45),
            (score_from_range(source.get("high_danger_xg_for"), low=0.4, high=1.8), 0.7),
            (score_from_range(source.get("high_danger_xg_against"), low=0.4, high=1.8, inverse=True), 0.65),
        )
    )
    rush_rebound = weighted_average(
        (
            (score_from_range(source.get("rush_chances_for"), low=1, high=9), 0.45),
            (score_from_range(source.get("rush_chances_against"), low=1, high=9, inverse=True), 0.4),
            (score_from_range(source.get("rebound_chances_for"), low=1, high=8), 0.4),
            (score_from_range(source.get("rebound_chances_against"), low=1, high=8, inverse=True), 0.35),
            (score_from_range(source.get("slot_shots_for"), low=2, high=14), 0.45),
        )
    )
    first_period = weighted_average(
        (
            (score_from_range(source.get("first_period_shot_rate"), low=6, high=15), 0.65),
            (score_from_range(source.get("first_period_xg_rate"), low=0.35, high=1.35), 0.8),
            (score_from_range(source.get("first_period_pace_proxy"), low=35, high=75), 0.3),
        )
    )
    pace_volume = weighted_average(
        (
            (score_from_range(source.get("pace_proxy"), low=45, high=75), 0.45),
            (shot_volume, 0.65),
            (score_from_range(source.get("penalty_minutes_rate"), low=4, high=16), 0.2),
        )
    )

    limited_proxy = source.get("expected_goals_for_per_game") in (None, "") and source.get("xg_share") in (None, "")
    if limited_proxy:
        xg_quality = weighted_average(
            (
                (score_from_range(source.get("goals_for_per_game"), low=1.8, high=4.2), 0.4),
                (score_from_range(source.get("goals_against_per_game"), low=1.8, high=4.2, inverse=True), 0.35),
                (shot_volume, 0.3),
            )
        )
    possession_score = weighted_average(((possession, 0.5), (xg_quality, 0.35), (high_danger, 0.15))) or 0.0
    possession_score = clamp(possession_score)
    total_signal = weighted_average(((pace_volume, 0.45), (xg_quality, 0.45), (high_danger, 0.35), (rush_rebound, 0.25))) or 0.0
    team_total_signal = weighted_average(((xg_quality, 0.55), (shot_volume, 0.35), (high_danger, 0.35), (pace_volume, 0.25))) or 0.0
    team_market_signal = weighted_average(((possession_score, 0.55), (xg_quality, 0.4), (high_danger, 0.2))) or 0.0
    if market_type in {"first_period_moneyline", "first_period_total", "first_period_team_total"}:
        total_signal = weighted_average(((total_signal, 0.55), (first_period, 0.75))) or total_signal
        team_market_signal = weighted_average(((team_market_signal, 0.55), (first_period, 0.45))) or team_market_signal

    missing = missing_fields(source, CORE_FIELDS)
    confidence_reason = None
    if data_tier <= 0:
        confidence_reason = "no_team_shot_or_game_context"
    elif limited_proxy:
        confidence_reason = "goals_shots_proxy_only_expected_goals_missing"
    elif insufficient_sample:
        confidence_reason = "small_sample_hockey_possession_context"

    return finalize_hockey_response(
        {
            "possession_score": round(possession_score, 2),
            "shot_volume_score": round(clamp(shot_volume or 0.0), 2),
            "xg_quality_score": round(clamp(xg_quality or 0.0), 2),
            "high_danger_score": round(clamp(high_danger or 0.0), 2),
            "rush_rebound_score": round(clamp(rush_rebound or 0.0), 2),
            "first_period_pressure_score": round(clamp(first_period or 0.0), 2),
            "pace_volume_score": round(clamp(pace_volume or 0.0), 2),
            "team_market_signal_score": round(clamp(team_market_signal), 2),
            "total_signal_score": round(clamp(total_signal), 2),
            "team_total_signal_score": round(clamp(team_total_signal), 2),
            "confidence_cap_reason": confidence_reason,
            "missing_inputs": compact_list(missing, limit=20),
            "insufficient_sample": bool(insufficient_sample),
            "limited_proxy": bool(limited_proxy),
            "xg_fabricated": False,
            "expected_goals_fabricated": False,
        },
        source_payload=source,
    )

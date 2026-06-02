from __future__ import annotations

from typing import Any

from .baseball_impact_common import clamp, compact_list, confidence_from_sample, finalize_baseball_response, missing_fields, present_fields, safe_float, score_centered, score_from_range, weighted_average


RUN_VALUE_INPUTS = (
    "runs_allowed_per_game",
    "runs_scored_per_game",
    "expected_runs_created",
    "expected_runs_allowed",
    "run_differential",
    "first_five_run_differential",
    "starter_era_proxy",
    "starter_fip_proxy",
    "starter_xfip_proxy",
    "pitcher_xwoba_allowed",
    "pitcher_k_rate",
    "pitcher_bb_rate",
    "pitcher_hr_rate",
    "pitcher_ground_ball_rate",
    "pitcher_fly_ball_rate",
    "pitcher_barrel_allowed_rate",
    "pitcher_hard_hit_allowed_rate",
    "pitch_run_value",
    "pitch_type_run_values",
    "plate_appearance_run_value",
    "base_out_run_expectancy_delta",
    "leverage_index_proxy",
    "team_woba",
    "team_xwoba",
    "team_iso",
    "team_k_rate",
    "team_bb_rate",
    "team_barrel_rate",
    "team_hard_hit_rate",
    "lineup_projected_runs_proxy",
    "bullpen_quality_score",
    "park_run_environment_score",
    "umpire_zone_modifier",
)


def _sample(row: dict[str, Any]) -> float:
    for key in ("sample_size", "plate_appearances", "batters_faced", "pitches", "games_sample_size"):
        value = safe_float(row.get(key))
        if value is not None:
            return value
    return 0.0


def evaluate_baseball_run_value_impact(row: dict[str, Any] | None = None, *, data_tier: int | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    present = present_fields(source, RUN_VALUE_INPUTS)
    missing = missing_fields(source, RUN_VALUE_INPUTS)
    sample = _sample(source)
    insufficient = bool(sample and sample < 40)
    pitch_run = safe_float(source.get("pitch_run_value"))
    pa_run = safe_float(source.get("plate_appearance_run_value"))
    limited_proxy = pitch_run is None and pa_run is None and any(source.get(k) not in (None, "", []) for k in ("runs_scored_per_game", "runs_allowed_per_game", "run_differential", "lineup_projected_runs_proxy"))
    pitch_level = score_centered(pitch_run, center=0.0, span=0.18)
    pa_score = score_centered(pa_run or source.get("base_out_run_expectancy_delta"), center=0.0, span=0.20)
    offense = weighted_average(
        (
            (score_from_range(source.get("runs_scored_per_game"), low=3.2, high=6.0), 0.65),
            (score_from_range(source.get("expected_runs_created"), low=3.2, high=6.0), 0.75),
            (score_from_range(source.get("lineup_projected_runs_proxy"), low=3.0, high=6.2), 0.55),
            (score_from_range(source.get("team_woba"), low=0.285, high=0.355), 0.65),
            (score_from_range(source.get("team_xwoba"), low=0.285, high=0.365), 0.65),
            (score_from_range(source.get("team_iso"), low=0.120, high=0.220), 0.35),
            (score_from_range(source.get("team_barrel_rate"), low=0.045, high=0.115), 0.45),
            (pa_score, 0.55),
        )
    )
    pitching = weighted_average(
        (
            (score_from_range(source.get("runs_allowed_per_game"), low=3.2, high=6.0, inverse=True), 0.55),
            (score_from_range(source.get("expected_runs_allowed"), low=3.2, high=6.0, inverse=True), 0.65),
            (score_from_range(source.get("starter_era_proxy"), low=2.5, high=5.7, inverse=True), 0.45),
            (score_from_range(source.get("starter_fip_proxy"), low=2.6, high=5.4, inverse=True), 0.55),
            (score_from_range(source.get("pitcher_xwoba_allowed"), low=0.270, high=0.380, inverse=True), 0.55),
            (score_from_range(source.get("pitcher_k_rate"), low=0.14, high=0.34), 0.35),
            (score_from_range(source.get("pitcher_bb_rate"), low=0.045, high=0.13, inverse=True), 0.35),
            (score_from_range(source.get("pitcher_barrel_allowed_rate"), low=0.035, high=0.12, inverse=True), 0.45),
            (pitch_level, 0.55),
        )
    )
    run_value = weighted_average(((offense, 0.55), (pitching, 0.55), (pitch_level, 0.35), (pa_score, 0.35), (score_centered(source.get("run_differential"), center=0.0, span=2.0), 0.4)))
    first_five = weighted_average(((pitching, 0.9), (offense, 0.45), (score_centered(source.get("first_five_run_differential"), center=0.0, span=1.2), 0.55), (pitch_level, 0.35)))
    full_game = weighted_average(((run_value, 0.55), (score_from_range(source.get("bullpen_quality_score"), low=0.0, high=100.0), 0.45), (offense, 0.35), (pitching, 0.35)))
    total_signal = weighted_average(((offense, 0.55), (100.0 - (pitching or 50.0), 0.45), (score_from_range(source.get("park_run_environment_score"), low=0.0, high=100.0), 0.35), (score_from_range(source.get("umpire_zone_modifier"), low=0.0, high=100.0, inverse=True), 0.25)))
    confidence = confidence_from_sample(sample, full_sample=250.0, floor=25.0, cap=88.0)
    cap_reason = None
    if not present:
        cap_reason = "missing_run_value_inputs"
        confidence = 15.0
    elif insufficient:
        cap_reason = "sample_too_small"
        confidence = min(confidence, 45.0)
    elif limited_proxy:
        cap_reason = "run_value_missing_limited_basic_proxy"
        confidence = min(confidence, 52.0)
    return finalize_baseball_response(
        {
            "run_value_score": round(clamp(run_value or 0.0), 2),
            "pitch_level_score": round(clamp(pitch_level or 0.0), 2),
            "plate_appearance_score": round(clamp(pa_score or 0.0), 2),
            "team_offense_score": round(clamp(offense or 0.0), 2),
            "team_pitching_score": round(clamp(pitching or 0.0), 2),
            "first_five_signal_score": round(clamp(first_five or 0.0), 2),
            "full_game_signal_score": round(clamp(full_game or 0.0), 2),
            "total_signal_score": round(clamp(total_signal or 0.0), 2),
            "team_total_signal_score": round(clamp(weighted_average(((offense, 0.7), (total_signal, 0.35))) or 0.0), 2),
            "confidence_cap": round(clamp(confidence), 2),
            "confidence_cap_reason": cap_reason,
            "missing_inputs": compact_list(missing, limit=35),
            "insufficient_sample": insufficient or sample == 0.0,
            "limited_proxy": bool(limited_proxy),
            "run_value_fabricated": False,
            "data_tier": data_tier,
        },
        source_payload=source,
    )

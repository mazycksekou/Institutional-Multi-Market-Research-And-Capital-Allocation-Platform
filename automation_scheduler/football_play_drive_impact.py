from __future__ import annotations

from typing import Any

from .football_impact_schema import (
    average_present,
    clamp,
    compact_list,
    confidence_from_sample,
    finalize_football_response,
    missing_fields,
    present_fields,
    safe_float,
    score_centered,
    score_from_range,
    weighted_average,
)


PLAY_DRIVE_INPUTS = (
    "epa_per_play",
    "success_rate",
    "explosive_play_rate",
    "negative_play_rate",
    "early_down_success_rate",
    "third_down_success_rate",
    "fourth_down_success_rate",
    "red_zone_epa",
    "red_zone_td_rate",
    "finishing_drives_points_per_trip",
    "drive_success_rate",
    "points_per_drive",
    "yards_per_play",
    "points_per_game",
    "yards_per_game",
    "plays_per_game",
    "seconds_per_play",
    "turnover_rate",
    "penalty_epa",
    "field_position_value",
    "garbage_time_adjusted",
)


def _sample_size(row: dict[str, Any]) -> float:
    for key in ("plays_sample_size", "play_count", "plays", "sample_size"):
        value = safe_float(row.get(key))
        if value is not None:
            return value
    drives = safe_float(row.get("drives_sample_size") or row.get("drive_count"))
    if drives is not None:
        return drives * 6.0
    games = safe_float(row.get("games_sample_size") or row.get("games"))
    if games is not None:
        return games * 60.0
    return 0.0


def evaluate_football_play_drive_impact(row: dict[str, Any] | None = None, *, data_tier: int | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    present = present_fields(source, PLAY_DRIVE_INPUTS)
    missing = missing_fields(source, PLAY_DRIVE_INPUTS)
    sample = _sample_size(source)
    insufficient_sample = bool(sample and sample < 40.0)
    epa = safe_float(source.get("epa_per_play"))
    proxy_allowed = epa is None and any(source.get(key) not in (None, "", []) for key in ("yards_per_play", "points_per_drive", "points_per_game", "yards_per_game", "success_rate"))

    epa_score = score_centered(epa, center=0.0, span=0.22) if epa is not None else None
    if epa_score is None and proxy_allowed:
        yards_proxy = score_from_range(source.get("yards_per_play"), low=4.0, high=7.2)
        if yards_proxy is None:
            yards_proxy = score_from_range(source.get("yards_per_game"), low=250.0, high=470.0)
        points_proxy = score_from_range(source.get("points_per_drive"), low=1.1, high=3.1)
        if points_proxy is None:
            points_proxy = score_from_range(source.get("points_per_game"), low=14.0, high=36.0)
        epa_score = weighted_average(
            (
                (yards_proxy, 0.6),
                (points_proxy, 0.7),
                (score_from_range(source.get("success_rate"), low=0.34, high=0.55), 0.7),
            )
        )

    success = score_from_range(source.get("success_rate"), low=0.34, high=0.55)
    explosive = score_from_range(source.get("explosive_play_rate"), low=0.04, high=0.18)
    negative_inverse = score_from_range(source.get("negative_play_rate"), low=0.08, high=0.24, inverse=True)
    early = score_from_range(source.get("early_down_success_rate"), low=0.34, high=0.56)
    third = score_from_range(source.get("third_down_success_rate"), low=0.28, high=0.52)
    fourth = score_from_range(source.get("fourth_down_success_rate"), low=0.35, high=0.75)
    red_epa = score_centered(source.get("red_zone_epa"), center=0.0, span=0.45)
    red_td = score_from_range(source.get("red_zone_td_rate"), low=0.38, high=0.72)
    finish = score_from_range(source.get("finishing_drives_points_per_trip"), low=2.8, high=5.4)
    drive_success = score_from_range(source.get("drive_success_rate"), low=0.28, high=0.58)
    points_drive = score_from_range(source.get("points_per_drive"), low=1.1, high=3.1)
    if points_drive is None:
        points_drive = score_from_range(source.get("points_per_game"), low=14.0, high=36.0)
    yards_play = score_from_range(source.get("yards_per_play"), low=4.0, high=7.2)
    if yards_play is None:
        yards_play = score_from_range(source.get("yards_per_game"), low=250.0, high=470.0)
    plays_game = score_from_range(source.get("plays_per_game"), low=54.0, high=76.0)
    seconds_play = score_from_range(source.get("seconds_per_play"), low=34.0, high=22.0)
    turnover_inverse = score_from_range(source.get("turnover_rate"), low=0.02, high=0.18, inverse=True)
    penalty_epa = safe_float(source.get("penalty_epa"))
    penalty_score = score_centered(penalty_epa, center=0.0, span=0.18) if penalty_epa is not None else None
    field_position = score_centered(source.get("field_position_value"), center=0.0, span=0.18)

    efficiency = weighted_average(((epa_score, 1.35), (success, 1.0), (yards_play, 0.65), (points_drive, 0.75)))
    explosiveness_score = weighted_average(((explosive, 1.0), (yards_play, 0.45), (negative_inverse, 0.35)))
    consistency = weighted_average(((success, 0.9), (early, 0.7), (negative_inverse, 0.85), (turnover_inverse, 0.65)))
    red_zone = weighted_average(((red_epa, 0.75), (red_td, 0.85), (finish, 0.65)))
    leverage = weighted_average(((third, 0.85), (fourth, 0.45), (red_zone, 0.85), (field_position, 0.35)))
    pace_volume = weighted_average(((plays_game, 0.75), (seconds_play, 0.65)))
    drive_impact = weighted_average(((drive_success, 0.75), (points_drive, 1.0), (red_zone, 0.6), (field_position, 0.35), (turnover_inverse, 0.45)))
    play_impact = weighted_average(((efficiency, 1.15), (explosiveness_score, 0.7), (consistency, 0.7), (leverage, 0.5)))

    turnover_penalty = round(100.0 - clamp(turnover_inverse or 100.0), 2)
    penalty_penalty = round(100.0 - clamp(penalty_score or 100.0), 2)
    confidence = confidence_from_sample(sample, full_sample=600.0, floor=28.0, cap=92.0)
    cap_reason = None
    if not present:
        cap_reason = "missing_play_drive_inputs"
        confidence = min(confidence, 15.0)
    elif insufficient_sample:
        cap_reason = "sample_too_small"
        confidence = min(confidence, 45.0)
    elif epa is None and proxy_allowed:
        cap_reason = "epa_missing_limited_tier_1_proxy"
        confidence = min(confidence, 58.0)

    if epa is None and not proxy_allowed:
        missing = compact_list(["epa_per_play", *missing], limit=30)

    result = {
        "play_impact_score": round(clamp(play_impact or 0.0), 2),
        "drive_impact_score": round(clamp(drive_impact or 0.0), 2),
        "efficiency_score": round(clamp(efficiency or 0.0), 2),
        "explosiveness_score": round(clamp(explosiveness_score or 0.0), 2),
        "consistency_score": round(clamp(consistency or 0.0), 2),
        "leverage_score": round(clamp(leverage or 0.0), 2),
        "red_zone_score": round(clamp(red_zone or 0.0), 2),
        "pace_volume_score": round(clamp(pace_volume or 0.0), 2),
        "turnover_penalty": turnover_penalty,
        "penalty_penalty": penalty_penalty,
        "missing_inputs": compact_list(missing, limit=35),
        "confidence_cap_reason": cap_reason,
        "confidence_score": round(clamp(confidence), 2),
        "insufficient_sample": insufficient_sample or sample == 0.0,
        "sample_size": int(sample),
        "impact_scope": "team_or_unit",
        "epa_fabricated": False,
        "limited_proxy_used": bool(epa is None and proxy_allowed),
        "garbage_time_adjusted": bool(source.get("garbage_time_adjusted")) if source.get("garbage_time_adjusted") not in (None, "") else None,
        "data_tier": data_tier,
    }
    if not present:
        result["status"] = "missing"
    elif cap_reason:
        result["status"] = "limited"
    else:
        result["status"] = "ready"
    return finalize_football_response(result, source_payload=source)

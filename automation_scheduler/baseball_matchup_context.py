from __future__ import annotations

from typing import Any

from .baseball_impact_common import clamp, compact_list, finalize_baseball_response, safe_float, score_centered, score_from_range, weighted_average


def evaluate_baseball_matchup_context(row: dict[str, Any] | None = None, *, market_type: str | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    same_hand = str(source.get("pitcher_handedness") or "").upper() == str(source.get("batter_handedness") or source.get("handedness") or "").upper() and source.get("pitcher_handedness") not in (None, "")
    platoon = score_from_range(source.get("team_platoon_woba") or source.get("platoon_split_woba") or source.get("platoon_split_xwoba"), low=0.285, high=0.390)
    handedness_score = clamp((platoon if platoon is not None else 50.0) + (-6.0 if same_hand else 6.0 if source.get("pitcher_handedness") and source.get("batter_handedness") else 0.0))
    pitch_mix = score_from_range(source.get("pitch_mix_advantage_score"), low=0.0, high=100.0)
    if pitch_mix is None:
        pitch_mix = score_centered(source.get("pitcher_pitch_type_matchup"), center=0.0, span=0.25)
    velocity = score_centered(source.get("velocity_band_matchup"), center=0.0, span=0.20)
    breaking = weighted_average(((score_from_range(source.get("breaking_ball_usage"), low=0.18, high=0.46), 0.4), (score_from_range(source.get("batter_chase_rate"), low=0.20, high=0.38), 0.45), (score_from_range(source.get("batter_whiff_rate"), low=0.16, high=0.34), 0.45)))
    k_matchup = weighted_average(((score_from_range(source.get("pitcher_k_rate"), low=0.14, high=0.34), 0.65), (score_from_range(source.get("opponent_k_rate") or source.get("lineup_k_rate"), low=0.17, high=0.29), 0.65), (score_from_range(source.get("called_strike_plus_whiff_proxy"), low=0.22, high=0.36), 0.35)))
    hr_matchup = weighted_average(((score_from_range(source.get("pitcher_hr_rate"), low=0.015, high=0.055), 0.55), (score_from_range(source.get("pitcher_barrel_allowed_rate"), low=0.035, high=0.12), 0.55), (score_from_range(source.get("lineup_barrel_rate") or source.get("batter_barrel_rate"), low=0.04, high=0.14), 0.65)))
    gb_fb = weighted_average(((score_from_range(source.get("pitcher_ground_ball_rate"), low=0.32, high=0.55), 0.35), (score_from_range(source.get("batter_ground_ball_rate"), low=0.30, high=0.55, inverse=True), 0.25), (score_from_range(source.get("batter_fly_ball_rate"), low=0.25, high=0.48), 0.25)))
    steal = weighted_average(((score_from_range(source.get("stolen_base_attempt_rate"), low=0.01, high=0.16), 0.45), (score_from_range(source.get("pitcher_hold_runner_score"), low=0.0, high=100.0, inverse=True), 0.45), (score_from_range(source.get("catcher_pop_time_proxy"), low=2.15, high=1.82), 0.35)))
    tto = score_from_range(source.get("times_through_order_penalty"), low=0.0, high=0.12)
    umpire = score_from_range(source.get("umpire_zone_size_proxy"), low=0.0, high=100.0)
    h2h = score_centered(source.get("batter_vs_pitcher_history_edge"), center=0.0, span=0.35)
    raw_h2h_weight = safe_float(source.get("batter_vs_pitcher_history_weight"), 0.0) or 0.0
    h2h_weight_used = min(max(raw_h2h_weight, 0.0), 0.1)
    pitcher_matchup = weighted_average(((k_matchup, 0.65), (100.0 - (hr_matchup or 50.0), 0.45), (100.0 - handedness_score, 0.2), (umpire, 0.15)))
    batter_matchup = weighted_average(((handedness_score, 0.45), (pitch_mix, 0.55), (velocity, 0.25), (hr_matchup, 0.45), (gb_fb, 0.25), (h2h, 0.08)))
    team_matchup = weighted_average(((platoon, 0.4), (hr_matchup, 0.35), (100.0 - (k_matchup or 50.0), 0.35), (tto, 0.25)))
    advantage = weighted_average(((pitcher_matchup, 0.45), (batter_matchup, 0.45), (team_matchup, 0.35)))
    risk = weighted_average(((hr_matchup, 0.55), (k_matchup if market_type in {"batter_strikeouts", "pitcher_strikeouts"} else None, 0.4), (tto, 0.35), (100.0 - (pitch_mix or 50.0), 0.25)))
    reasons = []
    no_bet = []
    notes = []
    if pitch_mix is not None:
        reasons.append("pitch_mix_advantage")
        reasons.append("pitch_mix_vs_hitter_profile_available")
        notes.extend(["pitcher_strikeouts", "batter_total_bases", "batter_strikeouts"])
    if k_matchup and k_matchup >= 65:
        reasons.append("strikeout_pitcher_vs_high_k_lineup")
        notes.extend(["pitcher_strikeouts", "batter_strikeouts"])
    if hr_matchup and hr_matchup >= 65:
        reasons.append("barrel_heavy_lineup_vs_homer_prone_pitcher")
        notes.extend(["batter_home_runs", "batter_total_bases", "team_total", "total"])
    if h2h and h2h >= 70:
        reasons.append("batter_vs_pitcher_history_low_weight_only")
        no_bet.append("batter_vs_pitcher_history_must_not_dominate")
        no_bet.append("batter_vs_pitcher_history_low_weight_only")
    if raw_h2h_weight > 0.2:
        reasons.append("batter_vs_pitcher_history_low_weight_only")
        no_bet.append("batter_vs_pitcher_history_must_not_dominate")
        no_bet.append("batter_vs_pitcher_history_low_weight_only")
    if source.get("umpire_name") and umpire is None:
        no_bet.append("umpire_name_without_tendency_data_not_usable")
    return finalize_baseball_response(
        {
            "matchup_advantage_score": round(clamp(advantage or 0.0), 2),
            "matchup_risk_score": round(clamp(risk or 0.0), 2),
            "pitcher_matchup_score": round(clamp(pitcher_matchup or 0.0), 2),
            "batter_matchup_score": round(clamp(batter_matchup or 0.0), 2),
            "team_matchup_score": round(clamp(team_matchup or 0.0), 2),
            "mismatch_reasons": compact_list(reasons, limit=15),
            "no_bet_reasons": compact_list(no_bet, limit=10),
            "market_specific_matchup_notes": compact_list([*notes, market_type], limit=15),
            "first_five_relevance": round(clamp(weighted_average(((pitcher_matchup, 0.75), (batter_matchup, 0.35), (tto, 0.25))) or 0.0), 2),
            "full_game_relevance": round(clamp(weighted_average(((team_matchup, 0.55), (batter_matchup, 0.35), (pitcher_matchup, 0.35))) or 0.0), 2),
            "player_prop_relevance": round(clamp(weighted_average(((pitcher_matchup, 0.45), (batter_matchup, 0.55), (steal, 0.25))) or 0.0), 2),
            "umpire_context_used": umpire is not None,
            "pitch_mix_context_used": pitch_mix is not None,
            "batter_vs_pitcher_history_weight": h2h_weight_used,
        },
        source_payload=source,
    )

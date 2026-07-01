from __future__ import annotations

from typing import Any

from .baseball_impact_common import clamp, compact_list, finalize_baseball_response, missing_fields, score_centered, score_from_range, weighted_average


BATTER_INPUTS = (
    "plate_appearances_projection",
    "lineup_slot",
    "handedness",
    "platoon_split_woba",
    "platoon_split_xwoba",
    "k_rate",
    "bb_rate",
    "chase_rate",
    "whiff_rate",
    "zone_contact_rate",
    "contact_rate",
    "hard_hit_rate",
    "barrel_rate",
    "average_exit_velocity",
    "launch_angle",
    "sweet_spot_rate",
    "xwoba",
    "xba",
    "xslg",
    "iso",
    "pull_rate",
    "ground_ball_rate",
    "fly_ball_rate",
    "sprint_speed",
    "stolen_base_attempt_rate",
    "pitcher_pitch_type_matchup",
    "recent_form_proxy",
    "injury_status",
    "bat_speed",
    "swing_length",
    "squared_up_rate",
    "blast_rate",
    "attack_angle",
)


def evaluate_baseball_batter_impact(row: dict[str, Any] | None = None, *, batter_level_allowed: bool = True, data_tier: int | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    if not batter_level_allowed and not any(source.get(k) not in (None, "", []) for k in ("lineup_slot", "plate_appearances_projection", "confirmed_lineup")):
        return finalize_baseball_response(
            {
                "batter_impact_score": 0.0,
                "contact_quality_score": 0.0,
                "plate_discipline_score": 0.0,
                "power_score": 0.0,
                "hit_probability_proxy": 0.0,
                "total_bases_relevance_score": 0.0,
                "home_run_relevance_score": 0.0,
                "stolen_base_relevance_score": 0.0,
                "strikeout_risk_score": 0.0,
                "batter_market_relevance": [],
                "missing_batter_inputs": ["batter_box_score_context", "batting_order_context"],
                "no_bet_reasons": [],
                "confidence_cap_reason": "batter_level_data_not_available",
                "bat_tracking_inferred": False,
            },
            source_payload=source,
        )
    contact = weighted_average(
        (
            (score_from_range(source.get("hard_hit_rate"), low=0.30, high=0.52), 0.55),
            (score_from_range(source.get("barrel_rate"), low=0.035, high=0.16), 0.7),
            (score_from_range(source.get("average_exit_velocity"), low=86.0, high=94.5), 0.45),
            (score_from_range(source.get("sweet_spot_rate"), low=0.25, high=0.43), 0.35),
            (score_from_range(source.get("xwoba"), low=0.285, high=0.390), 0.7),
            (score_from_range(source.get("xba"), low=0.210, high=0.310), 0.5),
            (score_from_range(source.get("xslg"), low=0.340, high=0.590), 0.55),
            (score_from_range(source.get("squared_up_rate"), low=0.18, high=0.38), 0.25),
        )
    )
    discipline = weighted_average(
        (
            (score_from_range(source.get("bb_rate"), low=0.045, high=0.15), 0.45),
            (score_from_range(source.get("k_rate"), low=0.12, high=0.34, inverse=True), 0.65),
            (score_from_range(source.get("chase_rate"), low=0.20, high=0.38, inverse=True), 0.55),
            (score_from_range(source.get("whiff_rate"), low=0.16, high=0.34, inverse=True), 0.45),
            (score_from_range(source.get("zone_contact_rate"), low=0.76, high=0.91), 0.5),
            (score_from_range(source.get("contact_rate"), low=0.66, high=0.84), 0.45),
        )
    )
    power = weighted_average(
        (
            (score_from_range(source.get("barrel_rate"), low=0.035, high=0.16), 0.75),
            (score_from_range(source.get("xslg"), low=0.340, high=0.590), 0.65),
            (score_from_range(source.get("iso"), low=0.100, high=0.260), 0.6),
            (score_from_range(source.get("fly_ball_rate"), low=0.25, high=0.48), 0.25),
            (score_from_range(source.get("pull_rate"), low=0.30, high=0.52), 0.25),
            (score_from_range(source.get("blast_rate"), low=0.02, high=0.16), 0.25),
            (score_centered(source.get("launch_angle"), center=14.0, span=18.0), 0.25),
        )
    )
    pa_conf = score_from_range(source.get("plate_appearances_projection"), low=2.8, high=5.0)
    if pa_conf is None and source.get("lineup_slot") not in (None, ""):
        try:
            slot = int(float(source.get("lineup_slot")))
            pa_conf = clamp(100.0 - max(0, slot - 1) * 8.5)
        except (TypeError, ValueError):
            pa_conf = None
    platoon = score_from_range(source.get("platoon_split_woba") or source.get("platoon_split_xwoba"), low=0.285, high=0.390)
    hit_prob = weighted_average(((contact, 0.65), (discipline, 0.35), (platoon, 0.35), (pa_conf, 0.45), (score_centered(source.get("recent_form_proxy"), center=0.0, span=0.18), 0.1)))
    tb = weighted_average(((power, 0.65), (contact, 0.55), (pa_conf, 0.35), (platoon, 0.3), (score_centered(source.get("pitcher_pitch_type_matchup"), center=0.0, span=0.25), 0.35)))
    hr = weighted_average(((power, 0.8), (score_from_range(source.get("barrel_rate"), low=0.035, high=0.16), 0.65), (score_centered(source.get("pitcher_pitch_type_matchup"), center=0.0, span=0.25), 0.25)))
    sb = weighted_average(((score_from_range(source.get("sprint_speed"), low=25.0, high=30.5), 0.45), (score_from_range(source.get("stolen_base_attempt_rate"), low=0.01, high=0.16), 0.65), (score_from_range(source.get("stolen_base_success_rate"), low=0.60, high=0.88), 0.35)))
    k_risk = weighted_average(((score_from_range(source.get("k_rate"), low=0.12, high=0.34), 0.75), (score_from_range(source.get("whiff_rate"), low=0.16, high=0.34), 0.55), (score_from_range(source.get("chase_rate"), low=0.20, high=0.38), 0.35)))
    impact = weighted_average(((contact, 0.75), (discipline, 0.45), (power, 0.45), (pa_conf, 0.35), (platoon, 0.25)))
    no_bet = []
    cap_reason = None
    if source.get("confirmed_lineup") is False or source.get("lineup_slot") in (None, ""):
        no_bet.append("batting_order_unknown_caps_batter_prop_confidence")
        cap_reason = "batting_order_unknown"
    if str(source.get("injury_status") or "").lower() in {"questionable", "day_to_day", "gtd", "game_time_decision"}:
        no_bet.append("batter_injury_uncertainty_caps_props")
        cap_reason = "injury_uncertainty"
    missing = missing_fields(source, BATTER_INPUTS)
    return finalize_baseball_response(
        {
            "batter_impact_score": round(clamp(impact or 0.0), 2),
            "contact_quality_score": round(clamp(contact or 0.0), 2),
            "plate_discipline_score": round(clamp(discipline or 0.0), 2),
            "power_score": round(clamp(power or 0.0), 2),
            "hit_probability_proxy": round(clamp(hit_prob or 0.0), 2),
            "total_bases_relevance_score": round(clamp(tb or 0.0), 2),
            "home_run_relevance_score": round(clamp(hr or 0.0), 2),
            "stolen_base_relevance_score": round(clamp(sb or 0.0), 2),
            "strikeout_risk_score": round(clamp(k_risk or 0.0), 2),
            "batter_market_relevance": ["batter_hits", "batter_total_bases", "batter_home_runs", "batter_rbis", "batter_runs", "batter_stolen_bases", "batter_walks", "batter_strikeouts"],
            "missing_batter_inputs": compact_list(missing, limit=35),
            "missing_bat_tracking_inputs": compact_list([k for k in ("bat_speed", "swing_length", "squared_up_rate", "blast_rate", "attack_angle") if source.get(k) in (None, "", [])], limit=10),
            "no_bet_reasons": compact_list(no_bet, limit=12),
            "confidence_cap_reason": cap_reason,
            "recent_form_modifier_only": source.get("recent_form_proxy") not in (None, ""),
            "platoon_split_fabricated": False,
            "bat_tracking_inferred": False,
            "data_tier": data_tier,
        },
        source_payload=source,
    )

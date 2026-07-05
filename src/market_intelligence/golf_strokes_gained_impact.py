from __future__ import annotations

from typing import Any

from .golf_impact_common import clamp, compact_list, finalize_golf_response, missing_fields, safe_float, score_centered, score_from_range, weighted_average


SG_INPUTS = (
    "sg_total",
    "sg_tee_to_green",
    "sg_off_the_tee",
    "sg_approach",
    "sg_around_the_green",
    "sg_putting",
    "sg_ball_striking",
    "sg_short_game",
    "recent_sg_total",
    "long_term_sg_total",
    "recent_sg_tee_to_green",
    "long_term_sg_tee_to_green",
    "recent_sg_putting",
    "long_term_sg_putting",
    "scoring_average",
    "birdie_or_better_rate",
    "bogey_avoidance_rate",
    "double_bogey_rate",
    "par_3_scoring",
    "par_4_scoring",
    "par_5_scoring",
    "round_1_scoring",
    "weekend_scoring",
    "cut_rate",
    "volatility_proxy",
    "sample_size",
)


def evaluate_golf_strokes_gained_impact(row: dict[str, Any] | None = None, *, data_tier: int | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    sg_total = score_centered(source.get("sg_total"), center=0.0, span=2.0)
    t2g = score_centered(source.get("sg_tee_to_green"), center=0.0, span=1.6)
    ott = score_centered(source.get("sg_off_the_tee"), center=0.0, span=0.8)
    app = score_centered(source.get("sg_approach"), center=0.0, span=1.0)
    arg = score_centered(source.get("sg_around_the_green"), center=0.0, span=0.7)
    putt = score_centered(source.get("sg_putting"), center=0.0, span=1.0)
    ball = weighted_average(((score_centered(source.get("sg_ball_striking"), center=0.0, span=1.4), 0.5), (ott, 0.4), (app, 0.7), (t2g, 0.35)))
    short = weighted_average(((score_centered(source.get("sg_short_game"), center=0.0, span=0.9), 0.5), (arg, 0.45), (putt, 0.35)))
    scoring = weighted_average(
        (
            (score_from_range(source.get("scoring_average"), low=72.8, high=68.0), 0.65),
            (score_from_range(source.get("round_1_scoring"), low=72.8, high=67.8), 0.25),
            (score_from_range(source.get("weekend_scoring"), low=72.8, high=68.0), 0.25),
        )
    )
    birdie_bogey = weighted_average(
        (
            (score_from_range(source.get("birdie_or_better_rate"), low=0.14, high=0.30), 0.55),
            (score_from_range(source.get("bogey_avoidance_rate"), low=0.72, high=0.90), 0.55),
            (score_from_range(source.get("double_bogey_rate"), low=0.055, high=0.005), 0.35),
        )
    )
    cut_profile = weighted_average(((score_from_range(source.get("cut_rate"), low=0.45, high=0.90), 0.75), (t2g, 0.35), (score_from_range(source.get("bogey_avoidance_rate"), low=0.72, high=0.90), 0.35)))
    volatility = score_from_range(source.get("volatility_proxy") or source.get("putting_volatility"), low=0.0, high=1.0)
    if volatility is None:
        volatility = weighted_average(((100.0 - (t2g or 50.0), 0.25), (putt, 0.2)))
    recent = safe_float(source.get("recent_sg_total"))
    baseline = safe_float(source.get("long_term_sg_total"))
    delta = None if recent is None or baseline is None else round(recent - baseline, 4)
    recent_delta_score = score_centered(delta, center=0.0, span=1.0)
    sample = safe_float(source.get("sample_size"), 0.0) or 0.0
    insufficient = sample < 24
    limited_proxy = sg_total is None and t2g is None and scoring is not None
    confidence_reason = None
    if limited_proxy:
        confidence_reason = "strokes_gained_missing_scoring_average_limited_proxy"
    if insufficient:
        confidence_reason = "sample_too_small" if confidence_reason is None else f"{confidence_reason};sample_too_small"
    if source.get("recent_sg_putting") not in (None, "") and source.get("long_term_sg_putting") not in (None, ""):
        putt_delta = (safe_float(source.get("recent_sg_putting"), 0.0) or 0.0) - (safe_float(source.get("long_term_sg_putting"), 0.0) or 0.0)
        if putt_delta >= 0.8:
            confidence_reason = "recent_putting_spike_volatility_warning" if confidence_reason is None else f"{confidence_reason};recent_putting_spike_volatility_warning"
            volatility = max(volatility or 0.0, 75.0)
    overall = weighted_average(((sg_total, 0.75), (t2g, 0.55), (ball, 0.45), (short, 0.25), (scoring, 0.35), (birdie_bogey, 0.35), (recent_delta_score, 0.15)))
    if overall is None and limited_proxy:
        overall = scoring
    return finalize_golf_response(
        {
            "strokes_gained_score": round(clamp(overall or 0.0), 2),
            "tee_to_green_score": round(clamp(t2g or weighted_average(((ott, 0.35), (app, 0.55), (arg, 0.15))) or 0.0), 2),
            "ball_striking_score": round(clamp(ball or 0.0), 2),
            "short_game_score": round(clamp(short or 0.0), 2),
            "putting_score": round(clamp(putt or 0.0), 2),
            "scoring_score": round(clamp(scoring or 0.0), 2),
            "birdie_bogey_score": round(clamp(birdie_bogey or 0.0), 2),
            "cut_made_profile_score": round(clamp(cut_profile or 0.0), 2),
            "volatility_score": round(clamp(volatility or 0.0), 2),
            "recent_vs_baseline_delta": delta,
            "confidence_cap_reason": confidence_reason,
            "missing_inputs": compact_list(missing_fields(source, SG_INPUTS), limit=35),
            "insufficient_sample": insufficient,
            "limited_proxy": bool(limited_proxy),
            "sg_splits_fabricated": False,
            "data_tier": data_tier,
        },
        source_payload=source,
    )

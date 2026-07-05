from __future__ import annotations

from typing import Any

from .golf_impact_common import clamp, compact_list, finalize_golf_response, missing_fields, percent_score, safe_float, score_centered, score_from_range, weighted_average


SHORT_PUTTING_INPUTS = (
    "sg_around_the_green",
    "scrambling_rate",
    "sand_save_rate",
    "bunker_proximity",
    "rough_short_game_skill",
    "missed_green_recovery_rate",
    "difficult_lie_recovery_proxy",
    "sg_putting",
    "putts_per_round",
    "three_putt_avoidance",
    "make_rate_inside_5",
    "make_rate_5_10",
    "make_rate_10_15",
    "make_rate_15_25",
    "lag_putting_skill",
    "putting_from_distance_proxy",
    "green_speed_fit",
    "grass_type_fit",
    "bermuda_putting_fit",
    "bentgrass_putting_fit",
    "poa_putting_fit",
    "paspalum_putting_fit",
    "putting_volatility",
    "recent_putting_delta",
    "long_term_putting_baseline",
)


def evaluate_golf_short_game_putting_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    arg = score_centered(source.get("sg_around_the_green"), center=0.0, span=0.7)
    scramble = score_from_range(source.get("scrambling_rate"), low=0.50, high=0.70)
    sand = score_from_range(source.get("sand_save_rate"), low=0.38, high=0.62)
    bunker = score_from_range(source.get("bunker_proximity"), low=13.0, high=7.0)
    rough_short = score_from_range(source.get("rough_short_game_skill"), low=0.0, high=100.0)
    recovery = weighted_average(((score_from_range(source.get("missed_green_recovery_rate"), low=0.45, high=0.70), 0.45), (score_from_range(source.get("difficult_lie_recovery_proxy"), low=0.0, high=100.0), 0.25)))
    short_game = weighted_average(((arg, 0.65), (scramble, 0.45), (sand, 0.25), (bunker, 0.25), (rough_short, 0.25), (recovery, 0.35)))
    sg_putt = score_centered(source.get("sg_putting"), center=0.0, span=1.0)
    putts_proxy = score_from_range(source.get("putts_per_round"), low=30.5, high=27.2)
    inside5 = score_from_range(source.get("make_rate_inside_5"), low=0.88, high=0.98)
    mid = weighted_average(((score_from_range(source.get("make_rate_5_10"), low=0.35, high=0.55), 0.3), (score_from_range(source.get("make_rate_10_15"), low=0.20, high=0.34), 0.25), (score_from_range(source.get("make_rate_15_25"), low=0.10, high=0.20), 0.2)))
    lag = score_from_range(source.get("lag_putting_skill") or source.get("putting_from_distance_proxy"), low=0.0, high=100.0)
    three_putt_avoid = score_from_range(source.get("three_putt_avoidance"), low=0.94, high=0.985)
    grass_scores = [
        percent_score(source.get("grass_type_fit")),
        percent_score(source.get("bermuda_putting_fit")),
        percent_score(source.get("bentgrass_putting_fit")),
        percent_score(source.get("poa_putting_fit")),
        percent_score(source.get("paspalum_putting_fit")),
    ]
    grass_fit = weighted_average((score, 1.0) for score in grass_scores)
    green_speed = percent_score(source.get("green_speed_fit"))
    putting = weighted_average(((sg_putt, 0.75), (putts_proxy if sg_putt is not None else None, 0.15), (inside5, 0.25), (mid, 0.35), (lag, 0.25), (three_putt_avoid, 0.3), (grass_fit, 0.2), (green_speed, 0.15)))
    volatility = percent_score(source.get("putting_volatility"))
    recent_delta = safe_float(source.get("recent_putting_delta"))
    baseline = safe_float(source.get("long_term_putting_baseline"))
    if volatility is None and recent_delta is not None:
        volatility = clamp(abs(recent_delta) * 70.0)
    if recent_delta is None and source.get("recent_sg_putting") not in (None, "") and baseline is not None:
        recent_delta = (safe_float(source.get("recent_sg_putting"), 0.0) or 0.0) - baseline
        volatility = max(volatility or 0.0, clamp(abs(recent_delta) * 70.0))
    three_putt_risk = 100.0 - (three_putt_avoid if three_putt_avoid is not None else 50.0)
    no_bet: list[str] = []
    if sg_putt is None and putts_proxy is not None:
        no_bet.append("putts_alone_do_not_fabricate_sg_putting")
    if grass_fit is None:
        no_bet.append("grass_fit_requires_grass_specific_history")
    if recent_delta is not None and recent_delta >= 0.8:
        no_bet.append("recent_putting_spike_volatility_warning")
        volatility = max(volatility or 0.0, 78.0)
    return finalize_golf_response(
        {
            "short_game_score": round(clamp(short_game or 0.0), 2),
            "scrambling_score": round(clamp(scramble or 0.0), 2),
            "bunker_score": round(clamp(weighted_average(((sand, 0.55), (bunker, 0.35))) or 0.0), 2),
            "putting_score": round(clamp(putting or 0.0), 2),
            "grass_fit_score": round(clamp(grass_fit or 0.0), 2),
            "three_putt_risk_score": round(clamp(three_putt_risk), 2),
            "putting_volatility_score": round(clamp(volatility or 0.0), 2),
            "score_save_modifier": round(clamp(weighted_average(((short_game, 0.55), (putting, 0.35), (100.0 - three_putt_risk, 0.25))) or 0.0), 2),
            "sg_putting_fabricated": False,
            "grass_fit_fabricated": False,
            "missing_inputs": compact_list(missing_fields(source, SHORT_PUTTING_INPUTS), limit=35),
            "no_bet_reasons": compact_list(no_bet, limit=12),
        },
        source_payload=source,
    )

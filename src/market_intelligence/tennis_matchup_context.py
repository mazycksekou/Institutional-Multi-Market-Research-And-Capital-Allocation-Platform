from __future__ import annotations

from typing import Any

from .tennis_impact_common import categorical_score, clamp, compact_list, finalize_tennis_response, missing_fields, percent_score, safe_float, score_from_range, weighted_average


MATCHUP_INPUTS = (
    "player_a_handedness",
    "player_b_handedness",
    "lefty_vs_righty_context",
    "backhand_weakness_proxy",
    "forehand_strength_proxy",
    "return_position",
    "serve_direction_preference",
    "rally_length_preference",
    "short_rally_win_rate",
    "medium_rally_win_rate",
    "long_rally_win_rate",
    "net_approach_rate",
    "net_points_won",
    "baseline_consistency_proxy",
    "winner_error_ratio",
    "forced_error_creation",
    "unforced_error_rate",
    "slice_usage",
    "topspin_heavy_context",
    "drop_shot_usage",
    "movement_defense_score",
    "opponent_style_bucket",
    "previous_head_to_head_context",
)


def _hand(value: Any) -> str:
    return str(value or "").strip().lower()[:1]


def _h2h_score(value: Any) -> tuple[float | None, int]:
    if isinstance(value, dict):
        starts = int(safe_float(value.get("matches"), 0.0) or 0)
        score = percent_score(value.get("win_rate") or value.get("score"))
        return score, starts
    return percent_score(value), 0


def evaluate_tennis_matchup_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    a_hand = _hand(source.get("player_a_handedness"))
    b_hand = _hand(source.get("player_b_handedness"))
    handed_supplied = a_hand in {"r", "l"} and b_hand in {"r", "l"}
    handedness = 58.0 if handed_supplied and a_hand != b_hand else 52.0 if handed_supplied else None
    lefty_context = percent_score(source.get("lefty_vs_righty_context"))
    backhand = percent_score(source.get("backhand_weakness_proxy"))
    forehand = percent_score(source.get("forehand_strength_proxy"))
    return_position = percent_score(source.get("return_position"))
    serve_direction = percent_score(source.get("serve_direction_preference"))
    short = score_from_range(source.get("short_rally_win_rate"), low=0.44, high=0.58)
    medium = score_from_range(source.get("medium_rally_win_rate"), low=0.44, high=0.58)
    long = score_from_range(source.get("long_rally_win_rate"), low=0.44, high=0.58)
    rally_pref = categorical_score(source.get("rally_length_preference"), {"short": short or 65.0, "medium": medium or 60.0, "long": long or 62.0})
    net = weighted_average(((score_from_range(source.get("net_approach_rate"), low=0.02, high=0.18), 0.25), (score_from_range(source.get("net_points_won"), low=0.54, high=0.72), 0.35)))
    baseline = percent_score(source.get("baseline_consistency_proxy"))
    winner_error = score_from_range(source.get("winner_error_ratio"), low=0.5, high=1.6)
    forced = percent_score(source.get("forced_error_creation"))
    unforced = score_from_range(source.get("unforced_error_rate"), low=0.34, high=0.12)
    slice = percent_score(source.get("slice_usage"))
    topspin = percent_score(source.get("topspin_heavy_context"))
    drop = percent_score(source.get("drop_shot_usage"))
    movement = percent_score(source.get("movement_defense_score"))
    shot_inputs_supplied = any(
        source.get(key) not in (None, "", [])
        for key in (
            "backhand_weakness_proxy",
            "forehand_strength_proxy",
            "return_position",
            "serve_direction_preference",
            "rally_length_preference",
            "short_rally_win_rate",
            "medium_rally_win_rate",
            "long_rally_win_rate",
            "net_approach_rate",
            "net_points_won",
            "baseline_consistency_proxy",
            "winner_error_ratio",
            "forced_error_creation",
            "unforced_error_rate",
            "slice_usage",
            "topspin_heavy_context",
            "drop_shot_usage",
            "movement_defense_score",
            "opponent_style_bucket",
        )
    )
    style = (
        weighted_average(
            (
                (forehand, 0.25),
                (100.0 - backhand if backhand is not None else None, 0.2),
                (baseline, 0.3),
                (winner_error, 0.25),
                (forced, 0.2),
                (unforced, 0.2),
                (movement, 0.2),
                (net, 0.15),
                (slice, 0.1),
                (topspin, 0.1),
                (drop, 0.1),
            )
        )
        if shot_inputs_supplied
        else None
    )
    serve_matchup = weighted_average(((serve_direction, 0.35), (handedness, 0.2), (backhand, 0.2), (short, 0.2)))
    return_matchup = weighted_average(((return_position, 0.25), (lefty_context, 0.2), (medium, 0.2), (long, 0.15)))
    rally = weighted_average(((rally_pref, 0.25), (short, 0.2), (medium, 0.2), (long, 0.2), (style, 0.35)))
    h2h, h2h_sample = _h2h_score(source.get("previous_head_to_head_context"))
    advantage = weighted_average(((serve_matchup, 0.3), (return_matchup, 0.3), (rally, 0.35), (handedness, 0.15), (min(h2h_sample / 5.0, 1.0) * (h2h or 0.0) if h2h is not None else None, 0.08)))
    conflict = 0.0
    if serve_matchup is not None and return_matchup is not None and abs(serve_matchup - return_matchup) >= 35:
        conflict = 35.0
    if rally is not None and style is not None and abs(rally - style) >= 35:
        conflict = max(conflict, 30.0)
    risk = weighted_average(((conflict, 0.45), (100.0 - (advantage or 50.0), 0.3), (100.0 - (movement or 50.0), 0.15)))
    no_bet: list[str] = []
    if not handed_supplied:
        no_bet.append("handedness_missing_no_handedness_claim")
    if style is None:
        no_bet.append("shot_pattern_missing_no_style_claim")
    if h2h_sample and h2h_sample < 4:
        no_bet.append("head_to_head_low_weight_sample_capped")
    if conflict:
        no_bet.append("conflicting_matchup_signals_reduce_confidence")
    return finalize_tennis_response(
        {
            "matchup_advantage_score": round(clamp(advantage or 0.0), 2),
            "matchup_risk_score": round(clamp(risk or 0.0), 2),
            "serve_matchup_score": round(clamp(serve_matchup or 0.0), 2),
            "return_matchup_score": round(clamp(return_matchup or 0.0), 2),
            "rally_matchup_score": round(clamp(rally or 0.0), 2),
            "handedness_matchup_score": round(clamp(handedness or 0.0), 2),
            "handedness_fabricated": False,
            "shot_pattern_fabricated": False,
            "head_to_head_weight": round(min(h2h_sample / 5.0, 1.0) * 0.08, 3) if h2h_sample else 0.0,
            "tactical_mismatch_reasons": compact_list(["lefty_righty_matchup_supplied" if handed_supplied and a_hand != b_hand else None, "rally_style_matchup_supplied" if rally is not None else None, "conflicting_matchup_signals" if conflict else None], limit=10),
            "no_bet_reasons": compact_list(no_bet, limit=12),
            "market_specific_matchup_notes": compact_list(["style_matchup_modifier_only", "head_to_head_low_weight"], limit=10),
            "moneyline_relevance": round(clamp(weighted_average(((advantage, 0.45), (100.0 - (risk or 0.0), 0.25))) or 0.0), 2),
            "total_games_relevance": round(clamp(weighted_average(((rally, 0.35), (serve_matchup, 0.25), (return_matchup, 0.25))) or 0.0), 2),
            "handicap_relevance": round(clamp(weighted_average(((advantage, 0.45), (return_matchup, 0.3), (serve_matchup, 0.25))) or 0.0), 2),
            "player_prop_relevance": round(clamp(weighted_average(((serve_matchup, 0.3), (return_matchup, 0.3), (rally, 0.25))) or 0.0), 2),
            "missing_inputs": compact_list(missing_fields(source, MATCHUP_INPUTS), limit=35),
        },
        source_payload=source,
    )

from __future__ import annotations

from typing import Any

from .tennis_impact_common import clamp, compact_list, finalize_tennis_response, missing_fields, percent_score, safe_float, score_from_range, weighted_average


FORMAT_INPUTS = (
    "best_of",
    "player_a_hold_probability",
    "player_b_hold_probability",
    "player_a_break_probability",
    "player_b_break_probability",
    "player_a_tiebreak_probability",
    "player_b_tiebreak_probability",
    "set_win_probability",
    "match_win_probability",
    "first_set_win_probability",
    "total_games_projection",
    "total_sets_projection",
    "game_handicap_projection",
    "set_handicap_projection",
    "correct_score_distribution",
    "tiebreak_probability",
    "first_set_tiebreak_probability",
    "retire_or_walkover_risk",
    "sample_size",
)


def _best_of_score(value: Any) -> tuple[int | None, float | None]:
    number = safe_float(value)
    if number in {3.0, 5.0}:
        return int(number), 65.0 if int(number) == 3 else 78.0
    return None, None


def evaluate_tennis_format_markov_context(row: dict[str, Any] | None = None) -> dict[str, Any]:
    source = row if isinstance(row, dict) else {}
    best_of, format_score = _best_of_score(source.get("best_of"))
    a_hold = score_from_range(source.get("player_a_hold_probability"), low=0.62, high=0.88)
    b_hold = score_from_range(source.get("player_b_hold_probability"), low=0.62, high=0.88)
    a_break = score_from_range(source.get("player_a_break_probability"), low=0.12, high=0.35)
    b_break = score_from_range(source.get("player_b_break_probability"), low=0.12, high=0.35)
    hold_balance_raw = None
    if a_hold is not None and b_hold is not None:
        hold_balance_raw = 100.0 - abs(a_hold - b_hold)
    hold_break_balance = weighted_average(((hold_balance_raw, 0.45), (a_hold, 0.25), (b_hold, 0.25), (a_break, 0.15), (b_break, 0.15)))
    a_tb = percent_score(source.get("player_a_tiebreak_probability"))
    b_tb = percent_score(source.get("player_b_tiebreak_probability"))
    tb = percent_score(source.get("tiebreak_probability"))
    first_tb = percent_score(source.get("first_set_tiebreak_probability"))
    match_win = percent_score(source.get("match_win_probability"))
    set_win = percent_score(source.get("set_win_probability"))
    first_set = percent_score(source.get("first_set_win_probability"))
    total_games = score_from_range(source.get("total_games_projection"), low=18.0, high=29.0)
    total_sets = score_from_range(source.get("total_sets_projection"), low=2.0, high=4.5)
    game_handicap = 100.0 - min(abs(safe_float(source.get("game_handicap_projection"), 0.0) or 0.0) * 12.0, 100.0) if source.get("game_handicap_projection") not in (None, "") else None
    set_handicap = 100.0 - min(abs(safe_float(source.get("set_handicap_projection"), 0.0) or 0.0) * 35.0, 100.0) if source.get("set_handicap_projection") not in (None, "") else None
    correct_score_dist = source.get("correct_score_distribution")
    correct_score_supported = isinstance(correct_score_dist, dict) and bool(correct_score_dist)
    correct_score = max((percent_score(v) or 0.0 for v in correct_score_dist.values()), default=0.0) if correct_score_supported else None
    retirement = percent_score(source.get("retire_or_walkover_risk"))
    sample = safe_float(source.get("sample_size"), 0.0) or 0.0
    limited_proxy = any(value is not None for value in (a_hold, b_hold, a_break, b_break)) and not any(value is not None for value in (match_win, set_win, total_games, total_sets, correct_score))
    markov = weighted_average(((hold_break_balance, 0.45), (match_win, 0.35), (set_win, 0.25), (format_score, 0.15), (100.0 - (retirement or 0.0), 0.2)))
    tiebreak_score = weighted_average(((tb, 0.55), (first_tb, 0.35), (a_tb, 0.2), (b_tb, 0.2), (hold_break_balance, 0.2)))
    no_bet: list[str] = []
    if best_of is None:
        no_bet.append("best_of_missing_caps_correct_score_total_sets")
    if correct_score_supported:
        no_bet.append("correct_score_heavily_calibration_capped")
    if retirement and retirement >= 45:
        no_bet.append("retirement_risk_caps_all_match_set_game_markets")
    if limited_proxy:
        no_bet.append("limited_hold_break_markov_proxy_no_distribution")
    if best_of == 5:
        no_bet.append("best_of_five_changes_fatigue_comeback_dynamics")
    return finalize_tennis_response(
        {
            "markov_context_score": round(clamp(markov or 0.0), 2),
            "hold_break_balance_score": round(clamp(hold_break_balance or 0.0), 2),
            "match_win_relevance_score": round(clamp(match_win or markov or 0.0), 2),
            "set_market_relevance_score": round(clamp(weighted_average(((set_win, 0.4), (first_set, 0.25), (format_score, 0.2), (hold_break_balance, 0.25))) or 0.0), 2),
            "total_games_relevance_score": round(clamp(weighted_average(((total_games, 0.55), (hold_break_balance, 0.35), (tiebreak_score, 0.25))) or 0.0), 2),
            "tiebreak_relevance_score": round(clamp(tiebreak_score or 0.0), 2),
            "correct_score_relevance_score": round(clamp(weighted_average(((correct_score, 0.45), (match_win, 0.25), (set_win, 0.25), (100.0 - (retirement or 0.0), 0.2))) or 0.0), 2),
            "game_handicap_relevance_score": round(clamp(weighted_average(((game_handicap, 0.35), (hold_break_balance, 0.35), (match_win, 0.25))) or 0.0), 2),
            "format_confidence_cap": "best_of_missing" if best_of is None else "correct_score_extra_capped" if correct_score_supported else None,
            "best_of": best_of,
            "markov_distribution_fabricated": False,
            "limited_proxy": limited_proxy,
            "insufficient_sample": sample < 20,
            "missing_inputs": compact_list(missing_fields(source, FORMAT_INPUTS), limit=35),
            "no_bet_reasons": compact_list(no_bet, limit=12),
        },
        source_payload=source,
    )

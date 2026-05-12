"""Cross-book price aggregation and market intelligence helpers."""
from __future__ import annotations

import statistics
from typing import Any

from quant_engine import american_to_decimal, book_hold_n_way, book_hold_two_way, implied_probability_from_american, no_vig_probabilities_n_way


def book_hold_from_american_pair(american_a: int | float, american_b: int | float) -> float:
    return book_hold_two_way(
        implied_probability_from_american(american_a),
        implied_probability_from_american(american_b),
    )


def book_hold_from_american_n_way(americans: list[int | float]) -> float:
    return book_hold_n_way([implied_probability_from_american(o) for o in americans])

SHARP_BOOK_KEYWORDS = ("pinnacle", "circa", "bookmaker", "betcris", "lowvig")


def best_price_american(odds_list: list[int | float]) -> Optional[int]:
    if not odds_list:
        return None
    best = None
    best_val = None
    for o in odds_list:
        dec = american_to_decimal(o)
        if best_val is None or dec > best_val:
            best_val = dec
            best = int(round(float(o)))
    return best


def worst_price_american(odds_list: list[int | float]) -> Optional[int]:
    if not odds_list:
        return None
    worst = None
    worst_val = None
    for o in odds_list:
        dec = american_to_decimal(o)
        if worst_val is None or dec < worst_val:
            worst_val = dec
            worst = int(round(float(o)))
    return worst


def average_implied_probability(odds_list: list[int | float]) -> float:
    if not odds_list:
        return 0.0
    return sum(implied_probability_from_american(o) for o in odds_list) / len(odds_list)


def median_implied_probability(odds_list: list[int | float]) -> float:
    if not odds_list:
        return 0.0
    imps = [implied_probability_from_american(o) for o in odds_list]
    return float(statistics.median(imps))


def market_spread_implied(odds_list: list[int | float]) -> float:
    """Difference between max and min implied probability across books."""
    if len(odds_list) < 2:
        return 0.0
    imps = [implied_probability_from_american(o) for o in odds_list]
    return max(imps) - min(imps)


def no_vig_consensus_probability(implied_probabilities: list[float]) -> list[float]:
    return no_vig_probabilities_n_way(implied_probabilities)


def sharp_book_consensus_probability(
    book_implied: list[tuple[str, float]],
) -> Optional[float]:
    """Average implied among books whose name matches sharp list (case-insensitive)."""
    sharp_imps = [
        imp for name, imp in book_implied if any(k in name.lower() for k in SHARP_BOOK_KEYWORDS)
    ]
    if not sharp_imps:
        return None
    return sum(sharp_imps) / len(sharp_imps)


def soft_book_stale_line_flag(
    opening_american: Optional[int],
    current_american: int,
    sharp_moved: bool,
    soft_moved: bool,
) -> bool:
    """Heuristic stale line: sharp moved materially but soft did not."""
    if opening_american is None:
        return False
    if not sharp_moved:
        return False
    return not soft_moved


def opening_vs_current_clv_implied_change_pct(
    opening_american: Optional[int],
    current_american: int,
) -> Optional[float]:
    if opening_american is None:
        return None
    o0 = implied_probability_from_american(opening_american)
    o1 = implied_probability_from_american(current_american)
    if o0 <= 0:
        return None
    return round((o1 - o0) / o0 * 100, 3)


def current_vs_projected_close_delta(
    current_implied: float,
    projected_close_implied: Optional[float],
) -> Optional[float]:
    if projected_close_implied is None:
        return None
    return round((current_implied - projected_close_implied) * 100, 3)


def closing_line_value_pct(
    bet_implied_at_bet: float,
    closing_implied: Optional[float],
) -> Optional[float]:
    """Positive CLV if closing line is sharper against the bettor's side (implied rose for underdog side)."""
    if closing_implied is None:
        return None
    return round((bet_implied_at_bet - closing_implied) * 100, 3)


def steam_move_detection(implied_series: list[float], threshold: float = 0.012) -> bool:
    """True if last move exceeds threshold in absolute single step."""
    if len(implied_series) < 2:
        return False
    return abs(implied_series[-1] - implied_series[-2]) >= threshold


def reverse_line_movement_flag(
    public_side_implied_dropped: bool,
    line_moved_toward_public: bool,
) -> bool:
    """RLM heuristic: line moves opposite to expected public flow."""
    return public_side_implied_dropped and line_moved_toward_public


def book_disagreement_score(implied_probabilities: list[float]) -> float:
    if len(implied_probabilities) < 2:
        return 0.0
    return max(implied_probabilities) - min(implied_probabilities)


def market_confidence_score(implied_probabilities: list[float]) -> float:
    """
    Higher when books agree (tight cluster). Scale 0-100.
    """
    if not implied_probabilities:
        return 0.0
    if len(implied_probabilities) == 1:
        return 80.0
    spread = book_disagreement_score(implied_probabilities)
    return max(0.0, min(100.0, 100.0 - spread * 400))

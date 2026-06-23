"""Cross-book price aggregation and market intelligence helpers."""
from __future__ import annotations

import statistics
from typing import Any, Optional

from src.core.clv import (
    closing_line_value_pct as _core_closing_line_value_pct,
    current_vs_projected_close_delta as _core_current_vs_projected_close_delta,
    opening_vs_current_clv_implied_change_pct as _core_opening_vs_current_clv_implied_change_pct,
    steam_move_from_implied_series,
)
from src.core.math_utils import (
    american_to_decimal,
    american_to_implied_probability as implied_probability_from_american,
    book_hold_n_way,
    book_hold_two_way,
    no_vig_probabilities_n_way,
    probability_to_fair_american,
)


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
    return _core_opening_vs_current_clv_implied_change_pct(opening_american, current_american)


def current_vs_projected_close_delta(
    current_implied: float,
    projected_close_implied: Optional[float],
) -> Optional[float]:
    return _core_current_vs_projected_close_delta(current_implied, projected_close_implied)


def closing_line_value_pct(
    bet_implied_at_bet: float,
    closing_implied: Optional[float],
) -> Optional[float]:
    """Positive CLV if closing line is sharper against the bettor's side (implied rose for underdog side)."""
    return _core_closing_line_value_pct(bet_implied_at_bet, closing_implied)


def steam_move_detection(implied_series: list[float], threshold: float = 0.012) -> bool:
    """True if last move exceeds threshold in absolute single step."""
    return steam_move_from_implied_series(implied_series, threshold)


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


def group_lines_by_market_point_selection(flat_odds: list[dict[str, Any]]) -> dict[tuple[str, Any, str], list[dict[str, Any]]]:
    """Group odds lines by market, point, and selection."""
    groups: dict[tuple[str, Any, str], list[dict[str, Any]]] = {}

    for line in flat_odds:
        if not isinstance(line, dict):
            continue

        market = str(line.get("market", "")).lower()
        selection = str(line.get("selection", "")).lower()
        point = line.get("point")

        # Normalize point for grouping
        if point is None:
            point_key = None
        else:
            point_key = float(point) if isinstance(point, (int, float)) else str(point)

        key = (market, point_key, selection)
        groups.setdefault(key, []).append(line)

    return groups


def calculate_market_group_statistics(group: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate statistics for a market group."""
    if not group:
        return {}

    # Extract American odds
    odds_list = []
    for line in group:
        odds = line.get("price_american")
        if odds is not None and isinstance(odds, (int, float)):
            odds_list.append(odds)

    if not odds_list:
        return {}

    # Calculate basic statistics
    best_price = best_price_american(odds_list)
    worst_price = worst_price_american(odds_list)
    avg_implied = average_implied_probability(odds_list)
    median_implied = median_implied_probability(odds_list)
    disagreement_score = book_disagreement_score([implied_probability_from_american(o) for o in odds_list])

    # Calculate book hold
    if len(odds_list) >= 2:
        book_hold = book_hold_from_american_n_way(odds_list)
    else:
        book_hold = 0.0

    # Calculate no-vig probabilities
    implied_probs = [implied_probability_from_american(o) for o in odds_list]
    no_vig_probs = no_vig_consensus_probability(implied_probs)

    # Calculate consensus probability (average of no-vig)
    consensus_prob = sum(no_vig_probs) / len(no_vig_probs) if no_vig_probs else avg_implied

    # Calculate fair American odds from consensus
    fair_odds = int(probability_to_fair_american(consensus_prob)) if consensus_prob > 0 and consensus_prob < 1 else None

    # Check for stale lines (flag if one book is far from consensus)
    stale_line_flag = False
    if len(odds_list) >= 3:
        for odds in odds_list:
            implied = implied_probability_from_american(odds)
            if abs(implied - consensus_prob) > 0.05:  # 5% deviation threshold
                stale_line_flag = True
                break

    return {
        "best_price": best_price,
        "worst_price": worst_price,
        "average_implied_probability": avg_implied,
        "median_implied_probability": median_implied,
        "book_disagreement_score": disagreement_score,
        "book_hold": book_hold,
        "no_vig_probabilities": no_vig_probs,
        "consensus_probability": consensus_prob,
        "fair_odds_american": fair_odds,
        "stale_line_flag": stale_line_flag,
        "sample_size": len(odds_list)
    }


def create_evaluation_ready_lines(
    flat_odds: list[dict[str, Any]],
    model_probabilities: Optional[dict[str, Any]] = None
) -> list[dict[str, Any]]:
    """Create evaluation-ready betting rows from flat odds."""
    groups = group_lines_by_market_point_selection(flat_odds)
    evaluation_lines: list[dict[str, Any]] = []

    for (market, point, selection), group in groups.items():
        # Calculate group statistics
        stats = calculate_market_group_statistics(group)
        if not stats:
            continue

        # Create evaluation line for each book in the group
        for line in group:
            try:
                odds_american = int(line["price_american"])
                implied_prob = implied_probability_from_american(odds_american)

                # Find corresponding no-vig probability
                implied_probs = [implied_probability_from_american(l["price_american"]) for l in group]
                no_vig_probs = no_vig_consensus_probability(implied_probs)

                # Get the no-vig probability for this selection
                selection_index = list(g[1] for g in groups.keys()).index(selection) if selection in list(g[1] for g in groups.keys()) else 0
                no_vig_prob = no_vig_probs[selection_index] if selection_index < len(no_vig_probs) else None

                # Create correlation group name
                event_id = line.get("event_id", "unknown")
                teams = f"{line.get('home_team', 'Team1')}_{line.get('away_team', 'Team2')}"
                point_str = f"_{point}" if point is not None else ""
                correlation_group = f"{teams}_{market}{point_str}"

                # Check for model probability
                model_prob = None
                if model_probabilities:
                    market_key = f"{market}_{point}" if point is not None else market
                    model_prob = model_probabilities.get(market_key, {}).get(selection)

                evaluation_line = {
                    "sportsbook": line.get("sportsbook", line.get("bookmaker_key", "unknown")),
                    "market": market,
                    "selection": line.get("selection", selection),
                    "line": point,
                    "odds_american": odds_american,
                    "implied_probability": round(implied_prob, 6),
                    "no_vig_probability": round(no_vig_prob, 6) if no_vig_prob is not None else None,
                    "consensus_probability": round(stats["consensus_probability"], 6),
                    "fair_odds_american": stats["fair_odds_american"],
                    "market_status": "market_priced_only" if model_prob is None else "model_enhanced",
                    "model_probability": round(model_prob, 6) if model_prob is not None else None,
                    "correlation_group": correlation_group,
                    "best_price_in_market": stats["best_price"],
                    "worst_price_in_market": stats["worst_price"],
                    "book_disagreement_score": stats["book_disagreement_score"],
                    "book_hold": stats["book_hold"],
                    "stale_line_flag": stats["stale_line_flag"]
                }

                evaluation_lines.append(evaluation_line)

            except Exception:
                # Skip invalid lines
                continue

    return evaluation_lines


def create_market_summary(evaluation_lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Create market summary from evaluation lines."""
    market_summary: dict[str, dict[str, Any]] = {}

    for line in evaluation_lines:
        market = line["market"]
        point = line["line"]
        key = f"{market}_{point}" if point is not None else market

        if key not in market_summary:
            market_summary[key] = {
                "market": market,
                "line": point,
                "selections": [],
                "best_prices": {},
                "worst_prices": {},
                "average_implied_probability": 0,
                "median_implied_probability": 0,
                "book_disagreement_score": 0,
                "book_hold": 0,
                "consensus_probability": 0,
                "sample_size": 0
            }

        summary = market_summary[key]

        # Add selection info
        selection_info = {
            "selection": line["selection"],
            "best_odds": line["best_price_in_market"],
            "worst_odds": line["worst_price_in_market"],
            "consensus_probability": line["consensus_probability"],
            "fair_odds": line["fair_odds_american"]
        }

        if selection_info not in summary["selections"]:
            summary["selections"].append(selection_info)

        # Update summary stats (use first line's group stats)
        if summary["sample_size"] == 0:
            summary.update({
                "average_implied_probability": line.get("average_implied_probability", 0),
                "median_implied_probability": line.get("median_implied_probability", 0),
                "book_disagreement_score": line.get("book_disagreement_score", 0),
                "book_hold": line.get("book_hold", 0),
                "consensus_probability": line["consensus_probability"],
                "sample_size": 1
            })

    return list(market_summary.values())

# Canonical compatibility imports
from src.core.pricing import *  # noqa: F401,F403

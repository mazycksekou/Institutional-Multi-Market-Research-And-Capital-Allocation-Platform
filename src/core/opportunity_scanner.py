"""Live market opportunity scanner.

The scanner consumes raw The Odds API event payloads and returns market-derived
opportunities. It does not place bets and does not claim independent model edge.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any

from src.core.math_utils import american_to_decimal, american_to_implied_probability


def _norm_line(market_key: str, outcome: dict[str, Any]) -> float | str | None:
    point = outcome.get("point")
    if point is None:
        return None
    try:
        point_value = float(point)
    except (TypeError, ValueError):
        return str(point)
    if market_key == "spreads":
        return abs(point_value)
    return point_value


def _best_price(offers: list[dict[str, Any]]) -> dict[str, Any]:
    return max(offers, key=lambda item: float(item["decimal_odds"]))


def _normalized_probabilities(prices: list[int | float]) -> list[float]:
    implied = [american_to_implied_probability(price) for price in prices]
    total = sum(implied)
    if total <= 0:
        return []
    return [value / total for value in implied]


def _arb_stakes(best_offers: list[dict[str, Any]], total_stake: float) -> dict[str, Any]:
    stake_value = max(0.0, float(total_stake))
    inv_sum = sum(1.0 / offer["decimal_odds"] for offer in best_offers)
    if inv_sum <= 0 or stake_value <= 0:
        return {"total_stake": stake_value, "stake_split": []}

    payout = stake_value / inv_sum
    rows = []
    for offer in best_offers:
        stake = (stake_value * (1.0 / offer["decimal_odds"])) / inv_sum
        rows.append({
            "selection": offer["selection"],
            "book": offer["book"],
            "odds": offer["price"],
            "stake": round(stake, 2),
            "payout": round(stake * offer["decimal_odds"], 2),
        })

    return {
        "total_stake": round(stake_value, 2),
        "guaranteed_payout": round(payout, 2),
        "guaranteed_profit": round(payout - stake_value, 2),
        "guaranteed_roi_percent": round((payout / stake_value - 1.0) * 100.0, 3),
        "stake_split": rows,
    }


def scan_opportunities(
    events: list[dict[str, Any]],
    stake: float = 100.0,
    min_edge: float = 0.0,
    *,
    near_arb_max_hold_percent: float = 1.25,
    middle_min_width: float = 0.5,
) -> dict[str, Any]:
    """Scan raw odds events for arbitrage, middles, line shopping, and low holds."""
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    all_offers: list[dict[str, Any]] = []
    book_holds: list[dict[str, Any]] = []

    for event in events or []:
        event_id = event.get("id")
        home = event.get("home_team")
        away = event.get("away_team")
        event_name = f"{away} vs {home}"

        for book in event.get("bookmakers") or []:
            book_name = book.get("title") or book.get("key")
            last_update = book.get("last_update")

            for market in book.get("markets") or []:
                market_key = market.get("key")
                outcomes = [outcome for outcome in market.get("outcomes") or [] if outcome.get("price") is not None]
                if len(outcomes) < 2:
                    continue

                try:
                    raw_probs = [american_to_implied_probability(outcome["price"]) for outcome in outcomes]
                except Exception:
                    continue

                total_raw_prob = sum(raw_probs)
                if total_raw_prob <= 0:
                    continue

                line_for_hold = None
                if market_key in {"spreads", "totals"}:
                    line_for_hold = _norm_line(str(market_key), outcomes[0])

                book_holds.append({
                    "event": event_name,
                    "market": market_key,
                    "line": line_for_hold,
                    "book": book_name,
                    "hold_percent": round((total_raw_prob - 1.0) * 100.0, 3),
                    "raw_probability_sum_percent": round(total_raw_prob * 100.0, 3),
                })

                for outcome, implied in zip(outcomes, raw_probs):
                    price = outcome.get("price")
                    point = outcome.get("point")
                    line_key = _norm_line(str(market_key), outcome)
                    try:
                        decimal_odds = american_to_decimal(price)
                    except Exception:
                        continue

                    offer = {
                        "event_id": event_id,
                        "event": event_name,
                        "home_team": home,
                        "away_team": away,
                        "market": market_key,
                        "selection": outcome.get("name"),
                        "line": line_key,
                        "point": point,
                        "book": book_name,
                        "price": price,
                        "decimal_odds": decimal_odds,
                        "implied_probability": implied,
                        "book_no_vig_probability": implied / total_raw_prob,
                        "last_update": last_update,
                    }
                    groups.setdefault((event_id, event_name, market_key, line_key), []).append(offer)
                    all_offers.append(offer)

    arbs: list[dict[str, Any]] = []
    near_arbs: list[dict[str, Any]] = []
    value_watch: list[dict[str, Any]] = []
    best_prices: list[dict[str, Any]] = []
    disagreement: list[dict[str, Any]] = []

    min_edge_percent = float(min_edge) * 100.0 if abs(float(min_edge)) <= 1.0 else float(min_edge)

    for group_key, offers in groups.items():
        _event_id, event_name, market_key, line_key = group_key
        by_selection: dict[str, list[dict[str, Any]]] = {}
        for offer in offers:
            by_selection.setdefault(str(offer["selection"]), []).append(offer)

        if len(by_selection) < 2:
            continue

        best_offers = [_best_price(selection_offers) for selection_offers in by_selection.values()]
        implied_sum = sum(1.0 / offer["decimal_odds"] for offer in best_offers)
        hold_percent = (implied_sum - 1.0) * 100.0
        selection_implied_ranges = []

        for selection, selection_offers in by_selection.items():
            best = _best_price(selection_offers)
            no_vig_values = [
                offer["book_no_vig_probability"]
                for offer in selection_offers
                if offer.get("book_no_vig_probability") is not None
            ]
            consensus_true = sum(no_vig_values) / len(no_vig_values) if no_vig_values else None
            best_implied = american_to_implied_probability(best["price"])
            edge = (consensus_true - best_implied) if consensus_true is not None else 0.0
            implied_values = [offer["implied_probability"] for offer in selection_offers]
            selection_implied_ranges.append(max(implied_values) - min(implied_values))

            best_prices.append({
                "event": event_name,
                "market": market_key,
                "selection": selection,
                "line": line_key,
                "best_book": best["book"],
                "best_odds": best["price"],
                "implied_probability_percent": round(best_implied * 100.0, 3),
                "market_true_no_vig_percent": round(consensus_true * 100.0, 3) if consensus_true is not None else None,
                "market_edge_percent": round(edge * 100.0, 3),
                "book_count": len(selection_offers),
            })

            if edge * 100.0 >= min_edge_percent:
                value_watch.append({
                    "type": "market_derived_value_watch",
                    "event": event_name,
                    "market": market_key,
                    "selection": selection,
                    "line": line_key,
                    "best_book": best["book"],
                    "best_odds": best["price"],
                    "implied_probability_percent": round(best_implied * 100.0, 3),
                    "market_true_no_vig_percent": round(consensus_true * 100.0, 3) if consensus_true is not None else None,
                    "edge_percent": round(edge * 100.0, 3),
                    "note": "Market-derived edge only. Not independent model-confirmed.",
                })

        if selection_implied_ranges:
            disagreement.append({
                "event": event_name,
                "market": market_key,
                "line": line_key,
                "max_book_disagreement_percent": round(max(selection_implied_ranges) * 100.0, 3),
                "selection_count": len(by_selection),
                "offer_count": len(offers),
            })

        if implied_sum < 1.0:
            arbs.append({
                "type": "arbitrage",
                "event": event_name,
                "market": market_key,
                "line": line_key,
                "combined_implied_percent": round(implied_sum * 100.0, 3),
                "arb_profit_percent": round((1.0 / implied_sum - 1.0) * 100.0, 3),
                "books": [
                    {"selection": offer["selection"], "book": offer["book"], "odds": offer["price"]}
                    for offer in best_offers
                ],
                "stake_plan": _arb_stakes(best_offers, stake),
            })
        elif hold_percent <= near_arb_max_hold_percent:
            near_arbs.append({
                "type": "near_arb_or_scalp_watch",
                "event": event_name,
                "market": market_key,
                "line": line_key,
                "combined_implied_percent": round(implied_sum * 100.0, 3),
                "remaining_hold_percent": round(hold_percent, 3),
                "books": [
                    {"selection": offer["selection"], "book": offer["book"], "odds": offer["price"]}
                    for offer in best_offers
                ],
                "note": "Not risk-free. Close to arb, useful for line shopping or price movement watch.",
            })

    spread_middles: list[dict[str, Any]] = []
    total_middles: list[dict[str, Any]] = []
    offers_by_event: dict[Any, list[dict[str, Any]]] = {}
    for offer in all_offers:
        offers_by_event.setdefault(offer["event_id"], []).append(offer)

    for offers in offers_by_event.values():
        spreads = [offer for offer in offers if offer["market"] == "spreads" and offer["point"] is not None]
        totals = [offer for offer in offers if offer["market"] == "totals" and offer["point"] is not None]

        for left, right in combinations(spreads, 2):
            if left["selection"] == right["selection"]:
                continue
            try:
                left_point = float(left["point"])
                right_point = float(right["point"])
            except (TypeError, ValueError):
                continue
            middle_width = left_point + right_point
            if middle_width >= middle_min_width:
                combined_implied = left["implied_probability"] + right["implied_probability"]
                spread_middles.append({
                    "type": "spread_middle_watch",
                    "event": left["event"],
                    "side_1": {
                        "selection": left["selection"],
                        "point": left["point"],
                        "book": left["book"],
                        "odds": left["price"],
                    },
                    "side_2": {
                        "selection": right["selection"],
                        "point": right["point"],
                        "book": right["book"],
                        "odds": right["price"],
                    },
                    "middle_width_points": round(middle_width, 3),
                    "combined_implied_percent": round(combined_implied * 100.0, 3),
                    "note": "Middle, not guaranteed arb. Both bets can win if final margin lands inside the window.",
                })

        overs = [offer for offer in totals if str(offer["selection"]).lower() == "over"]
        unders = [offer for offer in totals if str(offer["selection"]).lower() == "under"]
        for over in overs:
            for under in unders:
                try:
                    over_line = float(over["point"])
                    under_line = float(under["point"])
                except (TypeError, ValueError):
                    continue
                if under_line - over_line >= middle_min_width:
                    combined_implied = over["implied_probability"] + under["implied_probability"]
                    total_middles.append({
                        "type": "total_middle_watch",
                        "event": over["event"],
                        "over": {"line": over_line, "book": over["book"], "odds": over["price"]},
                        "under": {"line": under_line, "book": under["book"], "odds": under["price"]},
                        "middle_width_points": round(under_line - over_line, 3),
                        "combined_implied_percent": round(combined_implied * 100.0, 3),
                        "note": "Middle, not guaranteed arb. Over lower number and under higher number can both win.",
                    })

    book_holds_sorted = sorted(book_holds, key=lambda item: item["hold_percent"])
    best_prices_sorted = sorted(best_prices, key=lambda item: item["market_edge_percent"], reverse=True)
    value_watch_sorted = sorted(value_watch, key=lambda item: item["edge_percent"], reverse=True)
    arbs_sorted = sorted(arbs, key=lambda item: item["arb_profit_percent"], reverse=True)
    near_arbs_sorted = sorted(near_arbs, key=lambda item: item["remaining_hold_percent"])
    spread_middles_sorted = sorted(spread_middles, key=lambda item: item["middle_width_points"], reverse=True)
    total_middles_sorted = sorted(total_middles, key=lambda item: item["middle_width_points"], reverse=True)
    disagreement_sorted = sorted(disagreement, key=lambda item: item["max_book_disagreement_percent"], reverse=True)

    return {
        "offers_checked": len(all_offers),
        "checks_included": [
            "arbitrage",
            "near-arb/scalp watch",
            "spread middles",
            "total middles",
            "best-line shopping",
            "market-derived no-vig edge",
            "low-hold book markets",
            "book disagreement",
        ],
        "summary": {
            "arbs_found": len(arbs_sorted),
            "near_arbs_found": len(near_arbs_sorted),
            "spread_middles_found": len(spread_middles_sorted),
            "total_middles_found": len(total_middles_sorted),
            "value_watch_count": len(value_watch_sorted),
            "book_disagreement_count": len(disagreement_sorted),
        },
        "arbitrage": arbs_sorted[:25],
        "near_arbs": near_arbs_sorted[:25],
        "spread_middles": spread_middles_sorted[:25],
        "total_middles": total_middles_sorted[:25],
        "value_watch": value_watch_sorted[:25],
        "best_prices": best_prices_sorted[:50],
        "lowest_hold_markets": book_holds_sorted[:50],
        "book_disagreement": disagreement_sorted[:50],
        "important_note": (
            "Arbs are risk-free only if all legs can be placed at the listed odds before line movement. "
            "Middles and value-watch plays are not guaranteed profit."
        ),
    }

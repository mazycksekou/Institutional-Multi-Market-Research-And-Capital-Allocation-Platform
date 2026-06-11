"""Live market opportunity scanner.

The scanner consumes raw The Odds API event payloads and returns market-derived
opportunities. It does not place bets and does not claim independent model edge.
"""
from __future__ import annotations

from itertools import combinations
import math
from typing import Any

from src.core.math_utils import american_to_decimal, american_to_implied_probability


def offer_set_is_stale(offers: list[dict[str, Any]], max_timestamp_skew_seconds: int) -> bool:
    timestamps = [int(offer.get("timestamp")) for offer in offers if isinstance(offer.get("timestamp"), (int, float))]
    if not timestamps:
        return False
    return (max(timestamps) - min(timestamps)) > max_timestamp_skew_seconds


def best_arbitrage_prices_by_selection(offers: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    for offer in offers:
        if offer.get("odds") in (None, 0):
            continue
        selection = str(offer.get("selection"))
        decimal_price = american_to_decimal(offer["odds"])
        existing = best.get(selection)
        if existing is None or decimal_price > existing["decimal_odds"]:
            best[selection] = {**offer, "decimal_odds": decimal_price}
    return best


def arbitrage_stake_split(best_prices: list[dict[str, Any]], total_stake: float) -> tuple[list[dict[str, Any]], float]:
    implied_sum = sum(1.0 / price["decimal_odds"] for price in best_prices)
    plan = []
    for price in best_prices:
        stake = total_stake * ((1.0 / price["decimal_odds"]) / implied_sum)
        plan.append({**price, "stake": round(stake, 2), "payout": round(stake * price["decimal_odds"], 2)})
    return plan, implied_sum


def detect_arbitrage_from_normalized_offers(
    offers: list[dict[str, Any]],
    *,
    total_stake: float = 100.0,
    market_identity_confidence: float = 100.0,
    max_timestamp_skew_seconds: int = 120,
    stale_data_risk: bool = False,
) -> dict[str, Any]:
    if len(offers) < 2:
        return {"candidate_found": False, "reason": "not_enough_offers", "candidate_type": None}
    if stale_data_risk or offer_set_is_stale(offers, max_timestamp_skew_seconds):
        return {"candidate_found": False, "reason": "stale_data", "candidate_type": None}
    if market_identity_confidence < 85:
        return {"candidate_found": False, "reason": "low_market_identity_confidence", "candidate_type": None}

    best_by_selection = best_arbitrage_prices_by_selection(offers)
    if len(best_by_selection) < 2:
        return {"candidate_found": False, "reason": "same_side_only", "candidate_type": None}
    if len(best_by_selection) not in {2, 3}:
        return {"candidate_found": False, "reason": "unsupported_selection_count", "candidate_type": None}

    implied_sum = sum(1.0 / row["decimal_odds"] for row in best_by_selection.values())
    if implied_sum >= 1.0:
        return {
            "candidate_found": False,
            "reason": "no_arbitrage_after_vig",
            "candidate_type": None,
            "arbitrage_implied_sum": round(implied_sum, 6),
        }

    stake_plan = []
    payouts = []
    for selection, row in best_by_selection.items():
        stake = total_stake * ((1.0 / row["decimal_odds"]) / implied_sum)
        payout = stake * row["decimal_odds"]
        payouts.append(payout)
        stake_plan.append(
            {
                "selection": selection,
                "bookmaker": row["bookmaker"],
                "odds": row["odds"],
                "decimal_odds": round(row["decimal_odds"], 6),
                "stake": round(stake, 2),
                "payout": round(payout, 2),
            }
        )

    total_stake_value = round(sum(item["stake"] for item in stake_plan), 2)
    profits = [round(payout - total_stake_value, 2) for payout in payouts]
    min_profit = min(profits)
    max_profit = max(profits)
    return {
        "candidate_found": True,
        "candidate_type": "arbitrage_candidate",
        "books_compared": len({item["bookmaker"] for item in stake_plan}),
        "arbitrage_implied_sum": round(implied_sum, 6),
        "stake_plan": stake_plan,
        "total_stake": total_stake_value,
        "min_profit": min_profit,
        "max_profit": max_profit,
        "estimated_roi_percent": round((min_profit / total_stake_value) * 100.0, 4),
        "line_match_confidence": round(float(market_identity_confidence), 2),
        "stale_data_risk": False,
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "auto_bet_enabled": False,
        "auto_trade_enabled": False,
        "user_facing_label": "arbitrage_candidate",
    }


def detect_n_way_arbitrage_from_normalized_offers(
    offers: list[dict[str, Any]],
    *,
    expected_selection_count: int,
    total_stake: float = 100.0,
    market_identity_confidence: float = 100.0,
    confidence_field: str = "market_identity_confidence",
) -> dict[str, Any]:
    if len(offers) != expected_selection_count:
        return {"candidate_found": False, "reason": f"{expected_selection_count}_way_requires_{expected_selection_count}_offers"}
    if market_identity_confidence < 85:
        return {"candidate_found": False, "reason": "low_market_identity_confidence"}
    best_prices = [{**offer, "decimal_odds": american_to_decimal(offer["odds"])} for offer in offers]
    stake_plan, implied_sum = arbitrage_stake_split(best_prices, total_stake)
    if implied_sum >= 1:
        return {"candidate_found": False, "reason": "no_arbitrage_after_vig", "arbitrage_implied_sum": round(implied_sum, 6)}
    total = round(sum(item["stake"] for item in stake_plan), 2)
    profits = [round(item["payout"] - total, 2) for item in stake_plan]
    result = {
        "candidate_found": True,
        "candidate_type": "arbitrage_candidate",
        "stake_plan": stake_plan,
        "arbitrage_implied_sum": round(implied_sum, 6),
        "estimated_roi_percent": round((min(profits) / total) * 100.0, 4),
        "max_gain": max(profits),
        "max_loss": 0.0,
    }
    if expected_selection_count == 2:
        result[confidence_field] = round(float(market_identity_confidence), 2)
    return result


def normal_probability_between(low: float, high: float, mean: float, std_dev: float) -> float:
    if std_dev <= 0:
        return 0.0
    z_low = (low - mean) / (std_dev * math.sqrt(2))
    z_high = (high - mean) / (std_dev * math.sqrt(2))
    return max(0.0, min(1.0, (math.erf(z_high) - math.erf(z_low)) / 2))


def detect_middle_from_normalized_offers(
    left: dict[str, Any],
    right: dict[str, Any],
    *,
    market: str,
    confidence: float,
    stake_per_side: float = 100.0,
    model_distribution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    left_line = float(left.get("line") or 0)
    right_line = float(right.get("line") or 0)
    left_decimal = american_to_decimal(left["odds"])
    right_decimal = american_to_decimal(right["odds"])
    left_profit = stake_per_side * (left_decimal - 1)
    right_profit = stake_per_side * (right_decimal - 1)
    max_loss = round(stake_per_side * 2 - min(left_profit, right_profit), 2)
    non_middle_profit = min(left_profit - stake_per_side, right_profit - stake_per_side)

    left_selection = str(left.get("selection") or "").lower()
    right_selection = str(right.get("selection") or "").lower()
    if market == "total":
        over_line = left_line if left_selection == "over" else right_line
        under_line = left_line if left_selection == "under" else right_line
        middle_width = round(under_line - over_line, 4)
        middle_zone = [round(over_line, 4), round(under_line, 4)]
    else:
        favorite_line = left_line if left_line < right_line else right_line
        dog_line = right_line if favorite_line == left_line else left_line
        middle_width = round(dog_line - favorite_line, 4)
        middle_zone = [round(abs(favorite_line), 4), round(abs(dog_line), 4)]

    if middle_width <= 0:
        return {"candidate_found": False, "reason": "watch_recheck_no_corridor"}

    middle_hit_probability = float(
        (model_distribution or {}).get("middle_hit_probability")
        or normal_probability_between(
            middle_zone[0],
            middle_zone[1],
            float((model_distribution or {}).get("mean", sum(middle_zone) / 2.0)),
            float((model_distribution or {}).get("std_dev", max(1.0, middle_width))),
        )
    )
    middle_win = round(left_profit + right_profit, 2)
    break_even_probability = round(max_loss / (middle_win + max_loss), 6) if (middle_win + max_loss) > 0 else 1.0
    expected_value = round((middle_hit_probability * middle_win) + ((1 - middle_hit_probability) * non_middle_profit), 4)
    risk_acceptable = middle_hit_probability >= break_even_probability
    if expected_value <= 0 and not risk_acceptable:
        return {
            "candidate_found": False,
            "reason": "negative_middle_ev",
            "middle_width": middle_width,
            "break_even_probability": break_even_probability,
        }

    return {
        "candidate_found": True,
        "candidate_type": "middle_candidate",
        "market": market,
        "middle_zone": middle_zone,
        "middle_width": middle_width,
        "middle_hit_probability": round(middle_hit_probability, 6),
        "break_even_probability": break_even_probability,
        "expected_value": expected_value,
        "estimated_roi_percent": round((expected_value / (stake_per_side * 2)) * 100.0, 4),
        "max_loss": round(max_loss, 2),
        "max_gain": middle_win,
        "line_match_confidence": round(float(confidence), 2),
        "stale_data_risk": False,
        "stake_plan": [
            {"bookmaker": left["bookmaker"], "selection": left["selection"], "line": left_line, "stake": round(stake_per_side, 2)},
            {"bookmaker": right["bookmaker"], "selection": right["selection"], "line": right_line, "stake": round(stake_per_side, 2)},
        ],
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "auto_bet_enabled": False,
        "auto_trade_enabled": False,
    }


def simulate_middle_ev_from_prices(
    *,
    left_odds_american: Any,
    right_odds_american: Any,
    middle_hit_probability: float,
    stake_per_side: float = 100.0,
) -> dict[str, Any]:
    left_decimal = american_to_decimal(left_odds_american)
    right_decimal = american_to_decimal(right_odds_american)
    left_win = stake_per_side * (left_decimal - 1)
    right_win = stake_per_side * (right_decimal - 1)
    max_gain = round(left_win + right_win, 2)
    non_middle_profit = round(min(left_win - stake_per_side, right_win - stake_per_side), 2)
    max_loss = abs(non_middle_profit)
    break_even_probability = round(max_loss / (max_gain + max_loss), 6) if (max_gain + max_loss) > 0 else 1.0
    estimated_ev = round((middle_hit_probability * max_gain) + ((1 - middle_hit_probability) * non_middle_profit), 4)
    return {
        "max_gain": max_gain,
        "max_loss": round(max_loss, 2),
        "break_even_probability": break_even_probability,
        "estimated_ev": estimated_ev,
        "estimated_roi_percent": round((estimated_ev / (stake_per_side * 2)) * 100.0, 4),
    }


def detect_exchange_back_lay_arbitrage_from_prices(
    *,
    back_odds_american: Any,
    lay_decimal_odds: Any,
    total_stake: float = 100.0,
) -> dict[str, Any]:
    back_decimal = american_to_decimal(back_odds_american)
    lay_decimal = float(lay_decimal_odds)
    if lay_decimal <= 1:
        return {"candidate_found": False, "reason": "invalid_lay_odds"}
    back_stake = float(total_stake)
    lay_stake = (back_stake * back_decimal) / lay_decimal
    back_profit = back_stake * (back_decimal - 1)
    lay_liability = lay_stake * (lay_decimal - 1)
    outcome_a = round(back_profit - lay_liability, 2)
    outcome_b = round(lay_stake - back_stake, 2)
    if min(outcome_a, outcome_b) <= 0:
        return {"candidate_found": False, "reason": "no_exchange_arbitrage"}
    return {
        "candidate_found": True,
        "candidate_type": "arbitrage_candidate",
        "stake_plan": [
            {"side": "back", "stake": round(back_stake, 2), "odds": back_odds_american},
            {"side": "lay", "stake": round(lay_stake, 2), "odds": round(lay_decimal, 4)},
        ],
        "max_gain": max(outcome_a, outcome_b),
        "max_loss": 0.0,
        "estimated_roi_percent": round((min(outcome_a, outcome_b) / back_stake) * 100.0, 4),
    }


def detect_prediction_market_vs_sportsbook_arbitrage_from_prices(
    *,
    sportsbook_odds_american: Any,
    prediction_market_yes_price: Any,
    total_stake: float = 100.0,
) -> dict[str, Any]:
    sportsbook_prob = american_to_implied_probability(sportsbook_odds_american)
    prediction_prob = float(prediction_market_yes_price)
    if prediction_prob > 1:
        prediction_prob /= 100.0
    if prediction_prob < 0 or prediction_prob > 1:
        raise ValueError("prediction_market_yes_price must be between 0 and 1")
    implied_sum = sportsbook_prob + prediction_prob
    if implied_sum >= 1:
        return {"candidate_found": False, "reason": "no_prediction_market_arbitrage", "arbitrage_implied_sum": round(implied_sum, 6)}
    sportsbook_stake = total_stake * (sportsbook_prob / implied_sum)
    prediction_stake = total_stake * (prediction_prob / implied_sum)
    return {
        "candidate_found": True,
        "candidate_type": "arbitrage_candidate",
        "arbitrage_implied_sum": round(implied_sum, 6),
        "stake_plan": [
            {"side": "sportsbook", "stake": round(sportsbook_stake, 2), "odds": sportsbook_odds_american},
            {"side": "prediction_market", "stake": round(prediction_stake, 2), "price": prediction_market_yes_price},
        ],
        "max_gain": round(total_stake * ((1 - implied_sum) / implied_sum), 2),
        "max_loss": 0.0,
        "estimated_roi_percent": round(((1 - implied_sum) / implied_sum) * 100.0, 4),
    }


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

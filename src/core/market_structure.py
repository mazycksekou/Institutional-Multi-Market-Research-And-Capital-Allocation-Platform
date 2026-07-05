from __future__ import annotations

from typing import Any

from src.providers.kalshi_scoring import evaluate_kalshi_liquidity_policy


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _spread(bid: float | None, ask: float | None) -> float | None:
    if bid is None or ask is None:
        return None
    return max(0.0, ask - bid)


def kalshi_market_structure_signals(current: dict[str, Any], previous: dict[str, Any] | None = None) -> dict[str, Any]:
    previous = previous or {}
    yes_bid = _to_float(current.get("yes_bid"))
    yes_ask = _to_float(current.get("yes_ask"))
    spread = _spread(yes_bid, yes_ask)
    midpoint = None
    if yes_bid is not None and yes_ask is not None:
        midpoint = (yes_bid + yes_ask) / 2.0

    prev_prob = _to_float(previous.get("implied_probability"))
    cur_prob = _to_float(current.get("implied_probability"))
    probability_velocity = None
    if prev_prob is not None and cur_prob is not None:
        probability_velocity = cur_prob - prev_prob

    prev_volume = _to_float(previous.get("volume")) or 0.0
    cur_volume = _to_float(current.get("volume")) or 0.0
    prev_oi = _to_float(previous.get("open_interest")) or 0.0
    cur_oi = _to_float(current.get("open_interest")) or 0.0
    prev_liq = _to_float(previous.get("liquidity_score")) or 0.0
    policy = evaluate_kalshi_liquidity_policy(current)
    cur_liq = float(policy["liquidity_score"])

    low_liquidity_signal = bool(policy["low_liquidity_flag"])
    return {
        "bid_ask_spread": spread,
        "spread_percent": None if spread is None else round(spread * 100.0, 6),
        "midpoint": midpoint,
        "probability_velocity": probability_velocity,
        "volume_change": cur_volume - prev_volume,
        "open_interest_change": cur_oi - prev_oi,
        "liquidity_change": cur_liq - prev_liq,
        "stale_market_signal": bool(current.get("stale_market")),
        "low_liquidity_signal": low_liquidity_signal,
        "missing_liquidity_signal": bool(policy["missing_liquidity_flag"]),
        "liquidity_tier": policy["liquidity_tier"],
        "status_change_signal": bool(str(current.get("status") or "") != str(previous.get("status") or "")),
    }


def sportsbook_market_structure_signals(current: dict[str, Any], previous: dict[str, Any] | None = None) -> dict[str, Any]:
    previous = previous or {}
    cur_odds = _to_float(current.get("odds"))
    prev_odds = _to_float(previous.get("odds"))
    price_velocity = None
    if cur_odds is not None and prev_odds is not None:
        price_velocity = cur_odds - prev_odds
    book_disagreement = _to_float(current.get("book_disagreement_score")) or 0.0
    line_movement = (_to_float(current.get("line")) or 0.0) - (_to_float(previous.get("line")) or 0.0)
    return {
        "book_disagreement": book_disagreement,
        "line_movement": line_movement,
        "price_velocity": price_velocity,
        "stale_book_signal": bool(current.get("stale_data_risk")),
        "reverse_line_movement": None,
    }

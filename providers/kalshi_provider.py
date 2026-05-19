from __future__ import annotations

import os
from typing import Any

import requests

from .base_provider import available, provider_error, unavailable


def _prob(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number > 1:
        number = number / 100
    return max(0.0, min(1.0, number))


def normalize_kalshi_probability_market(market: dict[str, Any]) -> dict[str, Any]:
    yes_bid = _prob(market.get("yes_bid"))
    yes_ask = _prob(market.get("yes_ask"))
    no_bid = _prob(market.get("no_bid"))
    no_ask = _prob(market.get("no_ask"))
    mid_probability = None
    if yes_bid is not None and yes_ask is not None:
        mid_probability = (yes_bid + yes_ask) / 2
    elif yes_ask is not None:
        mid_probability = yes_ask
    elif yes_bid is not None:
        mid_probability = yes_bid
    return {
        "provider": "kalshi",
        "provider_type": "prediction_market",
        "market_type": "kalshi_prediction_market",
        "ticker": market.get("ticker") or market.get("market_ticker"),
        "event_ticker": market.get("event_ticker"),
        "title": market.get("title"),
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "no_bid": no_bid,
        "no_ask": no_ask,
        "mid_probability": mid_probability,
        "liquidity": market.get("liquidity"),
        "volume": market.get("volume"),
        "raw": market,
    }


def enrich_with_kalshi(ticket: dict[str, Any]) -> dict[str, Any]:
    if os.getenv("KALSHI_ENABLED", "").strip().lower() not in {"1", "true", "yes", "on"}:
        return unavailable("kalshi")
    base_url = os.getenv("KALSHI_BASE_URL", "").strip().rstrip("/")
    if not base_url:
        return unavailable("kalshi")

    query = ticket.get("event") or " ".join(x for x in (ticket.get("league"), ticket.get("selection")) if x)
    try:
        response = requests.get(
            f"{base_url}/markets",
            params={"query": query, "limit": 10},
            timeout=8,
        )
        response.raise_for_status()
        raw = response.json()
    except Exception as exc:
        return provider_error(
            "kalshi",
            f"Kalshi API call failed: {type(exc).__name__}",
            ["Kalshi provider failed but analysis continued"],
        )

    markets = raw.get("markets") if isinstance(raw, dict) else raw
    if not isinstance(markets, list):
        markets = []
    normalized = [normalize_kalshi_probability_market(m) for m in markets if isinstance(m, dict)]
    return available("kalshi", normalized, source="kalshi")

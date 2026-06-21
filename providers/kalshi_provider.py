from __future__ import annotations

import os
from typing import Any

import requests

from src.providers.compat import available, provider_error, unavailable
from src.providers.prediction_markets.adapters import normalize_prediction_market_quote as _normalize_prediction_market_quote


def normalize_kalshi_probability_market(market: dict[str, Any]) -> dict[str, Any]:
    return _normalize_prediction_market_quote(market, provider="kalshi", market_type="kalshi_prediction_market")


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

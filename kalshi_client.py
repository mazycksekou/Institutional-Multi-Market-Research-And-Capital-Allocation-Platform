import os
import time
from typing import Any

import requests

KALSHI_BASE_URL = os.getenv(
    "KALSHI_BASE_URL",
    "https://external-api.kalshi.com/trade-api/v2"
).rstrip("/")
REQUEST_TIMEOUT = 8


_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}


def _json_response(response: requests.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError:
        data = {"text": response.text}

    result = {
        "ok": response.ok,
        "status_code": response.status_code,
        "url": response.url,
        "data": data if response.ok else None,
        "raw_response": data,
        "error_type": None,
        "error": None,
    }

    if response.status_code == 429:
        result.update({
            "ok": False,
            "message": "Provider rate limit reached",
            "error_type": "RateLimitError",
            "error": "Kalshi returned HTTP 429",
        })
    elif not response.ok:
        result.update({
            "ok": False,
            "message": f"Kalshi returned HTTP {response.status_code}",
            "error_type": "HTTPError",
            "error": str(data),
        })

    return result


def _get(path: str) -> dict[str, Any]:
    url = f"{KALSHI_BASE_URL}{path}"

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        return _json_response(response)
    except Exception as error:
        return {
            "ok": False,
            "status_code": None,
            "url": url,
            "data": None,
            "raw_response": None,
            "error_type": type(error).__name__,
            "error": str(error),
        }


def get_kalshi_market(ticker: str) -> dict[str, Any]:
    return _get(f"/markets/{ticker}")


def get_kalshi_orderbook(ticker: str) -> dict[str, Any]:
    return _get(f"/markets/{ticker}/orderbook")


def _extract_price(value: Any) -> float | int | None:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return value

    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None

    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, (list, tuple)) and first:
            return _extract_price(first[0])
        return _extract_price(first)

    if isinstance(value, dict):
        for key in ("price", "bid", "ask", "yes_bid", "yes_ask", "no_bid", "no_ask"):
            if key in value:
                return _extract_price(value.get(key))

    return None


def _extract_prices(orderbook_payload: Any) -> dict[str, float | int | None]:
    source = orderbook_payload
    if isinstance(source, dict):
        source = (
            source.get("orderbook")
            or source.get("orderbook_fp")
            or source.get("data")
            or source
        )

    prices = {
        "yes_bid": None,
        "yes_ask": None,
        "no_bid": None,
        "no_ask": None,
    }

    if not isinstance(source, dict):
        return prices

    prices["yes_bid"] = (
        _extract_price(source.get("yes_bid"))
        or _extract_price(source.get("yes"))
        or _extract_price(source.get("yes_dollars"))
        or _extract_price(source.get("bids"))
    )
    prices["yes_ask"] = (
        _extract_price(source.get("yes_ask"))
        or _extract_price(source.get("asks"))
    )
    prices["no_bid"] = (
        _extract_price(source.get("no_bid"))
        or _extract_price(source.get("no"))
        or _extract_price(source.get("no_dollars"))
    )
    prices["no_ask"] = _extract_price(source.get("no_ask"))

    return prices


def get_kalshi_market_snapshot(ticker: str) -> dict[str, Any]:
    cache_key = f"snapshot:{ticker}"
    cached = _CACHE.get(cache_key)
    if cached and time.time() - cached[0] < 15:
        return cached[1]

    market_response = get_kalshi_market(ticker)
    orderbook_response = get_kalshi_orderbook(ticker)

    prices = _extract_prices(orderbook_response.get("raw_response"))
    has_actual_odds = any(value is not None for value in prices.values())
    has_market_data = bool(market_response.get("data") or market_response.get("raw_response"))

    result = {
        "ok": bool(has_actual_odds or has_market_data),
        "provider": "kalshi",
        "lookup_id": ticker,
        "ticker": ticker,
        "result_type": "kalshi_market_snapshot",
        "has_actual_odds": has_actual_odds,
        "yes_bid": prices["yes_bid"],
        "yes_ask": prices["yes_ask"],
        "no_bid": prices["no_bid"],
        "no_ask": prices["no_ask"],
        "market": market_response.get("data") or market_response.get("raw_response"),
        "orderbook": orderbook_response.get("data") or orderbook_response.get("raw_response"),
        "odds": None,
        "raw_response": {
            "market": market_response,
            "orderbook": orderbook_response,
        },
        "message": (
            "Kalshi market and orderbook prices found."
            if has_actual_odds
            else "Market found, but no active orderbook prices were returned."
        ),
        "error_type": None if has_market_data or has_actual_odds else "NoData",
        "error": None if has_market_data or has_actual_odds else "No Kalshi market or orderbook data found.",
    }

    _CACHE[cache_key] = (time.time(), result)
    return result

from typing import Any

from src.core.math_utils import (
    american_to_decimal as _core_american_to_decimal,
    american_to_implied_probability as _core_american_to_implied_probability,
)


def american_to_decimal(odds: int | float) -> float:
    return _core_american_to_decimal(odds)


def implied_probability_from_american(odds: int | float) -> float:
    return _core_american_to_implied_probability(odds)


def normalize_sportsbook_event(provider: str, event: dict[str, Any], league: str | None = None) -> dict[str, Any]:
    return {
        "provider": provider,
        "provider_type": "sportsbook_odds",
        "provider_event_id": event.get("id") or event.get("event_id"),
        "event_id": event.get("id") or event.get("event_id"),
        "id": event.get("id") or event.get("event_id"),
        "sport_key": event.get("sport_key"),
        "league": league or event.get("sport_title") or event.get("league"),
        "commence_time": event.get("commence_time"),
        "home_team": event.get("home_team"),
        "away_team": event.get("away_team"),
        "raw": event,
    }


def normalize_sportsbook_odds(
    provider: str,
    event_id: str,
    sport_key: str | None,
    market: str | None,
    sportsbook: str | None,
    selection: str | None,
    price_american: Any,
    point: Any,
    last_update: Any,
    raw: dict[str, Any],
) -> dict[str, Any]:
    decimal = american_to_decimal(price_american) if isinstance(price_american, (int, float)) else None
    implied = implied_probability_from_american(price_american) if isinstance(price_american, (int, float)) else None
    return {
        "provider": provider,
        "provider_type": "sportsbook_odds",
        "provider_event_id": event_id,
        "sport_key": sport_key,
        "market": market,
        "sportsbook": sportsbook,
        "selection": selection,
        "price_american": price_american,
        "price_decimal": decimal,
        "implied_probability": implied,
        "point": point,
        "last_update": last_update,
        "raw": raw,
    }


def normalize_kalshi_event(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider": "kalshi",
        "provider_type": "prediction_market",
        "event_ticker": event.get("event_ticker") or event.get("ticker"),
        "series_ticker": event.get("series_ticker"),
        "title": event.get("title"),
        "category": event.get("category"),
        "status": event.get("status"),
        "raw": event,
    }


def normalize_kalshi_market(market: dict[str, Any]) -> dict[str, Any]:
    yes_bid = market.get("yes_bid")
    yes_ask = market.get("yes_ask")
    last_price = market.get("last_price")
    implied = yes_ask if yes_ask is not None else yes_bid if yes_bid is not None else last_price
    return {
        "provider": "kalshi",
        "provider_type": "prediction_market",
        "market_ticker": market.get("ticker") or market.get("market_ticker"),
        "event_ticker": market.get("event_ticker"),
        "title": market.get("title"),
        "subtitle": market.get("subtitle"),
        "status": market.get("status"),
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "no_bid": market.get("no_bid"),
        "no_ask": market.get("no_ask"),
        "last_price": last_price,
        "volume": market.get("volume"),
        "liquidity": market.get("liquidity"),
        "close_time": market.get("close_time"),
        "implied_probability_yes": implied,
        "raw": market,
    }

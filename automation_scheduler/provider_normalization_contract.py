from __future__ import annotations

from typing import Any

from .injury_weather_adapter_contract import normalize_payload as normalize_injury_weather
from .kalshi_adapter_contract import normalize_payload as normalize_kalshi
from .news_events_adapter_contract import normalize_payload as normalize_news_events
from .player_props_adapter_contract import normalize_payload as normalize_player_props
from .sportsbook_adapter_contract import normalize_payload as normalize_sportsbook
from .stock_fundamentals_adapter_contract import normalize_payload as normalize_stock_fundamentals
from .stock_price_adapter_contract import normalize_payload as normalize_stock_price

NORMALIZED_SCHEMAS: dict[str, list[str]] = {
    "sportsbook_odds": ["event_id", "sport", "league", "event_name", "start_time", "book", "market", "selection", "line", "odds", "timestamp"],
    "player_props": ["event_id", "player_name", "team", "market", "selection", "line", "odds", "timestamp"],
    "prediction_market": ["market_id", "event_title", "contract_title", "yes_price", "no_price", "implied_probability", "volume", "open_interest", "close_time", "timestamp"],
    "stock_price": ["symbol", "price", "bid", "ask", "volume", "timestamp"],
    "stock_fundamentals": ["symbol", "market_cap", "revenue", "earnings", "sector", "report_date", "timestamp"],
    "news_events": ["source", "title", "event_type", "affected_entities", "severity_score", "published_at", "timestamp"],
    "injury_weather": ["event_id", "entity", "status", "severity_score", "source", "timestamp"],
}


def get_normalized_schema(provider_type: str) -> list[str]:
    if provider_type not in NORMALIZED_SCHEMAS:
        raise ValueError(f"unknown provider_type: {provider_type}")
    return list(NORMALIZED_SCHEMAS[provider_type])


def normalize_provider_payload(provider_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    if provider_type == "sportsbook_odds":
        return normalize_sportsbook(payload)
    if provider_type == "player_props":
        return normalize_player_props(payload)
    if provider_type == "prediction_market":
        return normalize_kalshi(payload)
    if provider_type == "stock_price":
        return normalize_stock_price(payload)
    if provider_type == "stock_fundamentals":
        return normalize_stock_fundamentals(payload)
    if provider_type == "news_events":
        return normalize_news_events(payload)
    if provider_type == "injury_weather":
        return normalize_injury_weather(payload)
    raise ValueError(f"unknown provider_type: {provider_type}")


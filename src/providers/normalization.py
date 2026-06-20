from __future__ import annotations

from typing import Any, Mapping

NORMALIZED_SCHEMAS: dict[str, list[str]] = {
    "sportsbook_odds": [
        "event_id",
        "sport",
        "league",
        "event_name",
        "start_time",
        "book",
        "market",
        "selection",
        "line",
        "odds",
        "timestamp",
    ],
    "player_props": ["event_id", "player_name", "team", "market", "selection", "line", "odds", "timestamp"],
    "prediction_market": [
        "provider_id",
        "provider_name",
        "received_at",
        "market_id",
        "event_id",
        "event_title",
        "contract_id",
        "contract_title",
        "ticker",
        "yes_bid",
        "yes_ask",
        "no_bid",
        "no_ask",
        "yes_price",
        "no_price",
        "implied_probability",
        "volume",
        "open_interest",
        "liquidity_score",
        "close_time",
        "status",
        "settlement_rule",
        "timestamp",
        "source_payload_redacted",
        "schema_version",
    ],
    "stock_price": ["symbol", "price", "bid", "ask", "volume", "timestamp"],
    "stock_fundamentals": ["symbol", "market_cap", "revenue", "earnings", "sector", "report_date", "timestamp"],
    "news_events": ["source", "title", "event_type", "affected_entities", "severity_score", "published_at", "timestamp"],
    "injury_weather": ["event_id", "entity", "status", "severity_score", "source", "timestamp"],
}


def get_normalized_schema(provider_type: str) -> list[str]:
    if provider_type not in NORMALIZED_SCHEMAS:
        raise ValueError(f"unknown provider_type: {provider_type}")
    return list(NORMALIZED_SCHEMAS[provider_type])


def normalize_provider_payload(provider_type: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    if provider_type and "provider_type" not in normalized:
        normalized["provider_type"] = provider_type
    return normalized

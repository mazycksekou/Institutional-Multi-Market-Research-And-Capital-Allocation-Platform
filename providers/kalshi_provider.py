from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from src.providers.prediction_markets.adapters import normalize_prediction_market_quote as _normalize_prediction_market_quote
from src.services.prediction_market_runtime_bridge import (
    PREDICTION_MARKET_CONNECTOR_CONFIGURATION,
    PREDICTION_MARKET_CONNECTOR_READINESS,
    PREDICTION_MARKET_DISABLED_CLIENT,
    PREDICTION_MARKET_PROVIDER_ADAPTER,
    enrich_with_kalshi as _bridge_enrich_with_kalshi,
)

requests = SimpleNamespace(get=None)


def normalize_kalshi_probability_market(market: dict[str, Any]) -> dict[str, Any]:
    return _normalize_prediction_market_quote(market, provider="kalshi", market_type="kalshi_prediction_market")


def enrich_with_kalshi(ticket: dict[str, Any]) -> dict[str, Any]:
    return _bridge_enrich_with_kalshi(ticket)


def describe_kalshi_provider() -> dict[str, Any]:
    return {
        "provider": "kalshi",
        "canonical_provider": "prediction_market",
        "connector_configuration": dict(PREDICTION_MARKET_CONNECTOR_CONFIGURATION.describe()),
        "connector_readiness": dict(PREDICTION_MARKET_CONNECTOR_READINESS),
        "disabled_client": PREDICTION_MARKET_DISABLED_CLIENT.describe(),
        "provider_contract": PREDICTION_MARKET_PROVIDER_ADAPTER.contract.as_dict(),
        "provider_health": PREDICTION_MARKET_PROVIDER_ADAPTER.health_check(),
    }


__all__ = [
    "describe_kalshi_provider",
    "enrich_with_kalshi",
    "normalize_kalshi_probability_market",
]

from __future__ import annotations

from typing import Any

from src.connectors.errors import ConnectorDisabledError
from src.connectors.prediction_market_data import (
    build_prediction_market_connector_configuration,
    describe_prediction_market_connector_readiness,
)

KALSHI_BASE_URL = "https://external-api.kalshi.com/trade-api/v2"
REQUEST_TIMEOUT = 8

_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}

KALSHI_CONNECTOR_CONFIGURATION = build_prediction_market_connector_configuration(
    metadata={"legacy_module": "kalshi_client"},
)
KALSHI_CONNECTOR_READINESS = describe_prediction_market_connector_readiness()


def describe_kalshi_client() -> dict[str, Any]:
    return {
        "provider": "kalshi",
        "canonical_provider": "prediction_market",
        "connector_configuration": dict(KALSHI_CONNECTOR_CONFIGURATION.describe()),
        "connector_readiness": dict(KALSHI_CONNECTOR_READINESS),
        "base_url": KALSHI_BASE_URL,
        "request_timeout": REQUEST_TIMEOUT,
        "live_access_enabled": False,
    }


def _disabled(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
    raise ConnectorDisabledError(
        "legacy Kalshi client is disabled; use src.connectors.prediction_market_data and src.providers.prediction_markets"
    )


def get_kalshi_market(ticker: str) -> dict[str, Any]:
    return _disabled(ticker)


def get_kalshi_orderbook(ticker: str) -> dict[str, Any]:
    return _disabled(ticker)


def get_kalshi_market_snapshot(ticker: str) -> dict[str, Any]:
    return _disabled(ticker)


__all__ = [
    "KALSHI_BASE_URL",
    "KALSHI_CONNECTOR_CONFIGURATION",
    "KALSHI_CONNECTOR_READINESS",
    "REQUEST_TIMEOUT",
    "describe_kalshi_client",
    "get_kalshi_market",
    "get_kalshi_market_snapshot",
    "get_kalshi_orderbook",
]

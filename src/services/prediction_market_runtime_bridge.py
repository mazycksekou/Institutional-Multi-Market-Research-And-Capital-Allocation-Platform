from __future__ import annotations

from typing import Any

from src.connectors.prediction_market_data import (
    build_prediction_market_connector_configuration,
    build_prediction_market_disabled_live_client,
    describe_prediction_market_connector_readiness,
)
from src.core.entity_resolver import normalize_ticket_fields
from src.providers.prediction_markets.adapters import PredictionMarketProviderAdapter


SCHEMA_VERSION = "src.services.prediction_market_runtime_bridge.v1"

PREDICTION_MARKET_CONNECTOR_CONFIGURATION = build_prediction_market_connector_configuration(
    metadata={"bridge_module": "src.services.prediction_market_runtime_bridge"},
)
PREDICTION_MARKET_CONNECTOR_READINESS = describe_prediction_market_connector_readiness()
PREDICTION_MARKET_DISABLED_CLIENT = build_prediction_market_disabled_live_client()
PREDICTION_MARKET_PROVIDER_ADAPTER = PredictionMarketProviderAdapter()


def enrich_with_kalshi(ticket: dict[str, Any]) -> dict[str, Any]:
    normalized_ticket = normalize_ticket_fields(ticket)
    return {
        "provider": "kalshi",
        "canonical_provider": "prediction_market",
        "provider_status": "unavailable",
        "reason": "prediction_market_connector_boundary_disabled",
        "data": [],
        "provider_notes": [
            "Prediction-market runtime access is routed through the canonical connector boundary.",
            "Legacy Kalshi provider shells are no longer runtime dependencies.",
        ],
        "normalized_ticket": normalized_ticket,
        "connector_configuration": dict(PREDICTION_MARKET_CONNECTOR_CONFIGURATION.describe()),
        "connector_readiness": dict(PREDICTION_MARKET_CONNECTOR_READINESS),
        "disabled_client": PREDICTION_MARKET_DISABLED_CLIENT.describe(),
        "provider_contract": PREDICTION_MARKET_PROVIDER_ADAPTER.contract.as_dict(),
        "provider_health": PREDICTION_MARKET_PROVIDER_ADAPTER.health_check(),
        "schema_version": SCHEMA_VERSION,
    }


def enrich_with_prediction_market(ticket: dict[str, Any]) -> dict[str, Any]:
    return enrich_with_kalshi(ticket)


__all__ = [
    "SCHEMA_VERSION",
    "PREDICTION_MARKET_CONNECTOR_CONFIGURATION",
    "PREDICTION_MARKET_CONNECTOR_READINESS",
    "PREDICTION_MARKET_DISABLED_CLIENT",
    "PREDICTION_MARKET_PROVIDER_ADAPTER",
    "enrich_with_kalshi",
    "enrich_with_prediction_market",
]

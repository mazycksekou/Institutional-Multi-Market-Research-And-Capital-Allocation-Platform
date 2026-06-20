"""Scaffold-only prediction market data connector boundary.

This is an inert read-only connector wrapper. It does not perform live access
and it exists to provide a vendor-neutral landing zone for future transport.
"""

from .adapter import PredictionMarketConnectorAdapter
from .client import PredictionMarketConnectorClient, PredictionMarketReadOnlyClient, build_prediction_market_read_only_client
from .contracts import PREDICTION_MARKET_DATA_CONNECTOR_CATEGORY, PredictionMarketDataConnectorContract, build_prediction_market_data_connector_contract
from .models import PredictionMarketConnectorStatus, PredictionMarketRecord, PredictionMarketSnapshot
from .payloads import build_prediction_market_record, normalize_prediction_market_payload, validate_prediction_market_payload

__all__ = [
    "PREDICTION_MARKET_DATA_CONNECTOR_CATEGORY",
    "PredictionMarketConnectorAdapter",
    "PredictionMarketConnectorClient",
    "PredictionMarketConnectorStatus",
    "PredictionMarketDataConnectorContract",
    "PredictionMarketReadOnlyClient",
    "PredictionMarketRecord",
    "PredictionMarketSnapshot",
    "build_prediction_market_data_connector_contract",
    "build_prediction_market_read_only_client",
    "build_prediction_market_record",
    "normalize_prediction_market_payload",
    "validate_prediction_market_payload",
]

"""Scaffold-only prediction market data connector boundary."""

from .contracts import (
    PREDICTION_MARKET_DATA_CONNECTOR_CATEGORY,
    PredictionMarketDataConnectorContract,
    build_prediction_market_data_connector_contract,
)

__all__ = [
    "PREDICTION_MARKET_DATA_CONNECTOR_CATEGORY",
    "PredictionMarketDataConnectorContract",
    "build_prediction_market_data_connector_contract",
]

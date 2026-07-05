from __future__ import annotations

from .read_only import PredictionMarketReadOnlyClient, build_prediction_market_read_only_client

PredictionMarketConnectorClient = PredictionMarketReadOnlyClient

__all__ = [
    "PredictionMarketConnectorClient",
    "PredictionMarketReadOnlyClient",
    "build_prediction_market_read_only_client",
]

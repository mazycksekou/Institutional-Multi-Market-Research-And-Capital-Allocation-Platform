"""Scaffold-only market data connector boundary."""

from .contracts import MARKET_DATA_CONNECTOR_CATEGORY, MarketDataConnectorContract, build_market_data_connector_contract

__all__ = [
    "MARKET_DATA_CONNECTOR_CATEGORY",
    "MarketDataConnectorContract",
    "build_market_data_connector_contract",
]

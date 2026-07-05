from __future__ import annotations

from .read_only import MarketDataReadOnlyClient, build_market_data_read_only_client

MarketDataConnectorClient = MarketDataReadOnlyClient

__all__ = [
    "MarketDataConnectorClient",
    "MarketDataReadOnlyClient",
    "build_market_data_read_only_client",
]

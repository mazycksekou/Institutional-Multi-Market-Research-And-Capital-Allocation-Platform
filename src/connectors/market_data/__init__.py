"""Scaffold-only market data connector boundary.

This is an inert read-only connector wrapper. It does not perform live access
and it exists to provide a vendor-neutral landing zone for future transport.
"""

from .adapter import MarketDataConnectorAdapter
from .client import MarketDataConnectorClient, MarketDataReadOnlyClient, build_market_data_read_only_client
from .contracts import MARKET_DATA_CONNECTOR_CATEGORY, MarketDataConnectorContract, build_market_data_connector_contract
from .models import MarketDataConnectorStatus, MarketDataQuote, MarketDataSnapshot
from .payloads import build_market_data_quote, normalize_market_data_payload, validate_market_data_payload

__all__ = [
    "MARKET_DATA_CONNECTOR_CATEGORY",
    "MarketDataConnectorAdapter",
    "MarketDataConnectorClient",
    "MarketDataConnectorContract",
    "MarketDataConnectorStatus",
    "MarketDataQuote",
    "MarketDataReadOnlyClient",
    "MarketDataSnapshot",
    "build_market_data_connector_contract",
    "build_market_data_quote",
    "build_market_data_read_only_client",
    "normalize_market_data_payload",
    "validate_market_data_payload",
]

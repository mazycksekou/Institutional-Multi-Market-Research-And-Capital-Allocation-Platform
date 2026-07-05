from __future__ import annotations

from .read_only import OddsDataReadOnlyClient, build_odds_data_read_only_client

OddsDataConnectorClient = OddsDataReadOnlyClient

__all__ = [
    "OddsDataConnectorClient",
    "OddsDataReadOnlyClient",
    "build_odds_data_read_only_client",
]

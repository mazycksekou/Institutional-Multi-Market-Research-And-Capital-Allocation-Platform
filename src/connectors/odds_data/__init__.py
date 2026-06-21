"""Scaffold-only odds data connector boundary.

This is an inert read-only connector wrapper. It does not perform live access
and it exists to provide a vendor-neutral landing zone for future transport.
"""

from .adapter import OddsDataConnectorAdapter
from .client import OddsDataConnectorClient, OddsDataReadOnlyClient, build_odds_data_read_only_client
from .contracts import ODDS_DATA_CONNECTOR_CATEGORY, OddsDataConnectorContract, build_odds_data_connector_contract
from .models import OddsDataConnectorStatus, OddsDataRecord, OddsDataSnapshot
from .payloads import build_odds_record, normalize_odds_payload, validate_odds_payload

__all__ = [
    "ODDS_DATA_CONNECTOR_CATEGORY",
    "OddsDataConnectorAdapter",
    "OddsDataConnectorClient",
    "OddsDataConnectorContract",
    "OddsDataConnectorStatus",
    "OddsDataReadOnlyClient",
    "OddsDataRecord",
    "OddsDataSnapshot",
    "build_odds_data_connector_contract",
    "build_odds_data_read_only_client",
    "build_odds_record",
    "normalize_odds_payload",
    "validate_odds_payload",
]

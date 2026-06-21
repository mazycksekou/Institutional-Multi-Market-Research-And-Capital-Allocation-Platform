"""Canonical connector boundary for raw external access.

Connectors own future live external access. Providers normalize already-supplied
data. This package is scaffold-only and import-safe.
"""

from .contracts import CONNECTOR_CATEGORIES, ConnectorContract, build_connector_contract
from .errors import (
    ConnectorBoundaryError,
    ConnectorConfigurationError,
    ConnectorDisabledError,
    ConnectorError,
    ConnectorResponseError,
    ConnectorUnavailableError,
)
from .models import ConnectorHealthStatus, ConnectorRequest, ConnectorResponse
from .odds_data import (
    ODDS_DATA_CONNECTOR_CATEGORY,
    OddsDataConnectorAdapter,
    OddsDataConnectorClient,
    OddsDataConnectorContract,
    OddsDataConnectorStatus,
    OddsDataReadOnlyClient,
    OddsDataRecord,
    OddsDataSnapshot,
    build_odds_data_connector_contract,
    build_odds_data_read_only_client,
    build_odds_record,
    normalize_odds_payload,
    validate_odds_payload,
)
from .policy import ConnectorPolicy, assert_connector_boundary, build_scaffold_connector_policy
from .registry import ConnectorRegistry, create_connector_registry, get_connector_registry

__all__ = [
    "CONNECTOR_CATEGORIES",
    "ConnectorBoundaryError",
    "ConnectorConfigurationError",
    "ConnectorDisabledError",
    "ConnectorContract",
    "ConnectorError",
    "ConnectorHealthStatus",
    "ConnectorPolicy",
    "ConnectorRegistry",
    "ConnectorRequest",
    "ConnectorResponse",
    "ConnectorResponseError",
    "ConnectorUnavailableError",
    "ODDS_DATA_CONNECTOR_CATEGORY",
    "assert_connector_boundary",
    "build_connector_contract",
    "build_odds_data_connector_contract",
    "build_odds_data_read_only_client",
    "build_odds_record",
    "build_scaffold_connector_policy",
    "create_connector_registry",
    "get_connector_registry",
    "normalize_odds_payload",
    "OddsDataConnectorAdapter",
    "OddsDataConnectorClient",
    "OddsDataConnectorContract",
    "OddsDataConnectorStatus",
    "OddsDataReadOnlyClient",
    "OddsDataRecord",
    "OddsDataSnapshot",
    "validate_odds_payload",
]

"""Canonical connector boundary for raw external access.

Connectors own future live external access. Providers normalize already-supplied
data. This package is scaffold-only and import-safe.
"""

from .contracts import CONNECTOR_CATEGORIES, ConnectorContract, build_connector_contract
from .errors import (
    ConnectorBoundaryError,
    ConnectorConfigurationError,
    ConnectorError,
    ConnectorResponseError,
    ConnectorUnavailableError,
)
from .models import ConnectorHealthStatus, ConnectorRequest, ConnectorResponse
from .policy import ConnectorPolicy, assert_connector_boundary, build_scaffold_connector_policy
from .registry import ConnectorRegistry, create_connector_registry, get_connector_registry

__all__ = [
    "CONNECTOR_CATEGORIES",
    "ConnectorBoundaryError",
    "ConnectorConfigurationError",
    "ConnectorContract",
    "ConnectorError",
    "ConnectorHealthStatus",
    "ConnectorPolicy",
    "ConnectorRegistry",
    "ConnectorRequest",
    "ConnectorResponse",
    "ConnectorResponseError",
    "ConnectorUnavailableError",
    "assert_connector_boundary",
    "build_connector_contract",
    "build_scaffold_connector_policy",
    "create_connector_registry",
    "get_connector_registry",
]

"""Scaffold-only prediction market data connector boundary.

This is an inert read-only connector wrapper. It does not perform live access
and it exists to provide a vendor-neutral landing zone for future transport.
"""

from .adapter import PredictionMarketConnectorAdapter
from .auth import PredictionMarketAuthRequirement, build_prediction_market_auth_requirement
from .client import PredictionMarketConnectorClient, PredictionMarketReadOnlyClient, build_prediction_market_read_only_client
from .configuration import PredictionMarketConnectorConfiguration, build_prediction_market_connector_configuration
from .contracts import PREDICTION_MARKET_DATA_CONNECTOR_CATEGORY, PredictionMarketDataConnectorContract, build_prediction_market_data_connector_contract
from .disabled_client import PredictionMarketDisabledLiveClient, build_prediction_market_disabled_live_client
from .models import PredictionMarketConnectorStatus, PredictionMarketRecord, PredictionMarketSnapshot
from .readiness import PredictionMarketConnectorReadiness, describe_prediction_market_connector_readiness
from .payloads import build_prediction_market_record, normalize_prediction_market_payload, validate_prediction_market_payload
from .signing import PredictionMarketSigningBoundary, build_prediction_market_signing_boundary, sign_prediction_market_request
from .transport import PredictionMarketConnectorTransport, build_prediction_market_transport

__all__ = [
    "PREDICTION_MARKET_DATA_CONNECTOR_CATEGORY",
    "PredictionMarketAuthRequirement",
    "PredictionMarketConnectorAdapter",
    "PredictionMarketConnectorConfiguration",
    "PredictionMarketConnectorClient",
    "PredictionMarketConnectorReadiness",
    "PredictionMarketConnectorTransport",
    "PredictionMarketConnectorStatus",
    "PredictionMarketDataConnectorContract",
    "PredictionMarketDisabledLiveClient",
    "PredictionMarketReadOnlyClient",
    "PredictionMarketRecord",
    "PredictionMarketSnapshot",
    "PredictionMarketSigningBoundary",
    "build_prediction_market_data_connector_contract",
    "build_prediction_market_auth_requirement",
    "build_prediction_market_connector_configuration",
    "build_prediction_market_disabled_live_client",
    "build_prediction_market_read_only_client",
    "build_prediction_market_record",
    "build_prediction_market_signing_boundary",
    "build_prediction_market_transport",
    "describe_prediction_market_connector_readiness",
    "normalize_prediction_market_payload",
    "validate_prediction_market_payload",
    "sign_prediction_market_request",
]

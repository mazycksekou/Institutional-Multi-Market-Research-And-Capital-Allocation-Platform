"""Scaffold-only odds data connector boundary.

This is an inert read-only connector wrapper. It does not perform live access
and it exists to provide a vendor-neutral landing zone for future transport.
"""

from .auth import OddsDataAuthRequirement, build_odds_data_auth_requirement
from .adapter import OddsDataConnectorAdapter
from .configuration import OddsDataConnectorConfiguration, build_odds_data_connector_configuration
from .client import OddsDataConnectorClient, OddsDataReadOnlyClient, build_odds_data_read_only_client
from .contracts import ODDS_DATA_CONNECTOR_CATEGORY, OddsDataConnectorContract, build_odds_data_connector_contract
from .disabled_client import OddsDataDisabledLiveClient, build_odds_data_disabled_live_client
from .live_client import OddsDataLiveClient, build_odds_data_live_client
from .models import OddsDataConnectorStatus, OddsDataRecord, OddsDataSnapshot
from .readiness import OddsDataConnectorReadiness, describe_odds_data_connector_readiness
from .payloads import build_odds_record, normalize_odds_payload, validate_odds_payload
from .source_profile import OddsDataSourceProfile, build_odds_data_source_profile
from .transport import OddsDataConnectorTransport, build_odds_data_transport
from .nfl import (
    NFL_ODDS_CONNECTOR_EXECUTION_MODE,
    NFL_ODDS_CONNECTOR_FAMILY,
    NFL_ODDS_CONNECTOR_ID,
    NFL_ODDS_CONNECTOR_NAME,
    NFL_ODDS_PROVIDER_ID,
    NFL_ODDS_PROVIDER_NAME,
    NFL_ODDS_PROVIDER_ROLE,
    NFL_ODDS_RESEARCH_ASSET_ID,
    build_nfl_odds_connector_bundle,
    build_nfl_odds_provider_capability,
)

__all__ = [
    "ODDS_DATA_CONNECTOR_CATEGORY",
    "OddsDataAuthRequirement",
    "OddsDataConnectorAdapter",
    "OddsDataConnectorConfiguration",
    "OddsDataConnectorClient",
    "OddsDataConnectorReadiness",
    "OddsDataConnectorTransport",
    "OddsDataConnectorContract",
    "OddsDataConnectorStatus",
    "OddsDataDisabledLiveClient",
    "OddsDataLiveClient",
    "OddsDataReadOnlyClient",
    "OddsDataRecord",
    "OddsDataSnapshot",
    "OddsDataSourceProfile",
    "NFL_ODDS_CONNECTOR_EXECUTION_MODE",
    "NFL_ODDS_CONNECTOR_FAMILY",
    "NFL_ODDS_CONNECTOR_ID",
    "NFL_ODDS_CONNECTOR_NAME",
    "NFL_ODDS_PROVIDER_ID",
    "NFL_ODDS_PROVIDER_NAME",
    "NFL_ODDS_PROVIDER_ROLE",
    "NFL_ODDS_RESEARCH_ASSET_ID",
    "build_odds_data_connector_contract",
    "build_odds_data_auth_requirement",
    "build_odds_data_connector_configuration",
    "build_odds_data_disabled_live_client",
    "build_odds_data_read_only_client",
    "build_odds_data_live_client",
    "build_odds_record",
    "build_odds_data_source_profile",
    "build_odds_data_transport",
    "build_nfl_odds_connector_bundle",
    "build_nfl_odds_provider_capability",
    "describe_odds_data_connector_readiness",
    "normalize_odds_payload",
    "validate_odds_payload",
]

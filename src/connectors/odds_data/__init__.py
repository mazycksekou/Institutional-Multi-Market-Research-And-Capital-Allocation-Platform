"""Scaffold-only odds data connector boundary."""

from .contracts import ODDS_DATA_CONNECTOR_CATEGORY, OddsDataConnectorContract, build_odds_data_connector_contract

__all__ = [
    "ODDS_DATA_CONNECTOR_CATEGORY",
    "OddsDataConnectorContract",
    "build_odds_data_connector_contract",
]

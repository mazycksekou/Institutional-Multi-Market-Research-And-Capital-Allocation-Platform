"""Scaffold-only feeds connector boundary."""

from .contracts import FEEDS_CONNECTOR_CATEGORY, FeedsConnectorContract, build_feeds_connector_contract

__all__ = [
    "FEEDS_CONNECTOR_CATEGORY",
    "FeedsConnectorContract",
    "build_feeds_connector_contract",
]

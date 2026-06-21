from __future__ import annotations

from .live_client import OddsDataLiveClient, build_odds_data_live_client

OddsDataDisabledLiveClient = OddsDataLiveClient

__all__ = [
    "OddsDataDisabledLiveClient",
    "OddsDataLiveClient",
    "build_odds_data_live_client",
    "build_odds_data_disabled_live_client",
]


def build_odds_data_disabled_live_client() -> OddsDataDisabledLiveClient:
    return build_odds_data_live_client()

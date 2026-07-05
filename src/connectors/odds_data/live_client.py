from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..errors import ConnectorDisabledError
from .readiness import OddsDataConnectorReadiness
from .source_profile import OddsDataSourceProfile, build_odds_data_source_profile


@dataclass(frozen=True)
class OddsDataLiveClient:
    provider: str = "odds_data"
    read_only: bool = True
    readiness: OddsDataConnectorReadiness = field(default_factory=OddsDataConnectorReadiness)
    source_profile: OddsDataSourceProfile = field(default_factory=build_odds_data_source_profile)
    message: str = "live client is disabled until live access is explicitly enabled"

    def describe(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "read_only": self.read_only,
            "ready_status": self.readiness.status,
            "live_access_enabled": self.readiness.live_access_enabled,
            "legacy_aliases": list(self.source_profile.legacy_aliases),
            "message": self.message,
        }

    def fetch_odds(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError(
            "odds_data live client is disabled until live access is explicitly enabled"
        )

    def fetch_events(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError(
            "odds_data live client is disabled until live access is explicitly enabled"
        )

    def fetch_books(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError(
            "odds_data live client is disabled until live access is explicitly enabled"
        )

    def fetch_snapshot(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError(
            "odds_data live client is disabled until live access is explicitly enabled"
        )

    def sign_request(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError(
            "odds_data live client is disabled until live access is explicitly enabled"
        )

    def request(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError(
            "odds_data live client is disabled until live access is explicitly enabled"
        )


def build_odds_data_live_client() -> OddsDataLiveClient:
    return OddsDataLiveClient()

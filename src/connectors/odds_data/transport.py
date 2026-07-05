from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..errors import ConnectorDisabledError


@dataclass(frozen=True)
class OddsDataConnectorTransport:
    provider: str = "odds_data"
    read_only: bool = True
    live_access_enabled: bool = False
    credential_names: tuple[str, ...] = (
        "ODDS_DATA_API_KEY",
        "ODDS_DATA_API_SECRET",
    )
    description: str = "transport is inert until live access is explicitly enabled"

    def describe(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "read_only": self.read_only,
            "live_access_enabled": self.live_access_enabled,
            "credential_names": list(self.credential_names),
            "description": self.description,
        }

    def request(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError(
            "odds_data transport is disabled until live access is explicitly enabled"
        )

    def fetch_odds(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError(
            "odds_data transport is disabled until live access is explicitly enabled"
        )

    def fetch_events(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError(
            "odds_data transport is disabled until live access is explicitly enabled"
        )

    def fetch_books(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError(
            "odds_data transport is disabled until live access is explicitly enabled"
        )

    def fetch_snapshot(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError(
            "odds_data transport is disabled until live access is explicitly enabled"
        )


def build_odds_data_transport(
    *,
    provider: str = "odds_data",
    read_only: bool = True,
    live_access_enabled: bool = False,
    credential_names: tuple[str, ...] = (
        "ODDS_DATA_API_KEY",
        "ODDS_DATA_API_SECRET",
    ),
    description: str = "transport is inert until live access is explicitly enabled",
) -> OddsDataConnectorTransport:
    return OddsDataConnectorTransport(
        provider=provider,
        read_only=read_only,
        live_access_enabled=live_access_enabled,
        credential_names=credential_names,
        description=description,
    )

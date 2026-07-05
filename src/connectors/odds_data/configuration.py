from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


ODDS_DATA_CONNECTOR_CATEGORY = "odds_data"


@dataclass(frozen=True)
class OddsDataConnectorConfiguration:
    provider: str = ODDS_DATA_CONNECTOR_CATEGORY
    live_access_enabled: bool = False
    read_only: bool = True
    credential_names: tuple[str, ...] = (
        "ODDS_DATA_API_KEY",
        "ODDS_DATA_API_SECRET",
    )
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def describe(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "live_access_enabled": self.live_access_enabled,
            "read_only": self.read_only,
            "credential_names": list(self.credential_names),
            "metadata": dict(self.metadata),
        }


def build_odds_data_connector_configuration(
    *,
    provider: str = ODDS_DATA_CONNECTOR_CATEGORY,
    live_access_enabled: bool = False,
    read_only: bool = True,
    credential_names: tuple[str, ...] = (
        "ODDS_DATA_API_KEY",
        "ODDS_DATA_API_SECRET",
    ),
    metadata: Mapping[str, Any] | None = None,
) -> OddsDataConnectorConfiguration:
    return OddsDataConnectorConfiguration(
        provider=provider,
        live_access_enabled=live_access_enabled,
        read_only=read_only,
        credential_names=credential_names,
        metadata={} if metadata is None else dict(metadata),
    )

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

ODDS_DATA_CONNECTOR_CATEGORY = "odds_data"


@dataclass(frozen=True)
class OddsDataConnectorContract:
    name: str
    description: str = ""
    supports_live_access: bool = False
    supports_credentials: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)


def build_odds_data_connector_contract(
    name: str,
    description: str = "",
    *,
    supports_live_access: bool = False,
    supports_credentials: bool = False,
    metadata: Mapping[str, Any] | None = None,
) -> OddsDataConnectorContract:
    return OddsDataConnectorContract(
        name=name,
        description=description,
        supports_live_access=supports_live_access,
        supports_credentials=supports_credentials,
        metadata={} if metadata is None else dict(metadata),
    )

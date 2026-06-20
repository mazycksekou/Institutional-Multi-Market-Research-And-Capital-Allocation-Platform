from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Final, Literal, Mapping

ConnectorCategory = Literal["market_data", "odds_data", "prediction_market_data", "web_scraping", "feeds"]
CONNECTOR_CATEGORIES: Final[tuple[str, ...]] = (
    "market_data",
    "odds_data",
    "prediction_market_data",
    "web_scraping",
    "feeds",
)


@dataclass(frozen=True)
class ConnectorContract:
    category: str
    name: str
    description: str = ""
    supports_live_access: bool = False
    supports_credentials: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)


def build_connector_contract(
    *,
    category: str,
    name: str,
    description: str = "",
    supports_live_access: bool = False,
    supports_credentials: bool = False,
    metadata: Mapping[str, Any] | None = None,
) -> ConnectorContract:
    return ConnectorContract(
        category=category,
        name=name,
        description=description,
        supports_live_access=supports_live_access,
        supports_credentials=supports_credentials,
        metadata={} if metadata is None else dict(metadata),
    )

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

FEEDS_CONNECTOR_CATEGORY = "feeds"


@dataclass(frozen=True)
class FeedsConnectorContract:
    name: str
    description: str = ""
    supports_live_access: bool = False
    supports_credentials: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)


def build_feeds_connector_contract(
    name: str,
    description: str = "",
    *,
    supports_live_access: bool = False,
    supports_credentials: bool = False,
    metadata: Mapping[str, Any] | None = None,
) -> FeedsConnectorContract:
    return FeedsConnectorContract(
        name=name,
        description=description,
        supports_live_access=supports_live_access,
        supports_credentials=supports_credentials,
        metadata={} if metadata is None else dict(metadata),
    )

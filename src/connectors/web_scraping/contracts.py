from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

WEB_SCRAPING_CONNECTOR_CATEGORY = "web_scraping"


@dataclass(frozen=True)
class WebScrapingConnectorContract:
    name: str
    description: str = ""
    supports_live_access: bool = False
    supports_credentials: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)


def build_web_intake_connector_contract(
    name: str,
    description: str = "",
    *,
    supports_live_access: bool = False,
    supports_credentials: bool = False,
    metadata: Mapping[str, Any] | None = None,
) -> WebScrapingConnectorContract:
    return WebScrapingConnectorContract(
        name=name,
        description=description,
        supports_live_access=supports_live_access,
        supports_credentials=supports_credentials,
        metadata={} if metadata is None else dict(metadata),
    )

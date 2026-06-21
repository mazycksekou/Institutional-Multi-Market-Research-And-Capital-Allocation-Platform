from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from ..errors import ConnectorDisabledError
from .client import MarketDataReadOnlyClient
from .contracts import MARKET_DATA_CONNECTOR_CATEGORY
from .payloads import build_market_data_quote, normalize_market_data_payload, validate_market_data_payload


@dataclass(frozen=True)
class MarketDataConnectorAdapter:
    client: MarketDataReadOnlyClient = field(default_factory=MarketDataReadOnlyClient)
    category: str = MARKET_DATA_CONNECTOR_CATEGORY
    live_access_enabled: bool = False

    def describe(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "provider": self.client.provider,
            "read_only": self.client.read_only,
            "live_access_enabled": self.live_access_enabled,
        }

    def normalize_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return normalize_market_data_payload(payload, source=self.client.provider)

    def build_quote(self, payload: Mapping[str, Any]) -> Any:
        return build_market_data_quote(payload, source=self.client.provider)

    def build_snapshot(self, payloads: Iterable[Mapping[str, Any]]) -> Any:
        return self.client.build_snapshot(payloads)

    def validate_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return validate_market_data_payload(payload)

    def fetch_market_data(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError("market_data connector is inert until live access is explicitly enabled")

    def fetch_quotes(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError("market_data connector is inert until live access is explicitly enabled")

    def fetch_snapshot(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError("market_data connector is inert until live access is explicitly enabled")

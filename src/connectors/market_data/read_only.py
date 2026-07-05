from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from ..errors import ConnectorDisabledError
from .models import MarketDataConnectorStatus, MarketDataSnapshot
from .payloads import build_market_data_quote, normalize_market_data_payload


@dataclass(frozen=True)
class MarketDataReadOnlyClient:
    provider: str = "market_data"
    read_only: bool = True
    status: MarketDataConnectorStatus = field(default_factory=MarketDataConnectorStatus)

    def describe(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "read_only": self.read_only,
            "status": self.status.status,
            "live_access_enabled": self.status.live_access_enabled,
        }

    def normalize_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return normalize_market_data_payload(payload, source=self.provider)

    def build_snapshot(self, payloads: Iterable[Mapping[str, Any]]) -> MarketDataSnapshot:
        records = tuple(build_market_data_quote(payload, source=self.provider) for payload in payloads)
        return MarketDataSnapshot(provider=self.provider, records=records)

    def fetch_market_data(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError("market_data connector is inert until live access is explicitly enabled")

    def fetch_quotes(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError("market_data connector is inert until live access is explicitly enabled")

    def fetch_snapshot(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError("market_data connector is inert until live access is explicitly enabled")


def build_market_data_read_only_client() -> MarketDataReadOnlyClient:
    return MarketDataReadOnlyClient()

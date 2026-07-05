from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from ..errors import ConnectorDisabledError
from .models import OddsDataConnectorStatus, OddsDataSnapshot
from .payloads import build_odds_record, normalize_odds_payload


@dataclass(frozen=True)
class OddsDataReadOnlyClient:
    provider: str = "odds_data"
    read_only: bool = True
    status: OddsDataConnectorStatus = field(default_factory=OddsDataConnectorStatus)

    def describe(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "read_only": self.read_only,
            "status": self.status.status,
            "live_access_enabled": self.status.live_access_enabled,
        }

    def normalize_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return normalize_odds_payload(payload, source=self.provider)

    def build_snapshot(self, payloads: Iterable[Mapping[str, Any]]) -> OddsDataSnapshot:
        records = tuple(build_odds_record(payload, source=self.provider) for payload in payloads)
        return OddsDataSnapshot(provider=self.provider, records=records)

    def fetch_odds(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError("odds_data connector is inert until live access is explicitly enabled")

    def fetch_events(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError("odds_data connector is inert until live access is explicitly enabled")

    def fetch_snapshot(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError("odds_data connector is inert until live access is explicitly enabled")


def build_odds_data_read_only_client() -> OddsDataReadOnlyClient:
    return OddsDataReadOnlyClient()

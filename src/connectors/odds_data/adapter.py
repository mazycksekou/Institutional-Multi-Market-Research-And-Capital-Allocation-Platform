from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from ..errors import ConnectorDisabledError
from .client import OddsDataReadOnlyClient, build_odds_data_read_only_client
from .models import OddsDataRecord, OddsDataSnapshot
from .payloads import build_odds_record, normalize_odds_payload, validate_odds_payload


@dataclass
class OddsDataConnectorAdapter:
    client: OddsDataReadOnlyClient = field(default_factory=build_odds_data_read_only_client)

    def describe(self) -> dict[str, Any]:
        return {
            "provider": self.client.provider,
            "category": "odds_data",
            "read_only": True,
            "live_access_enabled": False,
        }

    def normalize_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return normalize_odds_payload(payload, source=self.client.provider)

    def build_record(self, payload: Mapping[str, Any]) -> OddsDataRecord:
        return build_odds_record(payload, source=self.client.provider)

    def build_snapshot(self, payloads: Iterable[Mapping[str, Any]]) -> OddsDataSnapshot:
        return self.client.build_snapshot(payloads)

    def validate_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return validate_odds_payload(payload)

    def fetch_odds(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError("odds_data adapter is inert until live access is explicitly enabled")

    def fetch_events(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError("odds_data adapter is inert until live access is explicitly enabled")

    def fetch_snapshot(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError("odds_data adapter is inert until live access is explicitly enabled")

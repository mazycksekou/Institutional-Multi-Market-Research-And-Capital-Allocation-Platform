from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from ..errors import ConnectorDisabledError
from .models import PredictionMarketConnectorStatus, PredictionMarketSnapshot
from .payloads import build_prediction_market_record, normalize_prediction_market_payload


@dataclass(frozen=True)
class PredictionMarketReadOnlyClient:
    provider: str = "prediction_market_data"
    read_only: bool = True
    status: PredictionMarketConnectorStatus = field(default_factory=PredictionMarketConnectorStatus)

    def describe(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "read_only": self.read_only,
            "status": self.status.status,
            "live_access_enabled": self.status.live_access_enabled,
        }

    def normalize_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return normalize_prediction_market_payload(payload, source=self.provider)

    def build_snapshot(self, payloads: Iterable[Mapping[str, Any]]) -> PredictionMarketSnapshot:
        records = tuple(build_prediction_market_record(payload, source=self.provider) for payload in payloads)
        return PredictionMarketSnapshot(provider=self.provider, records=records)

    def fetch_markets(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError("prediction_market_data connector is inert until live access is explicitly enabled")

    def fetch_events(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError("prediction_market_data connector is inert until live access is explicitly enabled")

    def fetch_snapshot(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError("prediction_market_data connector is inert until live access is explicitly enabled")


def build_prediction_market_read_only_client() -> PredictionMarketReadOnlyClient:
    return PredictionMarketReadOnlyClient()

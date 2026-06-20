from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from ..errors import ConnectorDisabledError
from .client import PredictionMarketReadOnlyClient, build_prediction_market_read_only_client
from .models import PredictionMarketRecord, PredictionMarketSnapshot
from .payloads import build_prediction_market_record, normalize_prediction_market_payload, validate_prediction_market_payload


@dataclass
class PredictionMarketConnectorAdapter:
    client: PredictionMarketReadOnlyClient = field(default_factory=build_prediction_market_read_only_client)

    def describe(self) -> dict[str, Any]:
        return {
            "provider": self.client.provider,
            "category": "prediction_market_data",
            "read_only": True,
            "live_access_enabled": False,
        }

    def normalize_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return normalize_prediction_market_payload(payload, source=self.client.provider)

    def build_record(self, payload: Mapping[str, Any]) -> PredictionMarketRecord:
        return build_prediction_market_record(payload, source=self.client.provider)

    def build_snapshot(self, payloads: Iterable[Mapping[str, Any]]) -> PredictionMarketSnapshot:
        return self.client.build_snapshot(payloads)

    def validate_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return validate_prediction_market_payload(payload)

    def fetch_markets(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError("prediction_market_data adapter is inert until live access is explicitly enabled")

    def fetch_events(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError("prediction_market_data adapter is inert until live access is explicitly enabled")

    def fetch_snapshot(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError("prediction_market_data adapter is inert until live access is explicitly enabled")

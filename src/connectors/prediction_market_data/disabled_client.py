from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..errors import ConnectorDisabledError


@dataclass(frozen=True)
class PredictionMarketDisabledLiveClient:
    provider: str = "prediction_market_data"
    read_only: bool = True
    live_access_enabled: bool = False
    message: str = "live client is disabled until live access is explicitly enabled"

    def describe(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "read_only": self.read_only,
            "live_access_enabled": self.live_access_enabled,
            "message": self.message,
        }

    def request(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError(
            "prediction_market_data live client is disabled until live access is explicitly enabled"
        )

    def fetch_markets(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError(
            "prediction_market_data live client is disabled until live access is explicitly enabled"
        )

    def fetch_events(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError(
            "prediction_market_data live client is disabled until live access is explicitly enabled"
        )

    def fetch_snapshot(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError(
            "prediction_market_data live client is disabled until live access is explicitly enabled"
        )

    def sign_request(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError(
            "prediction_market_data live client is disabled until live access is explicitly enabled"
        )


def build_prediction_market_disabled_live_client() -> PredictionMarketDisabledLiveClient:
    return PredictionMarketDisabledLiveClient()

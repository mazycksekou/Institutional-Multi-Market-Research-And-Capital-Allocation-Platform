from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..errors import ConnectorDisabledError


@dataclass(frozen=True)
class PredictionMarketConnectorTransport:
    provider: str = "prediction_market_data"
    read_only: bool = True
    live_access_enabled: bool = False
    credential_names: tuple[str, ...] = (
        "PREDICTION_MARKET_API_KEY",
        "PREDICTION_MARKET_PRIVATE_KEY",
    )
    description: str = "transport is inert until live access is explicitly enabled"

    def describe(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "read_only": self.read_only,
            "live_access_enabled": self.live_access_enabled,
            "credential_names": list(self.credential_names),
            "description": self.description,
        }

    def request(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError(
            "prediction_market_data transport is disabled until live access is explicitly enabled"
        )

    def fetch_markets(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError(
            "prediction_market_data transport is disabled until live access is explicitly enabled"
        )

    def fetch_events(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError(
            "prediction_market_data transport is disabled until live access is explicitly enabled"
        )

    def fetch_snapshot(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectorDisabledError(
            "prediction_market_data transport is disabled until live access is explicitly enabled"
        )


def build_prediction_market_transport(
    *,
    provider: str = "prediction_market_data",
    read_only: bool = True,
    live_access_enabled: bool = False,
    credential_names: tuple[str, ...] = (
        "PREDICTION_MARKET_API_KEY",
        "PREDICTION_MARKET_PRIVATE_KEY",
    ),
    description: str = "transport is inert until live access is explicitly enabled",
) -> PredictionMarketConnectorTransport:
    return PredictionMarketConnectorTransport(
        provider=provider,
        read_only=read_only,
        live_access_enabled=live_access_enabled,
        credential_names=credential_names,
        description=description,
    )

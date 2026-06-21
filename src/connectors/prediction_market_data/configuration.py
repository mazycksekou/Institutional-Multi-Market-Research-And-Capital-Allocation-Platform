from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


PREDICTION_MARKET_CONNECTOR_CATEGORY = "prediction_market_data"


@dataclass(frozen=True)
class PredictionMarketConnectorConfiguration:
    provider: str = PREDICTION_MARKET_CONNECTOR_CATEGORY
    live_access_enabled: bool = False
    read_only: bool = True
    credential_names: tuple[str, ...] = (
        "PREDICTION_MARKET_API_KEY",
        "PREDICTION_MARKET_PRIVATE_KEY",
    )
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def describe(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "live_access_enabled": self.live_access_enabled,
            "read_only": self.read_only,
            "credential_names": list(self.credential_names),
            "metadata": dict(self.metadata),
        }


def build_prediction_market_connector_configuration(
    *,
    provider: str = PREDICTION_MARKET_CONNECTOR_CATEGORY,
    live_access_enabled: bool = False,
    read_only: bool = True,
    credential_names: tuple[str, ...] = (
        "PREDICTION_MARKET_API_KEY",
        "PREDICTION_MARKET_PRIVATE_KEY",
    ),
    metadata: Mapping[str, Any] | None = None,
) -> PredictionMarketConnectorConfiguration:
    return PredictionMarketConnectorConfiguration(
        provider=provider,
        live_access_enabled=live_access_enabled,
        read_only=read_only,
        credential_names=credential_names,
        metadata={} if metadata is None else dict(metadata),
    )

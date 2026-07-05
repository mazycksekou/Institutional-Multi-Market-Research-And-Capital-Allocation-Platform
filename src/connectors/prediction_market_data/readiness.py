from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PredictionMarketConnectorReadiness:
    provider: str = "prediction_market_data"
    status: str = "disabled"
    read_only: bool = True
    live_access_enabled: bool = False
    credential_names: tuple[str, ...] = (
        "PREDICTION_MARKET_API_KEY",
        "PREDICTION_MARKET_PRIVATE_KEY",
    )
    message: str = "connector wrapper is inert until live access is explicitly enabled"

    def describe(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "status": self.status,
            "read_only": self.read_only,
            "live_access_enabled": self.live_access_enabled,
            "credential_names": list(self.credential_names),
            "message": self.message,
        }


def describe_prediction_market_connector_readiness() -> dict[str, Any]:
    return PredictionMarketConnectorReadiness().describe()

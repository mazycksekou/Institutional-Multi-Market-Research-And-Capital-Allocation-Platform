from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..errors import ConnectorDisabledError


@dataclass(frozen=True)
class PredictionMarketSigningBoundary:
    credential_names: tuple[str, ...] = (
        "PREDICTION_MARKET_API_KEY",
        "PREDICTION_MARKET_PRIVATE_KEY",
    )
    live_signing_enabled: bool = False
    description: str = "request signing is disabled until live access is explicitly enabled"

    def describe(self) -> dict[str, object]:
        return {
            "credential_names": list(self.credential_names),
            "live_signing_enabled": self.live_signing_enabled,
            "description": self.description,
        }


def build_prediction_market_signing_boundary(
    credential_names: tuple[str, ...] = (
        "PREDICTION_MARKET_API_KEY",
        "PREDICTION_MARKET_PRIVATE_KEY",
    ),
    *,
    live_signing_enabled: bool = False,
) -> PredictionMarketSigningBoundary:
    return PredictionMarketSigningBoundary(
        credential_names=credential_names,
        live_signing_enabled=live_signing_enabled,
    )


def sign_prediction_market_request(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
    raise ConnectorDisabledError(
        "prediction_market_data request signing is disabled until live access is explicitly enabled"
    )

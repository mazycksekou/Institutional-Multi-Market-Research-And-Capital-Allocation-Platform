from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PredictionMarketAuthRequirement:
    credential_names: tuple[str, ...] = (
        "PREDICTION_MARKET_API_KEY",
        "PREDICTION_MARKET_PRIVATE_KEY",
    )
    live_access_enabled: bool = False
    description: str = "credential names are declared only; secrets are never read at import time"

    def describe(self) -> dict[str, object]:
        return {
            "credential_names": list(self.credential_names),
            "live_access_enabled": self.live_access_enabled,
            "description": self.description,
        }


def build_prediction_market_auth_requirement(
    credential_names: tuple[str, ...] = (
        "PREDICTION_MARKET_API_KEY",
        "PREDICTION_MARKET_PRIVATE_KEY",
    ),
    *,
    live_access_enabled: bool = False,
) -> PredictionMarketAuthRequirement:
    return PredictionMarketAuthRequirement(
        credential_names=credential_names,
        live_access_enabled=live_access_enabled,
    )

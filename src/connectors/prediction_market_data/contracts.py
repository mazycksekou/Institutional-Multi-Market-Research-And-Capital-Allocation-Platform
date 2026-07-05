from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

PREDICTION_MARKET_DATA_CONNECTOR_CATEGORY = "prediction_market_data"


@dataclass(frozen=True)
class PredictionMarketDataConnectorContract:
    name: str
    description: str = ""
    supports_live_access: bool = False
    supports_credentials: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)


def build_prediction_market_data_connector_contract(
    name: str,
    description: str = "",
    *,
    supports_live_access: bool = False,
    supports_credentials: bool = False,
    metadata: Mapping[str, Any] | None = None,
) -> PredictionMarketDataConnectorContract:
    return PredictionMarketDataConnectorContract(
        name=name,
        description=description,
        supports_live_access=supports_live_access,
        supports_credentials=supports_credentials,
        metadata={} if metadata is None else dict(metadata),
    )

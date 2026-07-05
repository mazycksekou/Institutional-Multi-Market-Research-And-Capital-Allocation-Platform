from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class PredictionMarketRecord:
    provider: str
    market_id: str = ""
    event_id: str = ""
    title: str = ""
    payload: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PredictionMarketSnapshot:
    provider: str = "prediction_market_data"
    records: tuple[PredictionMarketRecord, ...] = ()
    status: str = "inert"
    read_only: bool = True


@dataclass(frozen=True)
class PredictionMarketConnectorStatus:
    provider: str = "prediction_market_data"
    status: str = "disabled"
    read_only: bool = True
    live_access_enabled: bool = False
    message: str = "connector wrapper is inert until live access is explicitly authorized"

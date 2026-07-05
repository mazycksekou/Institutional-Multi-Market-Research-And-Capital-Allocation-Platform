from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class MarketDataQuote:
    provider: str
    symbol: str = ""
    asset_class: str = ""
    exchange: str = ""
    quote_type: str = "quote"
    payload: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MarketDataSnapshot:
    provider: str = "market_data"
    records: tuple[MarketDataQuote, ...] = ()
    status: str = "inert"
    read_only: bool = True


@dataclass(frozen=True)
class MarketDataConnectorStatus:
    provider: str = "market_data"
    status: str = "disabled"
    read_only: bool = True
    live_access_enabled: bool = False
    message: str = "connector wrapper is inert until live access is explicitly authorized"

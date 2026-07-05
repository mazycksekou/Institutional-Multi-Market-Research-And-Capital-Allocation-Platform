from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(slots=True)
class ZeroDteStockQuote:
    provider: str = "zero_dte_stocks"
    provider_type: str = "stock_price"
    symbol: str | None = None
    price: Any = None
    bid: Any = None
    ask: Any = None
    volume: Any = None
    timestamp: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any], *, provider: str = "zero_dte_stocks") -> "ZeroDteStockQuote":
        return cls(
            provider=provider,
            provider_type="stock_price",
            symbol=payload.get("symbol"),
            price=payload.get("price"),
            bid=payload.get("bid"),
            ask=payload.get("ask"),
            volume=payload.get("volume"),
            timestamp=payload.get("timestamp"),
            raw=dict(payload),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "provider_type": self.provider_type,
            "symbol": self.symbol,
            "price": self.price,
            "bid": self.bid,
            "ask": self.ask,
            "volume": self.volume,
            "timestamp": self.timestamp,
            "raw": dict(self.raw),
        }


@dataclass(slots=True)
class ZeroDteStockSnapshot:
    provider: str = "zero_dte_stocks"
    provider_type: str = "stock_price"
    quotes: tuple[ZeroDteStockQuote, ...] = ()
    status: str = "read_only"
    read_only: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "provider_type": self.provider_type,
            "quotes": [quote.as_dict() for quote in self.quotes],
            "status": self.status,
            "read_only": self.read_only,
        }


@dataclass(slots=True)
class ZeroDteStockProviderStatus:
    provider: str = "zero_dte_stocks"
    provider_type: str = "stock_price"
    status: str = "read_only"
    read_only: bool = True
    live_access_enabled: bool = False
    message: str = "zero_dte_stocks provider is read-only and consumes supplied market-data payloads only"

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(slots=True)
class PredictionMarketEventQuote:
    provider: str = "prediction_market"
    provider_type: str = "prediction_market"
    event_ticker: str | None = None
    series_ticker: str | None = None
    title: str | None = None
    category: str | None = None
    status: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any], *, provider: str = "prediction_market") -> "PredictionMarketEventQuote":
        return cls(
            provider=provider,
            provider_type="prediction_market",
            event_ticker=payload.get("event_ticker") or payload.get("ticker"),
            series_ticker=payload.get("series_ticker"),
            title=payload.get("title"),
            category=payload.get("category"),
            status=payload.get("status"),
            raw=dict(payload),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "provider_type": self.provider_type,
            "event_ticker": self.event_ticker,
            "series_ticker": self.series_ticker,
            "title": self.title,
            "category": self.category,
            "status": self.status,
            "raw": dict(self.raw),
        }


@dataclass(slots=True)
class PredictionMarketQuote:
    provider: str = "prediction_market"
    provider_type: str = "prediction_market"
    market_type: str = "prediction_market"
    ticker: str | None = None
    market_ticker: str | None = None
    event_ticker: str | None = None
    title: str | None = None
    subtitle: str | None = None
    status: str | None = None
    yes_bid: float | None = None
    yes_ask: float | None = None
    no_bid: float | None = None
    no_ask: float | None = None
    last_price: float | None = None
    mid_probability: float | None = None
    implied_probability_yes: float | None = None
    liquidity: Any = None
    volume: Any = None
    close_time: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, Any],
        *,
        provider: str = "prediction_market",
        market_type: str = "prediction_market",
    ) -> "PredictionMarketQuote":
        return cls(
            provider=provider,
            provider_type="prediction_market",
            market_type=market_type,
            ticker=payload.get("ticker") or payload.get("market_ticker"),
            market_ticker=payload.get("market_ticker") or payload.get("ticker"),
            event_ticker=payload.get("event_ticker"),
            title=payload.get("title"),
            subtitle=payload.get("subtitle"),
            status=payload.get("status"),
            yes_bid=payload.get("yes_bid"),
            yes_ask=payload.get("yes_ask"),
            no_bid=payload.get("no_bid"),
            no_ask=payload.get("no_ask"),
            last_price=payload.get("last_price"),
            mid_probability=payload.get("mid_probability"),
            implied_probability_yes=payload.get("implied_probability_yes"),
            liquidity=payload.get("liquidity"),
            volume=payload.get("volume"),
            close_time=payload.get("close_time"),
            raw=dict(payload),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "provider_type": self.provider_type,
            "market_type": self.market_type,
            "ticker": self.ticker,
            "market_ticker": self.market_ticker,
            "event_ticker": self.event_ticker,
            "title": self.title,
            "subtitle": self.subtitle,
            "status": self.status,
            "yes_bid": self.yes_bid,
            "yes_ask": self.yes_ask,
            "no_bid": self.no_bid,
            "no_ask": self.no_ask,
            "last_price": self.last_price,
            "mid_probability": self.mid_probability,
            "implied_probability_yes": self.implied_probability_yes,
            "liquidity": self.liquidity,
            "volume": self.volume,
            "close_time": self.close_time,
            "raw": dict(self.raw),
        }

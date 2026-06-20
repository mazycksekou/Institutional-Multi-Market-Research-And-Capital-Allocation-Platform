from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..base import ProviderAdapterBase
from ..contracts import ProviderContract
from ..health import build_scaffold_health_status
from ..validation import validate_provider_payload
from .contracts import build_prediction_market_provider_contract
from .models import PredictionMarketEventQuote, PredictionMarketQuote

PREDICTION_MARKET_PROVIDER_TYPE = "prediction_market"


def _prob(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number > 1:
        number = number / 100
    return max(0.0, min(1.0, number))


def normalize_prediction_market_event(payload: Mapping[str, Any], *, provider: str = "prediction_market") -> dict[str, Any]:
    return PredictionMarketEventQuote.from_mapping(payload, provider=provider).as_dict()


def normalize_prediction_market_quote(
    payload: Mapping[str, Any],
    *,
    provider: str = "prediction_market",
    market_type: str = "prediction_market",
) -> dict[str, Any]:
    yes_bid = _prob(payload.get("yes_bid"))
    yes_ask = _prob(payload.get("yes_ask"))
    no_bid = _prob(payload.get("no_bid"))
    no_ask = _prob(payload.get("no_ask"))
    last_price = _prob(payload.get("last_price"))
    mid_probability = None
    if yes_bid is not None and yes_ask is not None:
        mid_probability = (yes_bid + yes_ask) / 2
    elif yes_ask is not None:
        mid_probability = yes_ask
    elif yes_bid is not None:
        mid_probability = yes_bid
    return {
        "provider": provider,
        "provider_type": PREDICTION_MARKET_PROVIDER_TYPE,
        "market_type": market_type,
        "ticker": payload.get("ticker") or payload.get("market_ticker"),
        "event_ticker": payload.get("event_ticker"),
        "title": payload.get("title"),
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "no_bid": no_bid,
        "no_ask": no_ask,
        "mid_probability": mid_probability,
        "liquidity": payload.get("liquidity"),
        "volume": payload.get("volume"),
        "raw": dict(payload),
    }


def normalize_prediction_market_snapshot(
    payload: Mapping[str, Any],
    *,
    provider: str = "prediction_market",
    market_type: str = "prediction_market",
) -> dict[str, Any]:
    yes_bid = _prob(payload.get("yes_bid"))
    yes_ask = _prob(payload.get("yes_ask"))
    no_bid = _prob(payload.get("no_bid"))
    no_ask = _prob(payload.get("no_ask"))
    last_price = _prob(payload.get("last_price"))
    implied_probability_yes = payload.get("implied_probability_yes")
    if implied_probability_yes is None:
        implied_probability_yes = yes_ask if yes_ask is not None else yes_bid if yes_bid is not None else last_price
    return {
        "provider": provider,
        "provider_type": PREDICTION_MARKET_PROVIDER_TYPE,
        "market_type": market_type,
        "market_ticker": payload.get("market_ticker") or payload.get("ticker"),
        "event_ticker": payload.get("event_ticker"),
        "title": payload.get("title"),
        "subtitle": payload.get("subtitle"),
        "status": payload.get("status"),
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "no_bid": no_bid,
        "no_ask": no_ask,
        "last_price": last_price,
        "volume": payload.get("volume"),
        "liquidity": payload.get("liquidity"),
        "close_time": payload.get("close_time"),
        "implied_probability_yes": implied_probability_yes,
        "raw": dict(payload),
    }


def build_prediction_market_event_quote(
    payload: Mapping[str, Any],
    *,
    provider: str = "prediction_market",
) -> PredictionMarketEventQuote:
    return PredictionMarketEventQuote.from_mapping(payload, provider=provider)


def build_prediction_market_quote(
    payload: Mapping[str, Any],
    *,
    provider: str = "prediction_market",
    market_type: str = "prediction_market",
) -> PredictionMarketQuote:
    return PredictionMarketQuote.from_mapping(
        normalize_prediction_market_quote(payload, provider=provider, market_type=market_type),
        provider=provider,
        market_type=market_type,
    )


def build_prediction_market_snapshot(
    payload: Mapping[str, Any],
    *,
    provider: str = "prediction_market",
    market_type: str = "prediction_market",
) -> PredictionMarketQuote:
    return PredictionMarketQuote.from_mapping(
        normalize_prediction_market_snapshot(payload, provider=provider, market_type=market_type),
        provider=provider,
        market_type=market_type,
    )


class PredictionMarketProviderAdapter(ProviderAdapterBase):
    def __init__(self, contract: ProviderContract | Mapping[str, Any] | None = None) -> None:
        super().__init__(contract or build_prediction_market_provider_contract())

    def build_event_quote(self, payload: Mapping[str, Any], *, provider: str | None = None) -> PredictionMarketEventQuote:
        return build_prediction_market_event_quote(payload, provider=provider or "prediction_market")

    def build_quote(
        self,
        payload: Mapping[str, Any],
        *,
        provider: str | None = None,
        market_type: str | None = None,
    ) -> PredictionMarketQuote:
        return build_prediction_market_quote(
            payload,
            provider=provider or "prediction_market",
            market_type=market_type or "prediction_market",
        )

    def normalize_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return normalize_prediction_market_quote(payload, provider="prediction_market", market_type="prediction_market")

    def validate_payload(self, payload: Mapping[str, Any], max_staleness_seconds: int = 3600 * 12) -> dict[str, Any]:
        return validate_provider_payload(
            PREDICTION_MARKET_PROVIDER_TYPE,
            dict(payload),
            max_staleness_seconds=max_staleness_seconds,
        )

    def health_check(self) -> dict[str, Any]:
        return build_scaffold_health_status(
            self.contract.provider_id,
            provider_name=self.contract.provider_name,
            provider_type=self.contract.provider_type,
            blockers=("read_only_category_adapter",),
        ).as_dict()


__all__ = [
    "PREDICTION_MARKET_PROVIDER_TYPE",
    "PredictionMarketEventQuote",
    "PredictionMarketProviderAdapter",
    "PredictionMarketQuote",
    "build_prediction_market_event_quote",
    "build_prediction_market_quote",
    "build_prediction_market_snapshot",
    "normalize_prediction_market_event",
    "normalize_prediction_market_quote",
    "normalize_prediction_market_snapshot",
]

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from ..base import ProviderAdapterBase
from ..contracts import ProviderContract
from ..health import build_scaffold_health_status
from ..validation import validate_provider_payload
from .contracts import build_prediction_market_provider_contract
from .models import PredictionMarketEventQuote, PredictionMarketQuote

PREDICTION_MARKET_PROVIDER_TYPE = "prediction_market"


def _value(payload: Mapping[str, Any], *paths: Any) -> Any:
    for path in paths:
        current: Any = payload
        if isinstance(path, tuple):
            for key in path:
                if not isinstance(current, Mapping):
                    current = None
                    break
                current = current.get(key)
                if current in (None, ""):
                    break
            if current not in (None, ""):
                return current
            continue
        current = payload.get(path)
        if current not in (None, ""):
            return current
    return None


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


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _common_market_fields(payload: Mapping[str, Any]) -> dict[str, Any]:
    yes_bid = _prob(_value(payload, "yes_bid", "yesBid", "bid_yes", ("pricing", "yes_bid"), ("pricing", "yesBid"), ("prices", "yes_bid"), ("market", "yes_bid"), "yes_bid_dollars"))
    yes_ask = _prob(_value(payload, "yes_ask", "yesAsk", "ask_yes", ("pricing", "yes_ask"), ("pricing", "yesAsk"), ("prices", "yes_ask"), ("market", "yes_ask"), "yes_ask_dollars"))
    no_bid = _prob(_value(payload, "no_bid", "noBid", "bid_no", ("pricing", "no_bid"), ("pricing", "noBid"), ("prices", "no_bid"), ("market", "no_bid"), "no_bid_dollars"))
    no_ask = _prob(_value(payload, "no_ask", "noAsk", "ask_no", ("pricing", "no_ask"), ("pricing", "noAsk"), ("prices", "no_ask"), ("market", "no_ask"), "no_ask_dollars"))
    yes_price = _prob(_value(payload, "yes_price", "yesPrice", "last_price", "lastPrice", "last_price_dollars", ("pricing", "yes_price"), ("prices", "yes_price"), ("market", "yes_price")))
    no_price = _prob(_value(payload, "no_price", "noPrice", ("pricing", "no_price"), ("prices", "no_price"), ("market", "no_price"), "no_price_dollars"))
    price_signals = [yes_price, no_price, yes_bid, yes_ask, no_bid, no_ask]
    has_price_signal = any(value is not None for value in price_signals)
    volume = _value(payload, "volume", "volume_fp", "volumeFp")
    open_interest = _value(payload, "open_interest", "openInterest", "open_interest_fp", "openInterestFp")
    liquidity_score = _value(payload, "liquidity_score", "liquidityScore")
    if liquidity_score is None and volume is not None:
        liquidity_score = volume
    return {
        "market_id": _value(payload, "market_id", "marketId", "market_ticker", "marketTicker", "ticker", "contract_id", "contractId"),
        "event_id": _value(payload, "event_id", "eventId", "event_ticker", "eventTicker", "market_id", "marketId", "ticker"),
        "contract_id": _value(payload, "contract_id", "contractId", "ticker", "market_ticker", "marketTicker", "market_id", "marketId"),
        "contract_title": _value(payload, "contract_title", "contractTitle", "title", "name"),
        "event_title": _value(payload, "event_title", "eventTitle", "title", "name"),
        "status": _value(payload, "status", "market_status", "marketStatus"),
        "close_time": _value(payload, "close_time", "expiration_time", "closeTime", "market_close_at"),
        "timestamp": _value(payload, "timestamp", "received_at", "created_at", "updated_at") or _now_iso(),
        "source_payload_redacted": _value(payload, "source_payload_redacted", "sourcePayloadRedacted"),
        "source_type": _value(payload, "source_type", "sourceType") or "prediction_market",
        "market_type": _value(payload, "market_type", "marketType", "source_type", "sourceType") or "prediction_market",
        "implied_probability": _value(payload, "implied_probability", "implied_probability_yes", "impliedProbability", "yes_price", "yesPrice", "last_price", "lastPrice", "last_price_dollars")
        or yes_price
        or yes_ask
        or yes_bid,
        "yes_price": yes_price,
        "no_price": no_price,
        "pricing_quality_score": _value(payload, "pricing_quality_score", "pricingQualityScore") if _value(payload, "pricing_quality_score", "pricingQualityScore") is not None else (100.0 if has_price_signal else 0.0),
        "liquidity_score": liquidity_score,
        "volume": volume,
        "open_interest": open_interest,
        "liquidity_tier": _value(payload, "liquidity_tier", "liquidityTier"),
        "price_source": _value(payload, "price_source", "priceSource") or "read_only_payload",
    }


def normalize_prediction_market_event(payload: Mapping[str, Any], *, provider: str = "prediction_market") -> dict[str, Any]:
    return PredictionMarketEventQuote.from_mapping(payload, provider=provider).as_dict()


def normalize_prediction_market_quote(
    payload: Mapping[str, Any],
    *,
    provider: str = "prediction_market",
    market_type: str = "prediction_market",
) -> dict[str, Any]:
    yes_bid = _prob(_value(payload, "yes_bid", "yesBid", "bid_yes", ("pricing", "yes_bid"), ("pricing", "yesBid"), ("prices", "yes_bid"), ("market", "yes_bid"), "yes_bid_dollars"))
    yes_ask = _prob(_value(payload, "yes_ask", "yesAsk", "ask_yes", ("pricing", "yes_ask"), ("pricing", "yesAsk"), ("prices", "yes_ask"), ("market", "yes_ask"), "yes_ask_dollars"))
    no_bid = _prob(_value(payload, "no_bid", "noBid", "bid_no", ("pricing", "no_bid"), ("pricing", "noBid"), ("prices", "no_bid"), ("market", "no_bid"), "no_bid_dollars"))
    no_ask = _prob(_value(payload, "no_ask", "noAsk", "ask_no", ("pricing", "no_ask"), ("pricing", "noAsk"), ("prices", "no_ask"), ("market", "no_ask"), "no_ask_dollars"))
    last_price = _prob(_value(payload, "last_price", "lastPrice", "last_price_dollars"))
    mid_probability = None
    if yes_bid is not None and yes_ask is not None:
        mid_probability = (yes_bid + yes_ask) / 2
    elif yes_ask is not None:
        mid_probability = yes_ask
    elif yes_bid is not None:
        mid_probability = yes_bid
    normalized = {
        "provider": provider,
        "provider_type": PREDICTION_MARKET_PROVIDER_TYPE,
        "market_type": market_type,
        "ticker": _value(payload, "ticker", "market_ticker", "marketTicker"),
        "event_ticker": _value(payload, "event_ticker", "eventTicker"),
        "title": _value(payload, "title", "event_title", "eventTitle"),
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "no_bid": no_bid,
        "no_ask": no_ask,
        "mid_probability": mid_probability,
        "liquidity": _value(payload, "liquidity"),
        "volume": _value(payload, "volume", "volume_fp", "volumeFp"),
        "open_interest": _value(payload, "open_interest", "openInterest", "open_interest_fp", "openInterestFp"),
        "timestamp": _value(payload, "timestamp", "received_at", "created_at", "updated_at") or _now_iso(),
        "raw": dict(payload),
    }
    normalized.update(_common_market_fields(payload))
    return normalized


def normalize_prediction_market_snapshot(
    payload: Mapping[str, Any],
    *,
    provider: str = "prediction_market",
    market_type: str = "prediction_market",
) -> dict[str, Any]:
    yes_bid = _prob(_value(payload, "yes_bid", "yesBid", "bid_yes", ("pricing", "yes_bid"), ("pricing", "yesBid"), ("prices", "yes_bid"), ("market", "yes_bid"), "yes_bid_dollars"))
    yes_ask = _prob(_value(payload, "yes_ask", "yesAsk", "ask_yes", ("pricing", "yes_ask"), ("pricing", "yesAsk"), ("prices", "yes_ask"), ("market", "yes_ask"), "yes_ask_dollars"))
    no_bid = _prob(_value(payload, "no_bid", "noBid", "bid_no", ("pricing", "no_bid"), ("pricing", "noBid"), ("prices", "no_bid"), ("market", "no_bid"), "no_bid_dollars"))
    no_ask = _prob(_value(payload, "no_ask", "noAsk", "ask_no", ("pricing", "no_ask"), ("pricing", "noAsk"), ("prices", "no_ask"), ("market", "no_ask"), "no_ask_dollars"))
    last_price = _prob(_value(payload, "last_price", "lastPrice", "last_price_dollars"))
    implied_probability_yes = _value(payload, "implied_probability_yes", "impliedProbabilityYes", "implied_probability", "impliedProbability")
    if implied_probability_yes is None:
        implied_probability_yes = yes_ask if yes_ask is not None else yes_bid if yes_bid is not None else last_price
    normalized = {
        "provider": provider,
        "provider_type": PREDICTION_MARKET_PROVIDER_TYPE,
        "market_type": market_type,
        "market_ticker": _value(payload, "market_ticker", "marketTicker", "ticker"),
        "event_ticker": _value(payload, "event_ticker", "eventTicker"),
        "title": _value(payload, "title", "event_title", "eventTitle"),
        "subtitle": _value(payload, "subtitle", "subTitle"),
        "status": _value(payload, "status", "market_status", "marketStatus"),
        "yes_bid": yes_bid,
        "yes_ask": yes_ask,
        "no_bid": no_bid,
        "no_ask": no_ask,
        "last_price": last_price,
        "volume": _value(payload, "volume", "volume_fp", "volumeFp"),
        "open_interest": _value(payload, "open_interest", "openInterest", "open_interest_fp", "openInterestFp"),
        "liquidity": _value(payload, "liquidity"),
        "close_time": _value(payload, "close_time", "expiration_time", "closeTime", "market_close_at"),
        "timestamp": _value(payload, "timestamp", "received_at", "created_at", "updated_at") or _now_iso(),
        "implied_probability_yes": implied_probability_yes,
        "raw": dict(payload),
    }
    normalized.update(_common_market_fields(payload))
    return normalized


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

from typing import Any

from src.core.math_utils import (
    american_to_decimal as _core_american_to_decimal,
    american_to_implied_probability as _core_american_to_implied_probability,
)
from src.providers.prediction_markets.adapters import (
    normalize_prediction_market_event as _normalize_prediction_market_event,
    normalize_prediction_market_quote as _normalize_prediction_market_quote,
    normalize_prediction_market_snapshot as _normalize_prediction_market_snapshot,
)
from src.providers.sportsbooks.adapters import (
    normalize_sportsbook_event as _normalize_sportsbook_event,
    normalize_sportsbook_odds as _normalize_sportsbook_odds,
)


def american_to_decimal(odds: int | float) -> float:
    return _core_american_to_decimal(odds)


def implied_probability_from_american(odds: int | float) -> float:
    return _core_american_to_implied_probability(odds)


def normalize_sportsbook_event(provider: str, event: dict[str, Any], league: str | None = None) -> dict[str, Any]:
    return _normalize_sportsbook_event(provider, event, league=league)


def normalize_sportsbook_odds(
    provider: str,
    event_id: str,
    sport_key: str | None,
    market: str | None,
    sportsbook: str | None,
    selection: str | None,
    price_american: Any,
    point: Any,
    last_update: Any,
    raw: dict[str, Any],
) -> dict[str, Any]:
    return _normalize_sportsbook_odds(
        provider,
        event_id,
        sport_key,
        market,
        sportsbook,
        selection,
        price_american,
        point,
        last_update,
        raw,
    )


def normalize_kalshi_event(event: dict[str, Any]) -> dict[str, Any]:
    return _normalize_prediction_market_event(event, provider="kalshi")


def normalize_kalshi_market(market: dict[str, Any]) -> dict[str, Any]:
    return _normalize_prediction_market_snapshot(market, provider="kalshi", market_type="kalshi_prediction_market")

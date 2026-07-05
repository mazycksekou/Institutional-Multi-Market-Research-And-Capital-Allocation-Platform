from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.core.math_utils import american_to_decimal, american_to_implied_probability

from ..base import ProviderAdapterBase
from ..contracts import ProviderContract
from ..health import build_scaffold_health_status
from ..validation import validate_provider_payload
from .contracts import build_sportsbook_provider_contract
from .models import SportsbookEventQuote, SportsbookQuote

SPORTSBOOK_PROVIDER_TYPE = "sportsbook_odds"


def normalize_sportsbook_event(provider: str, event: Mapping[str, Any], league: str | None = None) -> dict[str, Any]:
    normalized = SportsbookEventQuote.from_mapping(
        {**dict(event), "league": league or event.get("sport_title") or event.get("league")},
        provider=provider,
    )
    return normalized.as_dict()


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
    raw: Mapping[str, Any],
) -> dict[str, Any]:
    decimal = american_to_decimal(price_american) if isinstance(price_american, (int, float)) else None
    implied = american_to_implied_probability(price_american) if isinstance(price_american, (int, float)) else None
    quote = SportsbookQuote.from_mapping(
        {
            "provider_event_id": event_id,
            "sport_key": sport_key,
            "market": market,
            "sportsbook": sportsbook,
            "selection": selection,
            "price_american": price_american,
            "price_decimal": decimal,
            "implied_probability": implied,
            "point": point,
            "last_update": last_update,
            "raw": dict(raw),
        },
        provider=provider,
    )
    return quote.as_dict()


def build_sportsbook_event_quote(payload: Mapping[str, Any], *, provider: str = "sportsbook") -> SportsbookEventQuote:
    return SportsbookEventQuote.from_mapping(payload, provider=provider)


def build_sportsbook_quote(payload: Mapping[str, Any], *, provider: str = "sportsbook") -> SportsbookQuote:
    return SportsbookQuote.from_mapping(payload, provider=provider)


def normalize_sportsbook_quote(payload: Mapping[str, Any], *, provider: str = "sportsbook") -> dict[str, Any]:
    return build_sportsbook_quote(payload, provider=provider).as_dict()


class SportsbookProviderAdapter(ProviderAdapterBase):
    def __init__(self, contract: ProviderContract | Mapping[str, Any] | None = None) -> None:
        super().__init__(contract or build_sportsbook_provider_contract())

    def build_event_quote(self, payload: Mapping[str, Any], *, provider: str | None = None) -> SportsbookEventQuote:
        return build_sportsbook_event_quote(payload, provider=provider or "sportsbook")

    def build_quote(self, payload: Mapping[str, Any], *, provider: str | None = None) -> SportsbookQuote:
        return build_sportsbook_quote(payload, provider=provider or "sportsbook")

    def normalize_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        return normalize_sportsbook_quote(payload, provider="sportsbook")

    def validate_payload(self, payload: Mapping[str, Any], max_staleness_seconds: int = 3600 * 12) -> dict[str, Any]:
        return validate_provider_payload(
            SPORTSBOOK_PROVIDER_TYPE,
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
    "SPORTSBOOK_PROVIDER_TYPE",
    "SportsbookEventQuote",
    "SportsbookProviderAdapter",
    "SportsbookQuote",
    "build_sportsbook_event_quote",
    "build_sportsbook_quote",
    "normalize_sportsbook_event",
    "normalize_sportsbook_odds",
    "normalize_sportsbook_quote",
]

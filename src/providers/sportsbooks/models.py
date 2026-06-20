from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(slots=True)
class SportsbookEventQuote:
    provider: str = "sportsbook"
    provider_type: str = "sportsbook_odds"
    provider_event_id: str | None = None
    event_id: str | None = None
    sport_key: str | None = None
    league: str | None = None
    commence_time: str | None = None
    home_team: str | None = None
    away_team: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any], *, provider: str = "sportsbook") -> "SportsbookEventQuote":
        event_id = payload.get("id") or payload.get("event_id")
        return cls(
            provider=provider,
            provider_type="sportsbook_odds",
            provider_event_id=event_id,
            event_id=event_id,
            sport_key=payload.get("sport_key"),
            league=payload.get("league") or payload.get("sport_title"),
            commence_time=payload.get("commence_time"),
            home_team=payload.get("home_team"),
            away_team=payload.get("away_team"),
            raw=dict(payload),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "provider_type": self.provider_type,
            "provider_event_id": self.provider_event_id,
            "event_id": self.event_id,
            "id": self.event_id,
            "sport_key": self.sport_key,
            "league": self.league,
            "commence_time": self.commence_time,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "raw": dict(self.raw),
        }


@dataclass(slots=True)
class SportsbookQuote:
    provider: str = "sportsbook"
    provider_type: str = "sportsbook_odds"
    provider_event_id: str | None = None
    sport_key: str | None = None
    market: str | None = None
    sportsbook: str | None = None
    selection: str | None = None
    price_american: Any = None
    price_decimal: float | None = None
    implied_probability: float | None = None
    point: Any = None
    last_update: Any = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any], *, provider: str = "sportsbook") -> "SportsbookQuote":
        return cls(
            provider=provider,
            provider_type="sportsbook_odds",
            provider_event_id=payload.get("provider_event_id"),
            sport_key=payload.get("sport_key"),
            market=payload.get("market"),
            sportsbook=payload.get("sportsbook"),
            selection=payload.get("selection"),
            price_american=payload.get("price_american"),
            price_decimal=payload.get("price_decimal"),
            implied_probability=payload.get("implied_probability"),
            point=payload.get("point"),
            last_update=payload.get("last_update"),
            raw=dict(payload),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "provider_type": self.provider_type,
            "provider_event_id": self.provider_event_id,
            "sport_key": self.sport_key,
            "market": self.market,
            "sportsbook": self.sportsbook,
            "selection": self.selection,
            "price_american": self.price_american,
            "price_decimal": self.price_decimal,
            "implied_probability": self.implied_probability,
            "point": self.point,
            "last_update": self.last_update,
            "raw": dict(self.raw),
        }


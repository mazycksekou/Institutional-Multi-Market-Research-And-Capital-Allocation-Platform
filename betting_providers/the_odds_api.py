import os
import time
from typing import Any, Optional

import httpx

from .aliases import resolve_sport_key
from .base import ProviderAdapter, SPORTSBOOK_ODDS, clean_error, env_bool, provider_not_configured
from .normalization import normalize_sportsbook_event, normalize_sportsbook_odds


class TheOddsApiAdapter(ProviderAdapter):
    id = "the_odds_api"
    name = "The Odds API"
    provider_type = SPORTSBOOK_ODDS

    def __init__(self) -> None:
        self.base_url = os.getenv("ODDS_API_BASE_URL", "https://api.the-odds-api.com/v4").rstrip("/")
        self.api_key = (os.getenv("THE_ODDS_API_KEY") or os.getenv("ODDS_API_KEY") or "").strip()
        self.default_bookmakers = os.getenv(
            "DEFAULT_BOOKMAKERS",
            "draftkings,fanduel,betmgm,caesars,espnbet,bet365",
        )
        self.default_regions = os.getenv("DEFAULT_REGIONS", "us")
        self.default_markets = os.getenv("DEFAULT_MARKETS", "h2h,spreads,totals")
        self._sports_cache: tuple[float, Any] | None = None

    @property
    def enabled(self) -> bool:
        return env_bool("ODDS_API_ENABLED", True)

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.base_url)

    def capability(self) -> dict[str, Any]:
        result = super().capability()
        result.update({
            "supports_sports_list": True,
            "supports_events": True,
            "supports_odds": True,
            "supports_props": False,
            "supports_prediction_markets": False,
        })
        return result

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.configured:
            return provider_not_configured(self.id)
        request_params = {"apiKey": self.api_key, **{k: v for k, v in params.items() if v not in (None, "")}}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}{path}", params=request_params)
        except Exception as error:
            return clean_error("PROVIDER_ERROR", f"The Odds API request failed: {error}", provider=self.id)
        try:
            raw = response.json()
        except ValueError:
            raw = {"text": response.text}
        if not response.is_success:
            return clean_error(
                "PROVIDER_ERROR",
                f"The Odds API returned HTTP {response.status_code}.",
                provider=self.id,
                status_code=response.status_code,
                raw_response=raw,
            )
        return {"ok": True, "provider": self.id, "raw_response": raw, "status_code": response.status_code}

    async def get_supported_sports(self) -> dict[str, Any]:
        if self._sports_cache and time.time() - self._sports_cache[0] < 300:
            return self._sports_cache[1]
        response = await self._get("/sports/", {"all": "true"})
        if not response.get("ok"):
            return response
        sports = response.get("raw_response") if isinstance(response.get("raw_response"), list) else []
        result = {
            "ok": True,
            "provider": self.id,
            "provider_type": self.provider_type,
            "count": len(sports),
            "sports": sports,
        }
        self._sports_cache = (time.time(), result)
        return result

    async def get_active_events(self, sport: Optional[str], league: Optional[str], **filters: Any) -> dict[str, Any]:
        sport_key, league_label, error = resolve_sport_key(sport, league)
        if error:
            return error
        response = await self._get(f"/sports/{sport_key}/events", {})
        if not response.get("ok"):
            return {**response, "sport_key": sport_key, "league": league_label, "count": 0, "events": []}
        raw_events = response.get("raw_response")
        if not isinstance(raw_events, list):
            return clean_error("PROVIDER_ERROR", "The Odds API returned an unexpected events payload.", provider=self.id)
        events = [
            normalize_sportsbook_event(self.id, event, league_label)
            for event in raw_events
            if isinstance(event, dict) and self._event_matches(event, filters)
        ]
        return {
            "ok": True,
            "result_type": "events",
            "provider": self.id,
            "provider_type": self.provider_type,
            "sport_key": sport_key,
            "league": league_label,
            "count": len(events),
            "events": events,
            "message": "Active events returned for requested sport/league only." if events else "No active events found for requested filters.",
        }

    async def get_event_odds(
        self,
        event_id: str,
        sport: Optional[str],
        league: Optional[str],
        markets: Optional[str] = None,
        bookmakers: Optional[str] = None,
    ) -> dict[str, Any]:
        sport_key, league_label, error = resolve_sport_key(sport, league)
        if error:
            return error
        response = await self._get(
            f"/sports/{sport_key}/odds",
            {
                "regions": self.default_regions,
                "markets": markets or self.default_markets,
                "oddsFormat": "american",
                "bookmakers": bookmakers or self.default_bookmakers,
            },
        )
        if not response.get("ok"):
            return {**response, "sport_key": sport_key, "league": league_label, "provider_event_id": event_id}
        raw_events = response.get("raw_response")
        if not isinstance(raw_events, list):
            return clean_error("PROVIDER_ERROR", "The Odds API returned an unexpected odds payload.", provider=self.id)
        matched = next((event for event in raw_events if str(event.get("id")) == str(event_id)), None)
        if not matched:
            return clean_error(
                "NO_DATA",
                "No sportsbook odds found for requested sport/league/event.",
                provider=self.id,
                sport_key=sport_key,
                league=league_label,
                provider_event_id=event_id,
            )
        odds = self._flatten_odds(matched)
        return {
            "ok": True,
            "result_type": "odds",
            "has_actual_odds": bool(odds),
            "provider": self.id,
            "provider_type": self.provider_type,
            "sport_key": sport_key,
            "league": league_label,
            "provider_event_id": event_id,
            "event": normalize_sportsbook_event(self.id, matched, league_label),
            "odds": odds,
            "best_prices": self._best_prices(odds),
            "message": "Sportsbook odds returned for requested sport/league/event only." if odds else "No sportsbook odds found for requested sport/league/event.",
        }

    async def get_first_event_odds(self, sport: Optional[str], league: Optional[str], **kwargs: Any) -> dict[str, Any]:
        events_response = await self.get_active_events(sport, league, **kwargs)
        if not events_response.get("ok"):
            return events_response
        events = events_response.get("events") or []
        if not events:
            return clean_error("NO_DATA", "No matching events found for requested sport/league/filters.", provider=self.id)
        first_event_id = events[0].get("provider_event_id")
        return await self.get_event_odds(first_event_id, sport, league, kwargs.get("markets"), kwargs.get("bookmakers"))

    def _event_matches(self, event: dict[str, Any], filters: dict[str, Any]) -> bool:
        home = str(event.get("home_team", "")).lower()
        away = str(event.get("away_team", "")).lower()
        commence_time = str(event.get("commence_time", ""))
        team = filters.get("team")
        home_team = filters.get("home_team")
        away_team = filters.get("away_team")
        event_date = filters.get("date")
        if team and team.lower() not in home and team.lower() not in away:
            return False
        if home_team and home_team.lower() not in home:
            return False
        if away_team and away_team.lower() not in away:
            return False
        if event_date and not commence_time.startswith(event_date):
            return False
        return True

    def _flatten_odds(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        rows = []
        event_id = str(event.get("id"))
        for bookmaker in event.get("bookmakers") or []:
            for market in bookmaker.get("markets") or []:
                for outcome in market.get("outcomes") or []:
                    rows.append(normalize_sportsbook_odds(
                        self.id,
                        event_id,
                        event.get("sport_key"),
                        market.get("key"),
                        bookmaker.get("key") or bookmaker.get("title"),
                        outcome.get("name"),
                        outcome.get("price"),
                        outcome.get("point"),
                        market.get("last_update") or bookmaker.get("last_update"),
                        {"bookmaker": bookmaker, "market": market, "outcome": outcome},
                    ))
        return rows

    def _best_prices(self, odds: list[dict[str, Any]]) -> list[dict[str, Any]]:
        grouped: dict[tuple[Any, ...], dict[str, Any]] = {}
        for row in odds:
            key = (row.get("market"), row.get("selection"), row.get("point"))
            current = grouped.get(key)
            price = row.get("price_american")
            current_price = current.get("price_american") if current else None
            if current is None or (isinstance(price, (int, float)) and (current_price is None or price > current_price)):
                grouped[key] = row
        return list(grouped.values())

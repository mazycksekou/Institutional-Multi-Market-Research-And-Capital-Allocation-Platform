from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException

from betting_providers import aliases as betting_aliases


ACTION_SAFE_EVENT_KEYS: frozenset[str] = frozenset({
    "provider",
    "provider_type",
    "provider_event_id",
    "event_id",
    "id",
    "sport_key",
    "league",
    "commence_time",
    "home_team",
    "away_team",
    "event_ticker",
    "series_ticker",
    "title",
    "category",
    "status",
})

ACTION_ODDS_LINE_KEYS: frozenset[str] = frozenset({
    "provider",
    "provider_type",
    "provider_event_id",
    "sport_key",
    "market",
    "sportsbook",
    "selection",
    "price_american",
    "price_decimal",
    "implied_probability",
    "point",
    "last_update",
})


class ActionBettingService:
    def __init__(
        self,
        provider_router: Any,
        *,
        default_markets: str,
        default_bookmakers: str,
    ) -> None:
        self.provider_router = provider_router
        self.default_markets = default_markets
        self.default_bookmakers = default_bookmakers

    @staticmethod
    def normalize_action_league_input(league: str) -> str:
        raw = (league or "").strip() or "baseball_mlb"
        if raw.lower().replace("-", "_") == "mlb":
            return "baseball_mlb"
        return raw

    @staticmethod
    def slim_events_for_action(events: Any, limit: int) -> list[dict[str, Any]]:
        if not isinstance(events, list):
            return []
        cap = max(0, min(int(limit), 100))
        out: list[dict[str, Any]] = []
        for event in events[:cap]:
            if not isinstance(event, dict):
                continue
            row = {key: event[key] for key in ACTION_SAFE_EVENT_KEYS if key in event}
            if not row:
                provider_id = event.get("id") or event.get("event_id") or event.get("provider_event_id")
                if provider_id is not None:
                    row = {"provider_event_id": provider_id, "event_id": provider_id, "id": provider_id}
            out.append(row)
        return out

    @staticmethod
    def parse_markets_requested(markets_csv: str) -> list[str]:
        parts = [part.strip() for part in (markets_csv or "").split(",") if part.strip()]
        return parts if parts else ["h2h", "spreads", "totals"]

    @staticmethod
    def build_markets_and_bookmakers(flat_odds: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        if not isinstance(flat_odds, list):
            return [], []
        by_market: dict[str, list[dict[str, Any]]] = {}
        books: dict[str, dict[str, str]] = {}
        for row in flat_odds:
            if not isinstance(row, dict):
                continue
            slim = {key: row[key] for key in ACTION_ODDS_LINE_KEYS if key in row}
            market = str(slim.get("market") or "unknown")
            by_market.setdefault(market, []).append(slim)
            sportsbook = slim.get("sportsbook")
            if sportsbook is not None and str(sportsbook) not in books:
                key = str(sportsbook)
                books[key] = {"key": key, "title": key}
        markets_out = [{"market_key": key, "lines": value} for key, value in sorted(by_market.items())]
        bookmakers_out = sorted(books.values(), key=lambda book: book["key"])
        return markets_out, bookmakers_out

    @staticmethod
    def event_odds_fail(
        endpoint_id: str,
        event_id: str,
        league_val: str,
        provider_val: str,
        markets_requested: list[str],
        error: str,
        detail: str,
    ) -> dict[str, Any]:
        return {
            "ok": False,
            "endpoint": endpoint_id,
            "event_id": event_id,
            "league": league_val,
            "provider": provider_val,
            "markets_requested": markets_requested,
            "markets": [],
            "bookmakers": [],
            "error": error,
            "detail": detail,
        }

    async def fetch_active_events_envelope(
        self,
        league: str,
        provider: Optional[str],
        limit: int,
    ) -> dict[str, Any]:
        endpoint_id = "getActiveBettingEvents"
        league_param = self.normalize_action_league_input(league)
        provider_used = (provider or "").strip() or None
        default_provider = self.provider_router.default_betting_provider()
        resolved_provider = provider_used or default_provider
        sport_key_out: Optional[str] = None

        try:
            sport_key, _label, resolve_err = betting_aliases.resolve_sport_key(None, league_param)
            if resolve_err:
                return {
                    "ok": False,
                    "endpoint": endpoint_id,
                    "league": league_param,
                    "provider": resolved_provider,
                    "count": 0,
                    "events": [],
                    "error": str(resolve_err.get("error_type") or "UNKNOWN_SPORT"),
                    "detail": str(resolve_err.get("message") or "Unknown sport or league."),
                }
            sport_key_out = sport_key

            payload = await self.provider_router.get_active_events(provider_used, None, league_param)

            if not isinstance(payload, dict):
                return {
                    "ok": False,
                    "endpoint": endpoint_id,
                    "league": sport_key_out or league_param,
                    "provider": resolved_provider,
                    "count": 0,
                    "events": [],
                    "error": "INVALID_RESPONSE",
                    "detail": "Provider returned an unexpected payload.",
                }

            if not payload.get("ok"):
                return {
                    "ok": False,
                    "endpoint": endpoint_id,
                    "league": str(payload.get("sport_key") or sport_key_out or league_param),
                    "provider": str(payload.get("provider") or resolved_provider),
                    "count": 0,
                    "events": [],
                    "error": str(payload.get("error_type") or "PROVIDER_ERROR"),
                    "detail": str(payload.get("message") or "Provider request failed."),
                }

            events_src = payload.get("events")
            if not isinstance(events_src, list) and isinstance(payload.get("data"), list):
                events_src = payload["data"]
            if not isinstance(events_src, list):
                events_src = []

            slim = self.slim_events_for_action(events_src, limit)
            league_out = str(payload.get("sport_key") or sport_key_out or league_param)

            return {
                "ok": True,
                "endpoint": endpoint_id,
                "league": league_out,
                "provider": str(payload.get("provider") or resolved_provider),
                "count": len(slim),
                "events": slim,
                "error": None,
                "detail": None,
            }
        except Exception:
            return {
                "ok": False,
                "endpoint": endpoint_id,
                "league": str(sport_key_out or league_param),
                "provider": str(provider_used or default_provider),
                "count": 0,
                "events": [],
                "error": "UNEXPECTED_ERROR",
                "detail": "Active events request failed.",
            }

    async def fetch_event_odds_envelope(
        self,
        event_id: str,
        league: str,
        provider: Optional[str],
        markets_csv: str,
        bookmakers_csv: str,
    ) -> dict[str, Any]:
        endpoint_id = "getEventOdds"
        league_param = self.normalize_action_league_input(league)
        provider_used = (provider or "").strip() or None
        default_provider = self.provider_router.default_betting_provider()
        resolved_provider = provider_used or default_provider
        markets_requested = self.parse_markets_requested(markets_csv)
        sport_key_out: Optional[str] = None

        try:
            sport_key, _label, resolve_err = betting_aliases.resolve_sport_key(None, league_param)
            if resolve_err:
                return self.event_odds_fail(
                    endpoint_id,
                    event_id,
                    league_param,
                    resolved_provider,
                    markets_requested,
                    str(resolve_err.get("error_type") or "UNKNOWN_SPORT"),
                    str(resolve_err.get("message") or "Unknown sport or league."),
                )
            sport_key_out = sport_key

            payload = await self.provider_router.get_event_odds(
                provider_used,
                event_id,
                None,
                league_param,
                markets=markets_csv or self.default_markets,
                bookmakers=bookmakers_csv or self.default_bookmakers,
            )

            if not isinstance(payload, dict):
                return self.event_odds_fail(
                    endpoint_id,
                    event_id,
                    str(sport_key_out or league_param),
                    resolved_provider,
                    markets_requested,
                    "INVALID_RESPONSE",
                    "Provider returned an unexpected payload.",
                )

            if not payload.get("ok"):
                return self.event_odds_fail(
                    endpoint_id,
                    event_id,
                    str(payload.get("sport_key") or sport_key_out or league_param),
                    str(payload.get("provider") or resolved_provider),
                    markets_requested,
                    str(payload.get("error_type") or "PROVIDER_ERROR"),
                    str(payload.get("message") or "Provider request failed."),
                )

            flat = payload.get("odds")
            markets_block, books_block = self.build_markets_and_bookmakers(flat)
            league_out = str(payload.get("sport_key") or sport_key_out or league_param)

            return {
                "ok": True,
                "endpoint": endpoint_id,
                "event_id": event_id,
                "league": league_out,
                "provider": str(payload.get("provider") or resolved_provider),
                "markets_requested": markets_requested,
                "markets": markets_block,
                "bookmakers": books_block,
                "error": None,
                "detail": None,
            }
        except HTTPException as exc:
            detail = exc.detail
            if not isinstance(detail, str):
                detail = "Request rejected."
            return self.event_odds_fail(
                endpoint_id,
                event_id,
                str(sport_key_out or league_param),
                str(provider_used or default_provider),
                markets_requested,
                "HTTP_ERROR",
                detail,
            )
        except Exception:
            return self.event_odds_fail(
                endpoint_id,
                event_id,
                str(sport_key_out or league_param),
                str(provider_used or default_provider),
                markets_requested,
                "UNEXPECTED_ERROR",
                "Event odds request failed.",
            )

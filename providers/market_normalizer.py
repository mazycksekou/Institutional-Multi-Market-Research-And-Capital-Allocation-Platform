from __future__ import annotations

from typing import Any


SPORT_ALIASES = {
    "nba": "basketball_nba",
    "wnba": "basketball_wnba",
    "nfl": "americanfootball_nfl",
    "cfb": "americanfootball_ncaaf",
    "ncaaf": "americanfootball_ncaaf",
    "mlb": "baseball_mlb",
    "nhl": "icehockey_nhl",
    "soccer": "soccer",
    "epl": "soccer",
    "ucl": "soccer",
    "ufc": "mixed_martial_arts",
    "mma": "mixed_martial_arts",
    "boxing": "boxing",
    "valorant": "esports",
    "csgo": "esports",
    "lol": "esports",
}

MARKET_ALIASES = {
    "h2h": "moneyline",
    "moneyline": "moneyline",
    "ml": "moneyline",
    "spread": "spread",
    "spreads": "spread",
    "total": "total",
    "totals": "total",
    "over_under": "total",
    "team_total": "team_total",
    "player_prop": "player_prop",
    "prop": "player_prop",
    "props": "player_prop",
    "first_half": "first_half",
    "1h": "first_half",
    "first_quarter": "first_quarter",
    "1q": "first_quarter",
    "first_5_innings": "first_5_innings",
    "f5": "first_5_innings",
    "live": "live",
    "in_play": "live",
    "alt_line": "alt_line",
    "alternate_line": "alt_line",
    "kalshi_prediction_market": "kalshi_prediction_market",
}


def _key(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def normalize_sport(value: Any, league: Any = None) -> str | None:
    sport = _key(value) or _key(league)
    if not sport:
        return None
    return SPORT_ALIASES.get(sport, sport)


def normalize_market(value: Any) -> str | None:
    market = _key(value)
    if not market:
        return None
    return MARKET_ALIASES.get(market, market)


def normalize_ticket_fields(payload: dict[str, Any]) -> dict[str, Any]:
    ticket = dict(payload)
    ticket["sport"] = normalize_sport(ticket.get("sport"), ticket.get("league"))
    ticket["league"] = normalize_sport(ticket.get("league"), ticket.get("sport")) or ticket.get("league")
    ticket["market"] = normalize_market(ticket.get("market"))
    return ticket


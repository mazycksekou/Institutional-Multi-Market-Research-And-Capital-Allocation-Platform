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
    "rugby": "rugby",
    "rugby_union": "rugby",
    "rugby_league": "rugby",
    "nrl": "rugby",
    "super_rugby": "rugby",
    "six_nations": "rugby",
    "premiership_rugby": "rugby",
    "united_rugby_championship": "rugby",
    "rugby_world_cup": "rugby",
    "top_14": "rugby",
    "lacrosse": "lacrosse",
    "lax": "lacrosse",
    "mens_lacrosse": "lacrosse",
    "womens_lacrosse": "lacrosse",
    "college_lacrosse": "lacrosse",
    "ncaa_lacrosse": "lacrosse",
    "pll": "lacrosse",
    "premier_lacrosse_league": "lacrosse",
    "nll": "lacrosse",
    "national_lacrosse_league": "lacrosse",
    "ufc": "mixed_martial_arts",
    "mma": "mixed_martial_arts",
    "boxing": "boxing",
    "valorant": "valorant",
    "val": "valorant",
    "riot_valorant": "valorant",
    "esports_valorant": "valorant",
    "vct": "valorant",
    "valorant_champions_tour": "valorant",
    "league_of_legends": "league_of_legends",
    "lol": "league_of_legends",
    "league": "league_of_legends",
    "riot_lol": "league_of_legends",
    "esports_lol": "league_of_legends",
    "lcs": "league_of_legends",
    "lec": "league_of_legends",
    "lck": "league_of_legends",
    "lpl": "league_of_legends",
    "worlds": "league_of_legends",
    "msi": "league_of_legends",
    "dota2": "dota2",
    "dota_2": "dota2",
    "dota": "dota2",
    "esports_dota2": "dota2",
    "dota_pro_circuit": "dota2",
    "dpc": "dota2",
    "the_international": "dota2",
    "ti": "dota2",
    "call_of_duty": "call_of_duty",
    "cod": "call_of_duty",
    "cdl": "call_of_duty",
    "esports_cod": "call_of_duty",
    "cod_league": "call_of_duty",
    "callofduty": "call_of_duty",
    "call_of_duty_league": "call_of_duty",
    "overwatch": "overwatch",
    "overwatch2": "overwatch",
    "overwatch_2": "overwatch",
    "ow": "overwatch",
    "ow2": "overwatch",
    "esports_overwatch": "overwatch",
    "overwatch_league": "overwatch",
    "owl": "overwatch",
    "overwatch_champions_series": "overwatch",
    "owcs": "overwatch",
    "formula_e": "formula_e",
    "formulae": "formula_e",
    "fe": "formula_e",
    "fia_formula_e": "formula_e",
    "abb_formula_e": "formula_e",
    "electric_racing": "formula_e",
    "motorsport_formula_e": "formula_e",
    "csgo": "cs2",
    "cs2": "cs2",
    "counter_strike_2": "cs2",
    "counterstrike2": "cs2",
    "counter_strike": "cs2",
    "counterstrike": "cs2",
    "esports_cs2": "cs2",
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

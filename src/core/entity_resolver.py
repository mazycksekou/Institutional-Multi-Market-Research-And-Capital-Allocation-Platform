from __future__ import annotations

import re
from typing import Any


_WHITESPACE_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^a-z0-9]+")

_NBA_TEAM_ALIASES = {
    "ny knicks": "New York Knicks",
    "knicks": "New York Knicks",
    "new york knicks": "New York Knicks",
    "sa spurs": "San Antonio Spurs",
    "spurs": "San Antonio Spurs",
    "san antonio spurs": "San Antonio Spurs",
    "la lakers": "Los Angeles Lakers",
    "lakers": "Los Angeles Lakers",
    "los angeles lakers": "Los Angeles Lakers",
    "la clippers": "Los Angeles Clippers",
    "clippers": "Los Angeles Clippers",
    "los angeles clippers": "Los Angeles Clippers",
    "gs warriors": "Golden State Warriors",
    "warriors": "Golden State Warriors",
    "golden state warriors": "Golden State Warriors",
    "okc thunder": "Oklahoma City Thunder",
    "thunder": "Oklahoma City Thunder",
    "oklahoma city thunder": "Oklahoma City Thunder",
}

_MARKET_ALIASES = {
    "moneyline": "h2h",
    "ml": "h2h",
    "h2h": "h2h",
    "spread": "spreads",
    "spreads": "spreads",
    "total": "totals",
    "totals": "totals",
    "over_under": "totals",
    "team_total": "team_totals",
    "player_prop": "player_props",
}

_BOOK_ALIASES = {
    "dk": "DraftKings",
    "draftkings": "DraftKings",
    "fanduel": "FanDuel",
    "fd": "FanDuel",
    "betmgm": "BetMGM",
    "caesars": "Caesars",
    "espnbet": "ESPN BET",
    "espn bet": "ESPN BET",
    "bet365": "bet365",
}

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
    "table_tennis": "table_tennis",
    "ping_pong": "table_tennis",
    "pingpong": "table_tennis",
    "ittf": "table_tennis",
    "wtt": "table_tennis",
    "world_table_tennis": "table_tennis",
    "olympic_table_tennis": "table_tennis",
    "badminton": "badminton",
    "bwf": "badminton",
    "world_badminton": "badminton",
    "olympic_badminton": "badminton",
    "badminton_singles": "badminton",
    "badminton_doubles": "badminton",
    "bwf_world_tour": "badminton",
    "pickleball": "pickleball",
    "pro_pickleball": "pickleball",
    "ppa": "pickleball",
    "mlf": "pickleball",
    "major_league_pickleball": "pickleball",
    "app_tour": "pickleball",
    "pickleball_singles": "pickleball",
    "pickleball_doubles": "pickleball",
    "darts": "darts",
    "pdc": "darts",
    "wdf": "darts",
    "professional_darts": "darts",
    "premier_league_darts": "darts",
    "world_darts_championship": "darts",
    "darts_match": "darts",
    "snooker": "snooker",
    "billiards": "snooker",
    "pool": "snooker",
    "cue_sports": "snooker",
    "world_snooker": "snooker",
    "wst": "snooker",
    "nine_ball": "snooker",
    "eight_ball": "snooker",
    "ten_ball": "snooker",
    "professional_snooker": "snooker",
    "volleyball": "volleyball",
    "indoor_volleyball": "volleyball",
    "beach_volleyball": "volleyball",
    "ncaa_volleyball": "volleyball",
    "mens_volleyball": "volleyball",
    "womens_volleyball": "volleyball",
    "fivb": "volleyball",
    "vnl": "volleyball",
    "avp": "volleyball",
    "olympic_volleyball": "volleyball",
    "handball": "handball",
    "team_handball": "handball",
    "european_handball": "handball",
    "olympic_handball": "handball",
    "ehf": "handball",
    "ihf": "handball",
    "handball_bundesliga": "handball",
    "champions_league_handball": "handball",
    "water_polo": "water_polo",
    "waterpolo": "water_polo",
    "olympic_water_polo": "water_polo",
    "ncaa_water_polo": "water_polo",
    "world_aquatics_water_polo": "water_polo",
    "fina_water_polo": "water_polo",
    "mens_water_polo": "water_polo",
    "womens_water_polo": "water_polo",
    "afl": "afl",
    "australian_rules": "afl",
    "aussie_rules": "afl",
    "australian_football": "afl",
    "australian_rules_football": "afl",
    "afl_football": "afl",
    "australian_football_league": "afl",
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

_CORE_TO_TICKET_MARKET = {
    "h2h": "moneyline",
    "spreads": "spread",
    "totals": "total",
    "team_totals": "team_total",
    "player_props": "player_prop",
}

_TICKET_MARKET_ALIASES = {
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


def normalize_text(value: str) -> str:
    cleaned = _PUNCT_RE.sub(" ", str(value or "").lower()).strip()
    return _WHITESPACE_RE.sub(" ", cleaned)


def canonical_team_name(name: str, sport: str = "basketball_nba") -> str:
    normalized = normalize_text(name)
    if sport == "basketball_nba":
        return _NBA_TEAM_ALIASES.get(normalized, str(name or "").strip())
    return str(name or "").strip()


def canonical_market_key(market: str) -> str:
    normalized = normalize_text(market).replace(" ", "_")
    return _MARKET_ALIASES.get(normalized, normalized)


def _alias_key(value: Any) -> str:
    return normalize_text(str(value or "")).replace(" ", "_")


def canonical_sport_key(value: Any, league: Any = None) -> str | None:
    sport = _alias_key(value) or _alias_key(league)
    if not sport:
        return None
    return SPORT_ALIASES.get(sport, sport)


def ticket_market_name(value: Any) -> str | None:
    market = _alias_key(value)
    if not market:
        return None
    canonical = canonical_market_key(market)
    return _CORE_TO_TICKET_MARKET.get(canonical) or _TICKET_MARKET_ALIASES.get(market, market)


def normalize_sport(value: Any, league: Any = None) -> str | None:
    return canonical_sport_key(value, league)


def normalize_market(value: Any) -> str | None:
    return ticket_market_name(value)


def normalize_ticket_fields(payload: dict[str, Any]) -> dict[str, Any]:
    ticket = dict(payload)
    ticket["sport"] = canonical_sport_key(ticket.get("sport"), ticket.get("league"))
    ticket["league"] = canonical_sport_key(ticket.get("league"), ticket.get("sport")) or ticket.get("league")
    ticket["market"] = ticket_market_name(ticket.get("market"))
    return ticket


def build_event_key(
    sport: str,
    home_team: str,
    away_team: str,
    commence_time: str | None = None,
) -> str:
    sport_key = normalize_text(sport).replace(" ", "_")
    home_key = normalize_text(canonical_team_name(home_team, sport)).replace(" ", "_")
    away_key = normalize_text(canonical_team_name(away_team, sport)).replace(" ", "_")
    time_key = normalize_text(commence_time or "").replace(" ", "_")
    parts = [sport_key, away_key, home_key]
    if time_key:
        parts.append(time_key)
    return ":".join(parts)


def resolve_book_name(book: str) -> str:
    raw = str(book or "").strip()
    normalized = normalize_text(raw)
    return _BOOK_ALIASES.get(normalized, raw)

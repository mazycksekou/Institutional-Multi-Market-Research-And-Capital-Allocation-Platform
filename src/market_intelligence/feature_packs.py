from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from .sports import normalize_market, normalize_sport


SPORT_FEATURE_PACKS_VERSION = "src.market_intelligence.feature_packs.v1"
MARKET_FEATURE_PACKS_VERSION = "src.market_intelligence.feature_packs.v1"

SPORT_FEATURE_NEVER_FEATURE_FIELDS = [
    "final_result",
    "winner",
    "home_score",
    "away_score",
    "profit_loss",
    "closing_odds",
    "closing_line",
    "clv",
    "result",
    "settled_result",
    "bet_result",
    "outcome",
]

MARKET_FEATURE_NEVER_FEATURE_FIELDS = list(SPORT_FEATURE_NEVER_FEATURE_FIELDS)

_SPORT_FALLBACK = {
    "general": {
        "sport_key": "general",
        "sport_family": "general",
        "required_fields": ["sport", "event_date", "market", "selection", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["home_team", "away_team", "confidence", "injuries", "weather"],
    },
    "basketball_nba": {
        "sport_key": "basketball_nba",
        "sport_family": "basketball",
        "required_fields": ["sport", "event_date", "market", "selection", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["home_team", "away_team", "pace", "injuries", "rest_days", "home_or_away"],
    },
    "basketball_wnba": {
        "sport_key": "basketball_wnba",
        "sport_family": "basketball",
        "required_fields": ["sport", "event_date", "market", "selection", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["home_team", "away_team", "pace", "injuries", "rest_days", "home_or_away"],
    },
    "basketball_ncaab": {
        "sport_key": "basketball_ncaab",
        "sport_family": "basketball",
        "required_fields": ["sport", "event_date", "market", "selection", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["home_team", "away_team", "pace", "injuries", "rest_days", "home_or_away"],
    },
    "basketball_ncaaw": {
        "sport_key": "basketball_ncaaw",
        "sport_family": "basketball",
        "required_fields": ["sport", "event_date", "market", "selection", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["home_team", "away_team", "pace", "injuries", "rest_days", "home_or_away"],
    },
    "americanfootball_nfl": {
        "sport_key": "americanfootball_nfl",
        "sport_family": "football",
        "required_fields": ["sport", "event_date", "market", "selection", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["home_team", "away_team", "injuries", "weather", "rest_days", "home_or_away"],
    },
    "americanfootball_ncaaf": {
        "sport_key": "americanfootball_ncaaf",
        "sport_family": "football",
        "required_fields": ["sport", "event_date", "market", "selection", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["home_team", "away_team", "injuries", "weather", "rest_days", "home_or_away"],
    },
    "baseball_mlb": {
        "sport_key": "baseball_mlb",
        "sport_family": "baseball",
        "required_fields": ["sport", "event_date", "market", "selection", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["home_team", "away_team", "starting_pitcher", "weather", "lineup", "rest_days"],
    },
    "icehockey_nhl": {
        "sport_key": "icehockey_nhl",
        "sport_family": "hockey",
        "required_fields": ["sport", "event_date", "market", "selection", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["home_team", "away_team", "goalie", "lineups", "injuries", "rest_days"],
    },
    "soccer": {
        "sport_key": "soccer",
        "sport_family": "soccer",
        "required_fields": ["sport", "event_date", "market", "selection", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["home_team", "away_team", "lineups", "injuries", "weather"],
    },
    "golf": {
        "sport_key": "golf",
        "sport_family": "golf",
        "required_fields": ["sport", "event_date", "market", "selection", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["player_name", "course", "weather", "tee_time"],
    },
    "tennis": {
        "sport_key": "tennis",
        "sport_family": "tennis",
        "required_fields": ["sport", "event_date", "market", "selection", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["player_name", "surface", "weather", "injuries"],
    },
    "cs2": {
        "sport_key": "cs2",
        "sport_family": "esports",
        "required_fields": ["sport", "event_date", "market", "selection", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["lineup", "map_pool", "patch", "form"],
    },
    "league_of_legends": {
        "sport_key": "league_of_legends",
        "sport_family": "esports",
        "required_fields": ["sport", "event_date", "market", "selection", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["lineup", "patch", "draft", "form"],
    },
    "ufc": {
        "sport_key": "ufc",
        "sport_family": "combat",
        "required_fields": ["sport", "event_date", "market", "selection", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["injuries", "weight_cut", "reach", "fight_style"],
    },
    "boxing": {
        "sport_key": "boxing",
        "sport_family": "combat",
        "required_fields": ["sport", "event_date", "market", "selection", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["injuries", "weight_cut", "reach", "fight_style"],
    },
}

_MARKET_FALLBACK = {
    "general_market": {
        "market_family": "general_market",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence", "liquidity_score"],
    },
    "two_way_moneyline": {
        "market_family": "two_way_moneyline",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence", "liquidity_score"],
    },
    "three_way_moneyline": {
        "market_family": "three_way_moneyline",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence", "liquidity_score"],
    },
    "spread_or_handicap": {
        "market_family": "spread_or_handicap",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability", "line_value"],
        "recommended_fields": ["support", "resistance", "confidence", "liquidity_score"],
    },
    "runline": {
        "market_family": "runline",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability", "line_value"],
        "recommended_fields": ["support", "resistance", "confidence", "liquidity_score"],
    },
    "puckline": {
        "market_family": "puckline",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability", "line_value"],
        "recommended_fields": ["support", "resistance", "confidence", "liquidity_score"],
    },
    "game_total": {
        "market_family": "game_total",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability", "line_value"],
        "recommended_fields": ["support", "resistance", "confidence", "liquidity_score"],
    },
    "team_total": {
        "market_family": "team_total",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability", "line_value"],
        "recommended_fields": ["support", "resistance", "confidence", "liquidity_score"],
    },
    "player_points_prop": {
        "market_family": "player_points_prop",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability", "line_value"],
        "recommended_fields": ["player_name", "support", "resistance", "confidence"],
    },
    "player_rebounds_prop": {
        "market_family": "player_rebounds_prop",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability", "line_value"],
        "recommended_fields": ["player_name", "support", "resistance", "confidence"],
    },
    "player_assists_prop": {
        "market_family": "player_assists_prop",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability", "line_value"],
        "recommended_fields": ["player_name", "support", "resistance", "confidence"],
    },
    "player_shots_prop": {
        "market_family": "player_shots_prop",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability", "line_value"],
        "recommended_fields": ["player_name", "support", "resistance", "confidence"],
    },
    "player_saves_prop": {
        "market_family": "player_saves_prop",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability", "line_value"],
        "recommended_fields": ["player_name", "support", "resistance", "confidence"],
    },
    "player_strikeouts_prop": {
        "market_family": "player_strikeouts_prop",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability", "line_value"],
        "recommended_fields": ["player_name", "support", "resistance", "confidence"],
    },
    "player_bases_prop": {
        "market_family": "player_bases_prop",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability", "line_value"],
        "recommended_fields": ["player_name", "support", "resistance", "confidence"],
    },
    "player_touchdowns_prop": {
        "market_family": "player_touchdowns_prop",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability", "line_value"],
        "recommended_fields": ["player_name", "support", "resistance", "confidence"],
    },
    "fight_moneyline": {
        "market_family": "fight_moneyline",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["fighter_name", "support", "resistance", "confidence"],
    },
    "fight_method": {
        "market_family": "fight_method",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["fighter_name", "support", "resistance", "confidence"],
    },
    "fight_round": {
        "market_family": "fight_round",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["fighter_name", "support", "resistance", "confidence"],
    },
    "fight_total_rounds": {
        "market_family": "fight_total_rounds",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability", "line_value"],
        "recommended_fields": ["fighter_name", "support", "resistance", "confidence"],
    },
    "fighter_prop": {
        "market_family": "fighter_prop",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability", "line_value"],
        "recommended_fields": ["fighter_name", "support", "resistance", "confidence"],
    },
    "outright": {
        "market_family": "outright",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence"],
    },
    "futures": {
        "market_family": "futures",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence"],
    },
    "tournament_winner": {
        "market_family": "tournament_winner",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence"],
    },
    "championship_winner": {
        "market_family": "championship_winner",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence"],
    },
    "award_winner": {
        "market_family": "award_winner",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence"],
    },
    "race_winner": {
        "market_family": "race_winner",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence"],
    },
    "top_finish": {
        "market_family": "top_finish",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence"],
    },
    "head_to_head_matchup": {
        "market_family": "head_to_head_matchup",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence"],
    },
    "finishing_position": {
        "market_family": "finishing_position",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence"],
    },
    "cut_made": {
        "market_family": "cut_made",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence"],
    },
    "placement_market": {
        "market_family": "placement_market",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence"],
    },
    "esports_match_winner": {
        "market_family": "esports_match_winner",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence"],
    },
    "esports_map_winner": {
        "market_family": "esports_map_winner",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence"],
    },
    "esports_map_handicap": {
        "market_family": "esports_map_handicap",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence"],
    },
    "esports_map_total": {
        "market_family": "esports_map_total",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence"],
    },
    "esports_series_correct_score": {
        "market_family": "esports_series_correct_score",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence"],
    },
    "both_teams_to_score": {
        "market_family": "both_teams_to_score",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence"],
    },
    "double_chance": {
        "market_family": "double_chance",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence"],
    },
    "draw_no_bet": {
        "market_family": "draw_no_bet",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence"],
    },
    "corners": {
        "market_family": "corners",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence"],
    },
    "cards": {
        "market_family": "cards",
        "required_fields": ["market", "selection", "event_date", "odds_at_decision_time", "market_implied_probability"],
        "recommended_fields": ["support", "resistance", "confidence"],
    },
}


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
    return text or default


def normalize_sport_key(value: Any) -> str:
    raw = _normalize_text(value or "general")
    aliases = {
        "nba": "basketball_nba",
        "basketball": "basketball_nba",
        "wnba": "basketball_wnba",
        "ncaab": "basketball_ncaab",
        "ncaaw": "basketball_ncaaw",
        "mlb": "baseball_mlb",
        "nfl": "americanfootball_nfl",
        "ncaaf": "americanfootball_ncaaf",
        "nhl": "icehockey_nhl",
        "soccer": "soccer",
        "golf": "golf",
        "tennis": "tennis",
        "csgo": "cs2",
        "counter_strike": "cs2",
        "lol": "league_of_legends",
        "league_of_legends": "league_of_legends",
        "ufc_mma": "ufc_mma",
        "ufc": "ufc",
        "boxing": "boxing",
        "mma": "mma",
        "afl": "afl",
        "badminton": "badminton",
        "darts": "darts",
        "handball": "handball",
        "lacrosse": "lacrosse",
        "pickleball": "pickleball",
        "rugby": "rugby",
        "snooker": "snooker",
        "volleyball": "volleyball",
        "water_polo": "water_polo",
    }
    return aliases.get(raw, raw if raw in _SPORT_FALLBACK else "general")


def normalize_market_family(
    market: Any,
    selection: Any | None = None,
    sport: Any | None = None,
) -> str:
    raw = _normalize_text(market or "general_market")
    selection_text = _normalize_text(selection)
    aliases = {
        "moneyline": "two_way_moneyline",
        "ml": "two_way_moneyline",
        "winner": "two_way_moneyline",
        "game_winner": "two_way_moneyline",
        "home_away": "two_way_moneyline",
        "1x2": "three_way_moneyline",
        "three_way": "three_way_moneyline",
        "three_way_moneyline": "three_way_moneyline",
        "full_time_result": "three_way_moneyline",
        "draw_market": "three_way_moneyline",
        "moneyline_or_1x2": "three_way_moneyline" if selection_text in {"draw", "x"} else "two_way_moneyline",
        "spread": "spread_or_handicap",
        "point_spread": "spread_or_handicap",
        "line": "spread_or_handicap",
        "runline": "runline",
        "puckline": "puckline",
        "total": "game_total",
        "over_under": "game_total",
        "over/under": "game_total",
        "team_total": "team_total",
        "team_points": "team_total",
        "player_points": "player_points_prop",
        "player_rebounds": "player_rebounds_prop",
        "player_assists": "player_assists_prop",
        "player_shots": "player_shots_prop",
        "player_saves": "player_saves_prop",
        "player_strikeouts": "player_strikeouts_prop",
        "player_bases": "player_bases_prop",
        "player_touchdowns": "player_touchdowns_prop",
        "prop": "player_points_prop" if selection_text == "player" else "player_points_prop",
        "player_prop": "player_points_prop",
        "fight_moneyline": "fight_moneyline",
        "method": "fight_method",
        "round": "fight_round",
        "total_rounds": "fight_total_rounds",
        "fighter_prop": "fighter_prop",
        "outright": "outright",
        "futures": "futures",
        "tournament_winner": "tournament_winner",
        "championship_winner": "championship_winner",
        "award_winner": "award_winner",
        "race_winner": "race_winner",
        "top_finish": "top_finish",
        "head_to_head": "head_to_head_matchup",
        "finishing_position": "finishing_position",
        "cut_made": "cut_made",
        "placement": "placement_market",
        "esports_match_winner": "esports_match_winner",
        "map_winner": "esports_map_winner",
        "map_handicap": "esports_map_handicap",
        "map_total": "esports_map_total",
        "correct_score": "esports_series_correct_score",
        "both_teams_to_score": "both_teams_to_score",
        "btts": "both_teams_to_score",
        "double_chance": "double_chance",
        "draw_no_bet": "draw_no_bet",
        "corners": "corners",
        "cards": "cards",
    }
    normalized = aliases.get(raw, raw)
    if normalized == "two_way_moneyline" and selection_text in {"draw", "x"}:
        return "three_way_moneyline"
    if normalized == "general_market" and sport:
        sport_key = normalize_sport_key(sport)
        if sport_key in {"basketball_nba", "basketball_wnba", "basketball_ncaab", "basketball_ncaaw", "americanfootball_nfl", "americanfootball_ncaaf", "baseball_mlb", "icehockey_nhl"}:
            return "two_way_moneyline"
    if normalized == "prop" and selection_text == "player":
        return "player_points_prop"
    if normalized in {"spread_or_handicap", "game_total", "team_total"}:
        return normalized
    return normalized if normalized in _MARKET_FALLBACK else "general_market"


def _field_presence(rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> dict[str, dict[str, Any]]:
    total_rows = len(rows)
    presence: dict[str, dict[str, Any]] = {}
    for field in fields:
        present = sum(1 for row in rows if row.get(field) not in (None, ""))
        missing = max(0, total_rows - present)
        coverage = round((present / total_rows * 100.0) if total_rows else 0.0, 1)
        presence[field] = {
            "present_count": present,
            "missing_count": missing,
            "coverage_percent": coverage,
        }
    return presence


def calculate_field_presence(rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> dict[str, dict[str, Any]]:
    return _field_presence(rows, fields)


def calculate_market_field_presence(rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> dict[str, dict[str, Any]]:
    return _field_presence(rows, fields)


def _pack_summary(
    *,
    key_name: str,
    key_value: str,
    family: str,
    required_fields: Sequence[str],
    recommended_fields: Sequence[str],
    version: str,
) -> dict[str, Any]:
    return {
        "ok": True,
        "version": version,
        key_name: key_value,
        "sport_family" if key_name == "sport_key" else "market_family": family,
        "display_name": key_value.replace("_", " ").title(),
        "depth_level": 1 if key_value else 0,
        "required_fields": list(required_fields),
        "recommended_fields": list(recommended_fields),
        "missing_data_warning": "",
        "operator_interpretation": (
            f"Local feature pack for {key_value or family}. "
            "Readiness is evaluated using deterministic local coverage only."
        ),
    }


def get_sport_feature_pack(sport: Any | None) -> dict[str, Any]:
    key = normalize_sport_key(sport)
    pack = dict(_SPORT_FALLBACK.get(key, _SPORT_FALLBACK["general"]))
    return _pack_summary(
        key_name="sport_key",
        key_value=key,
        family=str(pack["sport_family"]),
        required_fields=pack["required_fields"],
        recommended_fields=pack["recommended_fields"],
        version=SPORT_FEATURE_PACKS_VERSION,
    )


def get_supported_sport_feature_packs() -> list[str]:
    return sorted(_SPORT_FALLBACK)


def evaluate_sport_feature_readiness(
    rows: Sequence[Mapping[str, Any]],
    sport: Any | None = None,
    *,
    min_required_coverage_percent: float = 80.0,
    min_recommended_coverage_percent: float = 60.0,
) -> dict[str, Any]:
    key = normalize_sport_key(sport)
    pack = _SPORT_FALLBACK.get(key, _SPORT_FALLBACK["general"])
    required = _field_presence(rows, pack["required_fields"])
    recommended = _field_presence(rows, pack["recommended_fields"])
    required_ok = all(entry["coverage_percent"] >= float(min_required_coverage_percent) for entry in required.values()) if rows else False
    recommended_ok = all(entry["coverage_percent"] >= float(min_recommended_coverage_percent) for entry in recommended.values()) if rows else False
    missing_required_fields = [field for field, info in required.items() if info["coverage_percent"] < float(min_required_coverage_percent)]
    required_coverage_percent = round(
        sum(info["coverage_percent"] for info in required.values()) / max(1, len(required)),
        1,
    ) if rows else 0.0
    recommended_coverage_percent = round(
        sum(info["coverage_percent"] for info in recommended.values()) / max(1, len(recommended)),
        1,
    ) if rows else 0.0
    readiness_level = "no_data" if not rows else "strong" if required_ok and recommended_ok else "usable" if required_ok else "thin" if len(missing_required_fields) <= 2 else "not_ready"
    return {
        "ok": True,
        "version": SPORT_FEATURE_PACKS_VERSION,
        "sport_key": key,
        "sport_family": pack["sport_family"],
        "display_name": key.replace("_", " ").title(),
        "depth_level": 1 if rows else 0,
        "total_rows": len(rows),
        "required_field_presence": required,
        "recommended_field_presence": recommended,
        "missing_required_fields": missing_required_fields,
        "readiness_level": readiness_level,
        "required_coverage_percent": required_coverage_percent,
        "recommended_coverage_percent": recommended_coverage_percent,
    }


def summarize_sport_feature_readiness(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        key = normalize_sport_key(row.get("sport") or row.get("league"))
        groups.setdefault(key, []).append(row)
    summary = {}
    for key, items in groups.items():
        summary[key] = evaluate_sport_feature_readiness(items, sport=key)
    return {
        "ok": True,
        "status": "sport_feature_readiness_summary",
        "version": SPORT_FEATURE_PACKS_VERSION,
        "total_rows": len(rows),
        "sports": summary,
    }


def get_market_feature_pack(
    market: Any | None,
    *,
    selection: Any | None = None,
    sport: Any | None = None,
) -> dict[str, Any]:
    family = normalize_market_family(market, selection=selection, sport=sport)
    pack = dict(_MARKET_FALLBACK.get(family, _MARKET_FALLBACK["general_market"]))
    return _pack_summary(
        key_name="market_family",
        key_value=family,
        family=family,
        required_fields=pack["required_fields"],
        recommended_fields=pack["recommended_fields"],
        version=MARKET_FEATURE_PACKS_VERSION,
    )


def get_supported_market_feature_packs() -> list[str]:
    return sorted(_MARKET_FALLBACK)


def evaluate_market_feature_readiness(
    rows: Sequence[Mapping[str, Any]],
    market: Any | None = None,
    *,
    selection: Any | None = None,
    sport: Any | None = None,
    min_required_coverage_percent: float = 80.0,
    min_recommended_coverage_percent: float = 60.0,
) -> dict[str, Any]:
    family = normalize_market_family(market, selection=selection, sport=sport)
    pack = _MARKET_FALLBACK.get(family, _MARKET_FALLBACK["general_market"])
    required = _field_presence(rows, pack["required_fields"])
    recommended = _field_presence(rows, pack["recommended_fields"])
    required_ok = all(entry["coverage_percent"] >= float(min_required_coverage_percent) for entry in required.values()) if rows else False
    recommended_ok = all(entry["coverage_percent"] >= float(min_recommended_coverage_percent) for entry in recommended.values()) if rows else False
    missing_required_fields = [field for field, info in required.items() if info["coverage_percent"] < float(min_required_coverage_percent)]
    required_coverage_percent = round(
        sum(info["coverage_percent"] for info in required.values()) / max(1, len(required)),
        1,
    ) if rows else 0.0
    recommended_coverage_percent = round(
        sum(info["coverage_percent"] for info in recommended.values()) / max(1, len(recommended)),
        1,
    ) if rows else 0.0
    readiness_level = "no_data" if not rows else "strong" if required_ok and recommended_ok else "usable" if required_ok else "thin" if len(missing_required_fields) <= 2 else "not_ready"
    return {
        "ok": True,
        "version": MARKET_FEATURE_PACKS_VERSION,
        "market_family": family,
        "display_name": family.replace("_", " ").title(),
        "depth_level": 1 if rows else 0,
        "total_rows": len(rows),
        "required_field_presence": required,
        "recommended_field_presence": recommended,
        "missing_required_fields": missing_required_fields,
        "readiness_level": readiness_level,
        "required_coverage_percent": required_coverage_percent,
        "recommended_coverage_percent": recommended_coverage_percent,
    }


def summarize_market_feature_readiness(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[Mapping[str, Any]]] = {}
    for row in rows:
        key = normalize_market_family(row.get("market"), selection=row.get("selection"), sport=row.get("sport"))
        groups.setdefault(key, []).append(row)
    summary = {}
    for key, items in groups.items():
        summary[key] = evaluate_market_feature_readiness(items, market=key)
    return {
        "ok": True,
        "status": "market_feature_readiness_summary",
        "version": MARKET_FEATURE_PACKS_VERSION,
        "total_rows": len(rows),
        "markets": summary,
    }


def get_sport_feature_pack_snapshot_for_dashboard(
    db_path: str | Path,
    *,
    sport: str | None = None,
    league: str | None = None,
    market: str | None = None,
    source_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 1000,
) -> dict[str, Any]:
    from src.data.historical_odds import connect_historical_odds_db, initialize_historical_odds_db, query_historical_odds_rows

    result: dict[str, Any] = {
        "ok": False,
        "version": SPORT_FEATURE_PACKS_VERSION,
        "db_path": str(db_path),
        "filters": {
            "sport": sport,
            "league": league,
            "market": market,
            "source_key": source_key,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
        },
        "summary": {},
        "warnings": [],
    }
    try:
        conn = connect_historical_odds_db(str(db_path))
        initialize_historical_odds_db(conn)
        raw_rows = query_historical_odds_rows(
            conn,
            sport=sport,
            league=league,
            market=market,
            source_key=source_key,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        conn.close()
    except Exception as exc:
        result["warnings"].append(f"Cannot open database: {exc}")
        return result

    if not raw_rows:
        result["ok"] = True
        result["warnings"].append("No rows in filtered query.")
        return result

    try:
        summary = summarize_sport_feature_readiness(raw_rows)
        result["summary"] = summary
        result["ok"] = True
    except Exception as exc:
        result["warnings"].append(f"Readiness error: {exc}")
    return result


def get_market_feature_pack_snapshot_for_dashboard(
    db_path: str | Path,
    *,
    sport: str | None = None,
    league: str | None = None,
    market: str | None = None,
    source_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 1000,
) -> dict[str, Any]:
    from src.data.historical_odds import connect_historical_odds_db, initialize_historical_odds_db, query_historical_odds_rows

    result: dict[str, Any] = {
        "ok": False,
        "version": MARKET_FEATURE_PACKS_VERSION,
        "db_path": str(db_path),
        "filters": {
            "sport": sport,
            "league": league,
            "market": market,
            "source_key": source_key,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
        },
        "summary": {},
        "warnings": [],
    }
    try:
        conn = connect_historical_odds_db(str(db_path))
        initialize_historical_odds_db(conn)
        raw_rows = query_historical_odds_rows(
            conn,
            sport=sport,
            league=league,
            market=market,
            source_key=source_key,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        conn.close()
    except Exception as exc:
        result["warnings"].append(f"Cannot open database: {exc}")
        return result

    if not raw_rows:
        result["ok"] = True
        result["warnings"].append("No rows in filtered query.")
        return result

    try:
        summary = summarize_market_feature_readiness(raw_rows)
        result["summary"] = summary
        result["ok"] = True
    except Exception as exc:
        result["warnings"].append(f"Readiness error: {exc}")
    return result


__all__ = [
    "MARKET_FEATURE_NEVER_FEATURE_FIELDS",
    "MARKET_FEATURE_PACKS_VERSION",
    "SPORT_FEATURE_NEVER_FEATURE_FIELDS",
    "SPORT_FEATURE_PACKS_VERSION",
    "calculate_field_presence",
    "calculate_market_field_presence",
    "evaluate_market_feature_readiness",
    "evaluate_sport_feature_readiness",
    "get_market_feature_pack",
    "get_market_feature_pack_snapshot_for_dashboard",
    "get_sport_feature_pack",
    "get_sport_feature_pack_snapshot_for_dashboard",
    "get_supported_market_feature_packs",
    "get_supported_sport_feature_packs",
    "normalize_market_family",
    "normalize_sport_key",
    "summarize_market_feature_readiness",
    "summarize_sport_feature_readiness",
]

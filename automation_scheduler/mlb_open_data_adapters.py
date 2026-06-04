from __future__ import annotations

import argparse
import csv
import json
import io
import socket
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from .mlb_open_data_common import (
    MLB_MODULE,
    mlb_atomic_write_json,
    mlb_atomic_write_text,
    mlb_read_json,
    mlb_rel,
    mlb_root,
    mlb_report_root,
    mlb_safe_payload,
    mlb_validated_root,
)
from .mlb_open_data_sources import mlb_open_data_sources, source_by_id
from .open_sports_history_sources import SAFETY_FIELDS
from .scheduler_config import sanitize_filename, utc_now_iso


MLB_OPEN_DATA_ADAPTER_SCHEMA_VERSION = "mlb_open_data_adapter_v1"
DEFAULT_TINY_SAMPLE_RECORDS = 25
DEFAULT_ONE_SEASON = 2025
MAX_SAMPLE_ROWS_TO_PERSIST = 50
HTTP_TIMEOUT_SECONDS = 20
HTTP_USER_AGENT = "betting-stock-api-mlb-open-data-check"
GITHUB_API_BASE = "https://api.github.com/repos"
MLB_STATS_API_BASE = "https://statsapi.mlb.com/api/v1"
MLB_STATS_API_V11_BASE = "https://statsapi.mlb.com/api/v1.1"
LAHMAN_RAW_BASE = "https://raw.githubusercontent.com/cbwinslow/baseballdatabank/master/core"
REGISTER_RAW_BASE = "https://raw.githubusercontent.com/chadwickbureau/register/master/data"
RETROSHEET_RAW_BASE = "https://raw.githubusercontent.com/chadwickbureau/retrosheet/master"
MLB_MAX_RETROSHEET_GAMES = 20
MLB_MAX_STATS_API_GAMES = 25

BLOCKED_REASONS = {
    "available",
    "download_not_allowed",
    "download_not_implemented",
    "source_not_current_phase_allowed",
    "source_disabled",
    "source_not_available",
    "source_url_unverified",
    "source_timeout",
    "provider_error",
    "unsupported_source",
    "unsafe_source",
    "source_download_blocked",
    "terms_review_required",
    "manual_import_not_authorized",
    "structured_seed_disabled_by_default",
    "supplemental_only_no_record_ingestion",
    "no_records_found",
    "unsupported_file_shape",
    "missing_source_license",
    "missing_required_field",
    "missing_season",
    "invalid_date",
    "csv_read_error",
    "json_read_error",
    "structured_seed_fetch_error",
}

RAW_PAYLOAD_KEYS = {
    "provider_payload",
    "raw_payload",
    "external_payload",
    "source_payload",
    "raw_provider_payload",
    "response_payload",
    "raw_response",
}

SECRET_FIELD_MARKERS = ("api_key", "secret", "token", "password", "authorization", "auth_header", "cookie")


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _safe_scalar(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return None


def _real_value(value: Any) -> bool:
    if value in (None, [], {}):
        return False
    if isinstance(value, str) and value.strip().lower() in {"", "n/a", "na", "none", "null", "unknown", "tbd"}:
        return False
    return True


def _field_type(value: Any) -> str:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if value is None:
        return "null"
    return type(value).__name__


def _timeout_error(exc: BaseException) -> bool:
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return True
    if isinstance(exc, urllib.error.URLError) and isinstance(getattr(exc, "reason", None), (TimeoutError, socket.timeout)):
        return True
    return "timed out" in str(exc).lower() or "timeout" in str(exc).lower()


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [row for row in csv.DictReader(handle)]


def _read_json_rows(path: Path) -> list[dict[str, Any]]:
    payload = mlb_read_json(path)
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("items", "records", "rows", "data", "games", "results"):
            items = payload.get(key)
            if isinstance(items, list):
                return [row for row in items if isinstance(row, dict)]
    return []


def _http_get_text(url: str, *, timeout: int = HTTP_TIMEOUT_SECONDS, headers: dict[str, str] | None = None) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": HTTP_USER_AGENT,
            "Accept": "application/json,text/csv,text/plain,*/*",
            **(headers or {}),
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def _http_get_json(url: str, *, timeout: int = HTTP_TIMEOUT_SECONDS, headers: dict[str, str] | None = None) -> dict[str, Any]:
    text = _http_get_text(url, timeout=timeout, headers={"Accept": "application/vnd.github+json,application/json", **(headers or {})})
    payload = json.loads(text)
    return payload if isinstance(payload, dict) else {}


def _read_csv_text(text: str, *, max_records: int | None = None) -> list[dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(text))
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(reader):
        rows.append({str(key): value for key, value in row.items()})
        if max_records is not None and index + 1 >= int(max_records):
            break
    return rows


def _download_csv_rows(url: str, *, max_records: int | None = None) -> list[dict[str, Any]]:
    return _read_csv_text(_http_get_text(url), max_records=max_records)


def _github_directory_entries(owner: str, repo: str, path: str) -> list[dict[str, Any]]:
    url = f"{GITHUB_API_BASE}/{owner}/{repo}/contents/{path.strip('/')}"
    payload = json.loads(_http_get_text(url, headers={"Accept": "application/vnd.github+json"}))
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _github_raw_csv(owner: str, repo: str, path: str, *, max_records: int | None = None) -> list[dict[str, Any]]:
    return _download_csv_rows(f"https://raw.githubusercontent.com/{owner}/{repo}/master/{path.strip('/')}", max_records=max_records)


def _normalize_statsapi_people(person: dict[str, Any]) -> dict[str, Any]:
    return {
        "player_id": person.get("id"),
        "person_id": person.get("id"),
        "full_name": person.get("fullName"),
        "status": person.get("status", {}).get("description") if isinstance(person.get("status"), dict) else None,
        "position": person.get("position", {}).get("abbreviation") if isinstance(person.get("position"), dict) else None,
        "jersey_number": person.get("jerseyNumber"),
        "bat_side": person.get("batSide", {}).get("code") if isinstance(person.get("batSide"), dict) else None,
        "pitch_hand": person.get("pitchHand", {}).get("code") if isinstance(person.get("pitchHand"), dict) else None,
        "link": person.get("link"),
    }


def _statsapi_schedule_rows(*, season: str | int, max_records: int | None = None, game_types: str = "R") -> list[dict[str, Any]]:
    params = {
        "sportId": "1",
        "season": str(season),
        "gameTypes": game_types,
        "hydrate": "team,linescore,probablePitcher,weather,officials,venue",
    }
    url = f"{MLB_STATS_API_BASE}/schedule?{urllib.parse.urlencode(params)}"
    payload = _http_get_json(url, headers={"Accept": "application/json"})
    rows: list[dict[str, Any]] = []
    for date_block in payload.get("dates") or []:
        if not isinstance(date_block, dict):
            continue
        for game in date_block.get("games") or []:
            if not isinstance(game, dict):
                continue
            home = (game.get("teams") or {}).get("home") or {}
            away = (game.get("teams") or {}).get("away") or {}
            venue = game.get("venue") or {}
            rows.append(
                {
                    "game_pk": game.get("gamePk"),
                    "game_id": game.get("gamePk"),
                    "season": game.get("season") or season,
                    "event_date": game.get("officialDate") or str(game.get("gameDate") or "")[:10],
                    "game_date": game.get("gameDate"),
                    "game_type": game.get("gameType"),
                    "postseason_flag": game.get("gameType") not in {None, "", "R"},
                    "home_team": home.get("team", {}).get("abbreviation") or home.get("team", {}).get("name"),
                    "away_team": away.get("team", {}).get("abbreviation") or away.get("team", {}).get("name"),
                    "home_team_id": home.get("team", {}).get("id"),
                    "away_team_id": away.get("team", {}).get("id"),
                    "home_score": home.get("score"),
                    "away_score": away.get("score"),
                    "is_tie": game.get("isTie"),
                    "venue_id": venue.get("id"),
                    "venue_name": venue.get("name"),
                    "temperature": (game.get("weather") or {}).get("temp") if isinstance(game.get("weather"), dict) else None,
                    "weather": (game.get("weather") or {}).get("condition") if isinstance(game.get("weather"), dict) else None,
                    "wind_speed": (game.get("weather") or {}).get("wind") if isinstance(game.get("weather"), dict) else None,
                    "officials": [
                        {
                            "official_id": official.get("official", {}).get("id"),
                            "official_name": official.get("official", {}).get("fullName"),
                            "position": official.get("officialType"),
                        }
                        for official in game.get("officials") or []
                        if isinstance(official, dict)
                    ],
                    "probable_pitcher_home": _normalize_statsapi_people(home.get("probablePitcher") or {}),
                    "probable_pitcher_away": _normalize_statsapi_people(away.get("probablePitcher") or {}),
                    "source_label": "mlb_stats_api_schedule",
                }
            )
            if max_records is not None and len(rows) >= int(max_records):
                return rows
    return rows


def _statsapi_team_rows(*, season: str | int, max_records: int | None = None) -> list[dict[str, Any]]:
    params = {"sportId": "1", "season": str(season)}
    url = f"{MLB_STATS_API_BASE}/teams?{urllib.parse.urlencode(params)}"
    payload = _http_get_json(url, headers={"Accept": "application/json"})
    rows: list[dict[str, Any]] = []
    for team in payload.get("teams") or []:
        if not isinstance(team, dict):
            continue
        rows.append(
            {
                "team_id": team.get("id"),
                "team_name": team.get("name"),
                "team_abbr": team.get("abbreviation"),
                "team_code": team.get("teamCode"),
                "season": team.get("season") or season,
                "league_id": (team.get("league") or {}).get("id") if isinstance(team.get("league"), dict) else None,
                "division_id": (team.get("division") or {}).get("id") if isinstance(team.get("division"), dict) else None,
                "franchise_name": team.get("franchiseName"),
                "club_name": team.get("clubName"),
                "location_name": team.get("locationName"),
                "first_year_of_play": team.get("firstYearOfPlay"),
                "active": team.get("active"),
                "source_label": "mlb_stats_api_teams",
            }
        )
        if max_records is not None and len(rows) >= int(max_records):
            return rows
    return rows


def _statsapi_roster_rows(*, season: str | int, max_records: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    teams = _statsapi_team_rows(season=season)
    for team in teams:
        team_id = team.get("team_id")
        if team_id is None:
            continue
        url = f"{MLB_STATS_API_BASE}/teams/{team_id}/roster?{urllib.parse.urlencode({'rosterType': '40Man', 'season': str(season)})}"
        payload = _http_get_json(url, headers={"Accept": "application/json"})
        for item in payload.get("roster") or []:
            if not isinstance(item, dict):
                continue
            person = item.get("person") or {}
            position = item.get("position") or {}
            status = item.get("status") or {}
            rows.append(
                {
                    "team_id": team_id,
                    "player_id": person.get("id"),
                    "season": str(season),
                    "status": status.get("description"),
                    "status_code": status.get("code"),
                    "jersey_number": item.get("jerseyNumber"),
                    "position": position.get("abbreviation") or position.get("name"),
                    "full_name": person.get("fullName"),
                    "bat_side": None,
                    "pitch_hand": None,
                    "source_label": "mlb_stats_api_roster",
                }
            )
            if max_records is not None and len(rows) >= int(max_records):
                return rows
    return rows


def _statsapi_transactions_rows(*, season: str | int, max_records: int | None = None) -> list[dict[str, Any]]:
    params = {"sportId": "1", "startDate": f"{season}-01-01", "endDate": f"{season}-12-31"}
    url = f"{MLB_STATS_API_BASE}/transactions?{urllib.parse.urlencode(params)}"
    payload = _http_get_json(url, headers={"Accept": "application/json"})
    rows: list[dict[str, Any]] = []
    for item in payload.get("transactions") or []:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "transaction_id": item.get("id"),
                "date": item.get("date"),
                "effective_date": item.get("effectiveDate"),
                "resolution_date": item.get("resolutionDate"),
                "player_id": (item.get("person") or {}).get("id") if isinstance(item.get("person"), dict) else None,
                "team_id": (item.get("toTeam") or {}).get("id") if isinstance(item.get("toTeam"), dict) else None,
                "type": item.get("typeDesc"),
                "description": item.get("description"),
                "source_label": "mlb_stats_api_transactions",
            }
        )
        if max_records is not None and len(rows) >= int(max_records):
            return rows
    return rows


def _statsapi_standings_rows(*, season: str | int) -> list[dict[str, Any]]:
    params = {"leagueId": "103,104", "season": str(season), "standingsTypes": "regularSeason"}
    url = f"{MLB_STATS_API_BASE}/standings?{urllib.parse.urlencode(params)}"
    payload = _http_get_json(url, headers={"Accept": "application/json"})
    rows: list[dict[str, Any]] = []
    for record in payload.get("records") or []:
        if not isinstance(record, dict):
            continue
        league = record.get("league") or {}
        for team in record.get("teamRecords") or []:
            if not isinstance(team, dict):
                continue
            rows.append(
                {
                    "season": str(season),
                    "team_id": (team.get("team") or {}).get("id") if isinstance(team.get("team"), dict) else None,
                    "team_abbr": (team.get("team") or {}).get("abbreviation") if isinstance(team.get("team"), dict) else None,
                    "league_id": league.get("id"),
                    "wins": team.get("wins"),
                    "losses": team.get("losses"),
                    "division_rank": team.get("divisionRank"),
                    "wild_card_rank": team.get("wildCardRank"),
                    "runs_scored": team.get("runsScored"),
                    "runs_allowed": team.get("runsAllowed"),
                    "source_label": "mlb_stats_api_standings",
                }
            )
    return rows


def _statsapi_game_feed_rows(*, season: str | int, max_records: int | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    schedule = _statsapi_schedule_rows(season=season, max_records=max_records)
    lineup_rows: list[dict[str, Any]] = []
    official_rows: list[dict[str, Any]] = []
    probable_rows: list[dict[str, Any]] = []
    starting_rows: list[dict[str, Any]] = []
    bullpen_rows: list[dict[str, Any]] = []
    play_rows: list[dict[str, Any]] = []
    for game in schedule[: MLB_MAX_STATS_API_GAMES if max_records is None else min(len(schedule), int(max_records))]:
        game_pk = game.get("game_pk")
        if game_pk is None:
            continue
        url = f"{MLB_STATS_API_V11_BASE}/game/{game_pk}/feed/live"
        payload = _http_get_json(url, headers={"Accept": "application/json"})
        live = payload.get("liveData") or {}
        game_data = payload.get("gameData") or {}
        boxscore = live.get("boxscore") or {}
        home_team = (boxscore.get("teams") or {}).get("home") or {}
        away_team = (boxscore.get("teams") or {}).get("away") or {}
        for side_name, side in (("home", home_team), ("away", away_team)):
            batting_order = side.get("battingOrder") or []
            players = side.get("players") or {}
            team = (game_data.get("teams") or {}).get(side_name) or {}
            for order_index, player_key in enumerate(batting_order, start=1):
                player = players.get(player_key) or {}
                person = player.get("person") or {}
                lineup_rows.append(
                    {
                        "game_pk": game_pk,
                        "team_id": team.get("id"),
                        "player_id": person.get("id"),
                        "batting_order": order_index,
                        "position": (player.get("position") or {}).get("abbreviation"),
                        "status": (player.get("status") or {}).get("description"),
                        "full_name": person.get("fullName"),
                        "source_label": "mlb_stats_api_lineup",
                    }
                )
                if max_records is not None and len(lineup_rows) >= int(max_records):
                    break
            if max_records is not None and len(lineup_rows) >= int(max_records):
                break
            pitchers = side.get("pitchers") or []
            for pitcher_index, player_id in enumerate(pitchers, start=1):
                player_key = f"ID{player_id}"
                player = players.get(player_key) or {}
                person = player.get("person") or {"id": player_id, "fullName": None}
                stats = player.get("stats") or {}
                pitching = stats.get("pitching") if isinstance(stats, dict) else {}
                pitching = pitching if isinstance(pitching, dict) else {}
                innings = pitching.get("inningsPitched")
                pitches = pitching.get("pitchesThrown") or pitching.get("numberOfPitches")
                if pitcher_index == 1:
                    starting_rows.append(
                        {
                            "game_pk": game_pk,
                            "team_id": team.get("id"),
                            "player_id": person.get("id"),
                            "start_flag": True,
                            "innings_pitched": innings,
                            "pitch_count": pitches,
                            "probable": bool((game_data.get("probablePitchers") or {}).get(side_name)),
                            "hand": ((game_data.get("probablePitchers") or {}).get(side_name) or {}).get("pitchHand", {}).get("code") if isinstance((game_data.get("probablePitchers") or {}).get(side_name), dict) else None,
                            "game_date": (game_data.get("datetime") or {}).get("officialDate") if isinstance(game_data.get("datetime"), dict) else None,
                            "full_name": person.get("fullName"),
                            "source_label": "mlb_stats_api_starting_pitcher",
                        }
                    )
                bullpen_rows.append(
                    {
                        "game_pk": game_pk,
                        "team_id": team.get("id"),
                        "player_id": person.get("id"),
                        "relief_flag": pitcher_index > 1,
                        "pitch_count": pitches,
                        "innings_pitched": innings,
                        "save_opportunity": pitching.get("saveOpportunities"),
                        "full_name": person.get("fullName"),
                        "source_label": "mlb_stats_api_bullpen_usage",
                    }
                )
                if max_records is not None and len(bullpen_rows) >= int(max_records):
                    break
            if max_records is not None and len(bullpen_rows) >= int(max_records):
                break
        officials = boxscore.get("officials") or []
        for official in officials:
            if not isinstance(official, dict):
                continue
            off = official.get("official") or {}
            official_rows.append(
                {
                    "game_pk": game_pk,
                    "official_id": off.get("id"),
                    "umpire_name": off.get("fullName"),
                    "position": official.get("officialType"),
                    "crew": None,
                    "source_label": "mlb_stats_api_officials",
                }
            )
        probable = game_data.get("probablePitchers") or {}
        for side_name, pitcher in probable.items():
            if not isinstance(pitcher, dict):
                continue
            team = (game_data.get("teams") or {}).get(side_name) or {}
            probable_rows.append(
                {
                    "game_pk": game_pk,
                    "team_id": team.get("id"),
                    "player_id": pitcher.get("id"),
                    "probable": True,
                    "hand": (pitcher.get("pitchHand") or {}).get("code") if isinstance(pitcher.get("pitchHand"), dict) else None,
                    "game_date": game_data.get("datetime", {}).get("officialDate") if isinstance(game_data.get("datetime"), dict) else None,
                    "source_label": "mlb_stats_api_probable_pitchers",
                }
            )
        for event in (live.get("plays") or {}).get("allPlays") or []:
            if not isinstance(event, dict):
                continue
            play_rows.append(
                {
                    "game_pk": game_pk,
                    "at_bat_number": event.get("about", {}).get("atBatNumber"),
                    "inning": event.get("about", {}).get("inning"),
                    "half_inning": event.get("about", {}).get("halfInning"),
                    "batter": (event.get("matchup") or {}).get("batter", {}).get("fullName") if isinstance(event.get("matchup"), dict) else None,
                    "pitcher": (event.get("matchup") or {}).get("pitcher", {}).get("fullName") if isinstance(event.get("matchup"), dict) else None,
                    "event_type": event.get("result", {}).get("event"),
                    "description": event.get("result", {}).get("description"),
                    "runs_scored": event.get("result", {}).get("rbi"),
                    "source_label": "mlb_stats_api_play_by_play",
                }
            )
            if max_records is not None and len(play_rows) >= int(max_records):
                break
        if max_records is not None and len(play_rows) >= int(max_records) and len(lineup_rows) >= int(max_records):
            break
    return lineup_rows, official_rows, probable_rows, starting_rows, bullpen_rows, play_rows


def _retrosheet_event_rows(*, season: str | int, max_records: int | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    entries = _github_directory_entries("chadwickbureau", "retrosheet", f"seasons/{season}")
    event_files = [item for item in entries if str(item.get("name") or "").upper().endswith((".EVA", ".EVN", ".EVE", ".EBA", ".EBN", ".EBE"))]
    event_files = sorted(event_files, key=lambda item: str(item.get("name") or ""))
    game_rows: list[dict[str, Any]] = []
    play_rows: list[dict[str, Any]] = []
    for item in event_files:
        raw_url = str(item.get("download_url") or "")
        if not raw_url:
            continue
        text = _http_get_text(raw_url)
        current: dict[str, Any] = {}
        current_game_id = None
        current_pitchers: dict[str, str | None] = {"home": None, "away": None}
        current_teams: dict[str, str | None] = {"home": None, "away": None}
        lineups: list[dict[str, Any]] = []
        for row in csv.reader(io.StringIO(text)):
            if not row:
                continue
            rec_type = row[0]
            if rec_type == "id" and len(row) > 1:
                current_game_id = row[1]
            elif rec_type == "info" and len(row) > 2:
                current.setdefault("info", {})[str(row[1])] = row[2]
            elif rec_type == "start" and len(row) >= 6:
                player_id = row[1]
                player_name = row[2].strip('"') if row[2] else None
                batting_order = row[3]
                position = row[5]
                side = "away" if len(lineups) < 9 else "home"
                if position == "1":
                    current_pitchers[side] = player_id
                lineups.append(
                    {
                        "game_id": current_game_id,
                        "season": str(season),
                        "player_id": player_id,
                        "full_name": player_name,
                        "batting_order": batting_order,
                        "position": position,
                        "team_side": side,
                        "source_label": "retrosheet_start_line",
                    }
                )
            elif rec_type == "sub" and len(row) >= 6:
                player_id = row[1]
                player_name = row[2].strip('"') if row[2] else None
                position = row[5]
                side = "away" if (row[3] == "0") else "home"
                if position == "1":
                    current_pitchers[side] = player_id
                lineups.append(
                    {
                        "game_id": current_game_id,
                        "season": str(season),
                        "player_id": player_id,
                        "full_name": player_name,
                        "batting_order": None,
                        "position": position,
                        "team_side": side,
                        "source_label": "retrosheet_sub_line",
                    }
                )
            elif rec_type == "play" and len(row) >= 7:
                side = "away" if row[2] == "0" else "home"
                fielding_side = "home" if side == "away" else "away"
                play_rows.append(
                    {
                        "game_id": current_game_id,
                        "play_id": f"{current_game_id}:{len(play_rows)+1}",
                        "season": str(season),
                        "inning": row[1],
                        "batting_team_side": side,
                        "fielding_team_side": fielding_side,
                        "batter_id": row[3],
                        "pitcher_id": current_pitchers.get(fielding_side),
                        "count": row[4],
                        "pitches": row[5],
                        "event_type": row[6],
                        "source_label": "retrosheet_play",
                    }
                )
                if max_records is not None and len(play_rows) >= int(max_records):
                    break
        info = current.get("info") or {}
        if current_game_id:
            game_rows.append(
                {
                    "game_id": current_game_id,
                    "season": str(season),
                    "event_date": str(info.get("date") or "")[:10].replace("/", "-"),
                    "home_team": info.get("hometeam"),
                    "away_team": info.get("visteam"),
                    "game_type": info.get("gametype"),
                    "postseason_flag": str(info.get("gametype") or "").lower() != "regular",
                    "playoff_round": str(item.get("name") or "").replace(f"{season}", "").split(".")[0] if str(info.get("gametype") or "").lower() != "regular" else None,
                    "stadium": info.get("site"),
                    "temperature": info.get("temp"),
                    "wind_speed": info.get("windspeed"),
                    "wind_direction": info.get("winddir"),
                    "attendance": info.get("attendance"),
                    "umpire_home": info.get("umphome"),
                    "umpire_1b": info.get("ump1b"),
                    "umpire_2b": info.get("ump2b"),
                    "umpire_3b": info.get("ump3b"),
                    "starting_pitcher_away": current_pitchers.get("away"),
                    "starting_pitcher_home": current_pitchers.get("home"),
                    "source_label": "retrosheet_event_game",
                }
            )
        if max_records is not None and len(game_rows) >= int(max_records):
            break
    return game_rows, play_rows


def _fetch_open_mlb_rows(source: dict[str, Any], *, season: str | int | None = None, max_records: int | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source_id = str(source.get("source_id") or "")
    category = str(source.get("data_category") or "")
    source_kind = str(source.get("source_kind") or "")
    season_text = str(season or DEFAULT_ONE_SEASON)
    if source_id == "batting_stats_lahman":
        rows = _github_raw_csv("cbwinslow", "baseballdatabank", "core/Batting.csv", max_records=max_records)
        if season is not None:
            rows = [row for row in rows if str(row.get("yearID") or row.get("season") or "") == season_text]
        return rows, {"downloads_attempted": 1, "downloads_succeeded": 1, "provider_calls_attempted": 1}
    if source_id == "pitching_stats_lahman":
        rows = _github_raw_csv("cbwinslow", "baseballdatabank", "core/Pitching.csv", max_records=max_records)
        if season is not None:
            rows = [row for row in rows if str(row.get("yearID") or row.get("season") or "") == season_text]
        return rows, {"downloads_attempted": 1, "downloads_succeeded": 1, "provider_calls_attempted": 1}
    if source_id == "fielding_stats_lahman":
        rows = _github_raw_csv("cbwinslow", "baseballdatabank", "core/Fielding.csv", max_records=max_records)
        if season is not None:
            rows = [row for row in rows if str(row.get("yearID") or row.get("season") or "") == season_text]
        return rows, {"downloads_attempted": 1, "downloads_succeeded": 1, "provider_calls_attempted": 1}
    if source_id == "team_stats_lahman":
        rows = _github_raw_csv("cbwinslow", "baseballdatabank", "core/Teams.csv", max_records=max_records)
        if season is not None:
            rows = [row for row in rows if str(row.get("yearID") or row.get("season") or "") == season_text]
        return rows, {"downloads_attempted": 1, "downloads_succeeded": 1, "provider_calls_attempted": 1}
    if source_id == "player_master_lahman":
        rows = _github_raw_csv("cbwinslow", "baseballdatabank", "core/People.csv", max_records=max_records)
        return rows, {"downloads_attempted": 1, "downloads_succeeded": 1, "provider_calls_attempted": 1}
    if source_id == "park_factors_lahman":
        rows = _github_raw_csv("cbwinslow", "baseballdatabank", "core/Parks.csv", max_records=max_records)
        if season is not None:
            rows = [row for row in rows if str(row.get("yearID") or row.get("season") or "") == season_text]
        return rows, {"downloads_attempted": 1, "downloads_succeeded": 1, "provider_calls_attempted": 1}
    if source_id == "stadiums_lahman":
        rows = _github_raw_csv("cbwinslow", "baseballdatabank", "core/Parks.csv", max_records=max_records)
        return rows, {"downloads_attempted": 1, "downloads_succeeded": 1, "provider_calls_attempted": 1}
    if source_id == "awards_allstar_lahman":
        rows = _github_raw_csv("cbwinslow", "baseballdatabank", "core/AllstarFull.csv", max_records=max_records)
        if season is not None:
            rows = [row for row in rows if str(row.get("yearID") or row.get("season") or "") == season_text]
        return rows, {"downloads_attempted": 1, "downloads_succeeded": 1, "provider_calls_attempted": 1}
    if source_id == "franchises_lahman":
        rows = _github_raw_csv("cbwinslow", "baseballdatabank", "core/TeamsFranchises.csv", max_records=max_records)
        return rows, {"downloads_attempted": 1, "downloads_succeeded": 1, "provider_calls_attempted": 1}
    if source_id == "draft_lahman":
        url = f"{MLB_STATS_API_BASE}/draft/latest"
        try:
            payload = _http_get_json(url, headers={"Accept": "application/json"})
        except Exception:
            return [], {"downloads_attempted": 1, "downloads_succeeded": 0, "provider_calls_attempted": 1}
        rows: list[dict[str, Any]] = []
        for round_item in payload.get("drafts") or payload.get("rounds") or []:
            if not isinstance(round_item, dict):
                continue
            for pick in round_item.get("picks") or []:
                if not isinstance(pick, dict):
                    continue
                rows.append(
                    {
                        "playerID": (pick.get("player") or {}).get("id") if isinstance(pick.get("player"), dict) else None,
                        "yearID": payload.get("draftYear"),
                        "round": round_item.get("round"),
                        "pick": pick.get("pickNumber"),
                        "teamID": (pick.get("team") or {}).get("id") if isinstance(pick.get("team"), dict) else None,
                        "school": (pick.get("school") or {}).get("name") if isinstance(pick.get("school"), dict) else None,
                        "signed_flag": pick.get("signed"),
                        "source_label": "mlb_stats_api_draft",
                    }
                )
        return rows, {"downloads_attempted": 1, "downloads_succeeded": 1 if rows else 0, "provider_calls_attempted": 1}
    if source_id == "people_identifiers_chadwick":
        rows: list[dict[str, Any]] = []
        for name in ["people-0.csv", "people-1.csv", "people-2.csv", "people-3.csv", "people-4.csv", "people-5.csv", "people-6.csv", "people-7.csv", "people-8.csv", "people-9.csv", "people-a.csv", "people-b.csv", "people-c.csv", "people-d.csv", "people-e.csv", "people-f.csv"]:
            rows.extend(_github_raw_csv("chadwickbureau", "register", f"data/{name}", max_records=None if max_records is None else max_records))
            if max_records is not None and len(rows) >= int(max_records):
                return rows[: int(max_records)], {"downloads_attempted": 1, "downloads_succeeded": 1, "provider_calls_attempted": 1}
        rows = rows[: int(max_records)] if max_records is not None else rows
        return rows, {"downloads_attempted": 1, "downloads_succeeded": 1, "provider_calls_attempted": 1}
    if source_id == "minor_league_links_chadwick":
        rows = _github_raw_csv("chadwickbureau", "register", "data/links.csv", max_records=max_records)
        for row in rows:
            if not row.get("playerID"):
                row["playerID"] = row.get("key_mlbam") or row.get("key_retro") or row.get("key_bbref")
            if not row.get("season"):
                row["season"] = row.get("pro_played_first") or row.get("mlb_played_first")
            row.setdefault("minor_league_team", row.get("source"))
            row.setdefault("affiliate", row.get("value"))
            row.setdefault("level", row.get("source"))
        return rows, {"downloads_attempted": 1, "downloads_succeeded": 1, "provider_calls_attempted": 1}
    if source_id == "structured_wiki_seed" and source_kind == "structured_open_data":
        query = WikidataMlbSeedAdapter(source).build_wikidata_query(max_records=max_records or 250)
        payload = _http_get_json("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"format": "json", "query": query}), headers={"Accept": "application/sparql-results+json,application/json"})
        bindings = []
        if isinstance(payload.get("results"), dict):
            bindings = [row for row in payload["results"].get("bindings") or [] if isinstance(row, dict)]
        rows = WikidataMlbSeedAdapter(source).normalize_wikidata_records(bindings)
        if max_records is not None:
            rows = rows[: int(max_records)]
        return rows, {"downloads_attempted": 0, "downloads_succeeded": 0, "provider_calls_attempted": 1}
    if source_id in {"retrosheet_schedules_results", "retrosheet_game_logs", "retrosheet_play_by_play_events", "postseason_labels_retrosheet"}:
        game_rows, play_rows = _retrosheet_event_rows(season=season_text, max_records=max_records)
        if source_id in {"retrosheet_play_by_play_events", "play_by_play_events"}:
            rows = play_rows
        elif source_id in {"postseason_labels_retrosheet"}:
            rows = [row for row in game_rows if bool(row.get("postseason_flag"))]
        else:
            rows = game_rows
        return rows, {"downloads_attempted": 1, "downloads_succeeded": 1 if rows else 0, "provider_calls_attempted": 1}
    if source_id in {"rosters_mlb_stats_api", "transactions_mlb_stats_api", "standings_mlb_stats_api", "managers_coaches_mlb_stats_api", "injuries_mlb_stats_api", "lineups_mlb_stats_api", "probable_pitchers_mlb_stats_api", "starting_pitchers_mlb_stats_api", "bullpen_usage_mlb_stats_api", "defensive_positions_mlb_stats_api", "weather_mlb_stats_api", "umpires_officials_mlb_stats_api"}:
        if source_id == "rosters_mlb_stats_api":
            rows = _statsapi_roster_rows(season=season_text, max_records=max_records)
        elif source_id == "injuries_mlb_stats_api":
            rows = _statsapi_roster_rows(season=season_text, max_records=max_records)
            for row in rows:
                row["injury_status"] = row.get("status")
                row["source_label"] = "mlb_stats_api_injury_proxy"
        elif source_id == "transactions_mlb_stats_api":
            rows = _statsapi_transactions_rows(season=season_text, max_records=max_records)
        elif source_id == "standings_mlb_stats_api":
            rows = _statsapi_standings_rows(season=season_text)
            if max_records is not None:
                rows = rows[: int(max_records)]
        elif source_id == "managers_coaches_mlb_stats_api":
            rows = []
            teams = _statsapi_team_rows(season=season_text)
            for team in teams:
                team_id = team.get("team_id")
                if team_id is None:
                    continue
                url = f"{MLB_STATS_API_BASE}/teams/{team_id}/coaches?season={urllib.parse.quote(season_text)}"
                try:
                    payload = _http_get_json(url, headers={"Accept": "application/json"})
                except Exception:
                    return [], {"downloads_attempted": 1, "downloads_succeeded": 0, "provider_calls_attempted": 1}
                for item in payload.get("coaches") or []:
                    if not isinstance(item, dict):
                        continue
                    person = item.get("person") or {}
                    rows.append(
                        {
                            "team_id": team_id,
                            "season": season_text,
                            "manager_name": person.get("fullName"),
                            "coach_name": person.get("fullName"),
                            "role": item.get("job"),
                            "start_date": item.get("startDate"),
                            "end_date": item.get("endDate"),
                            "source_label": "mlb_stats_api_coaches",
                        }
                    )
                    if max_records is not None and len(rows) >= int(max_records):
                        break
        elif source_id == "weather_mlb_stats_api":
            rows = _statsapi_schedule_rows(season=season_text, max_records=max_records)
        elif source_id in {"lineups_mlb_stats_api", "defensive_positions_mlb_stats_api", "umpires_officials_mlb_stats_api", "probable_pitchers_mlb_stats_api", "starting_pitchers_mlb_stats_api", "bullpen_usage_mlb_stats_api"}:
            lineup_rows, official_rows, probable_rows, starting_rows, bullpen_rows, _play_rows = _statsapi_game_feed_rows(season=season_text, max_records=max_records)
            if source_id in {"lineups_mlb_stats_api", "defensive_positions_mlb_stats_api"}:
                rows = lineup_rows
            elif source_id == "umpires_officials_mlb_stats_api":
                rows = official_rows
            elif source_id == "probable_pitchers_mlb_stats_api":
                rows = probable_rows
            elif source_id == "starting_pitchers_mlb_stats_api":
                rows = starting_rows
            else:
                rows = bullpen_rows
        else:
            rows = []
        return rows, {"downloads_attempted": 1, "downloads_succeeded": 1 if rows else 0, "provider_calls_attempted": 1}
    return [], {"downloads_attempted": 0, "downloads_succeeded": 0, "provider_calls_attempted": 0}


def _source_gate(source: dict[str, Any]) -> str | None:
    if not source.get("current_phase_allowed"):
        return "source_not_current_phase_allowed"
    if source.get("paid_or_freemium") or source.get("requires_budget_approval") or source.get("future_paid_candidate"):
        return "unsafe_source"
    if source.get("requires_auth") or source.get("requires_api_key"):
        return "unsafe_source"
    if source.get("source_kind") == "manual_csv" and not source.get("manual_import_supported"):
        return "manual_import_not_authorized"
    if source.get("raw_html_required") and source.get("terms_review_status") not in {"reviewed_open_allowed"}:
        return "terms_review_required"
    if source.get("approval_status") == "blocked":
        return source.get("blockers", ["unsupported_source"])[0]
    return None


def _choose_text(value: Any) -> str | None:
    text = _clean(value)
    return text or None


def _parse_date(value: Any) -> str | None:
    text = _clean(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%Y%m%d"):
            try:
                return datetime.strptime(text[:10] if fmt == "%Y-%m-%d" else text, fmt).date().isoformat()
            except ValueError:
                continue
    return None


def _has_risk(value: Any, *, markers: tuple[str, ...]) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            lower = str(key).lower()
            if lower in RAW_PAYLOAD_KEYS:
                return True
            if any(marker in lower for marker in markers) and _real_value(nested):
                return True
            if _has_risk(nested, markers=markers):
                return True
    elif isinstance(value, list):
        return any(_has_risk(item, markers=markers) for item in value[:100])
    return False


def _canonicalize_row(row: dict[str, Any], source: dict[str, Any], *, index: int = 0) -> dict[str, Any]:
    safe = {str(key): _safe_scalar(value) for key, value in row.items() if isinstance(value, (str, int, float, bool)) or value is None}
    source_id = str(source["source_id"])
    category = str(source["data_category"])
    season = _choose_text(safe.get("season") or safe.get("year") or safe.get("yearID") or safe.get("season_year"))
    event_date = _parse_date(safe.get("event_date") or safe.get("game_date") or safe.get("date") or safe.get("gameday") or safe.get("timestamp"))
    game_id = _choose_text(safe.get("game_id") or safe.get("game_pk") or safe.get("gamePk") or safe.get("gameid") or safe.get("old_game_id"))
    team = _choose_text(safe.get("team") or safe.get("team_id") or safe.get("teamID") or safe.get("home_team") or safe.get("away_team") or safe.get("recent_team") or safe.get("team_abbr"))
    player_id = _choose_text(safe.get("player_id") or safe.get("playerID") or safe.get("person_id") or safe.get("mlbam") or safe.get("key_mlbam"))
    row_id = _choose_text(safe.get("record_id") or safe.get("id") or safe.get("transaction_id") or safe.get("play_id"))
    if not row_id:
        row_id = f"{source_id}:{index}:{game_id or season or player_id or team or 'row'}"
    compact = {
        "module": MLB_MODULE,
        "source_id": source_id,
        "source_family": source.get("source_family"),
        "data_category": category,
        "record_id": row_id,
        "season": season,
        "event_date": event_date,
        "game_id": game_id,
        "team": team,
        "player_id": player_id,
        "home_team": _choose_text(safe.get("home_team") or safe.get("home_team_name")),
        "away_team": _choose_text(safe.get("away_team") or safe.get("away_team_name")),
        "home_score": safe.get("home_score") or safe.get("home_runs") or safe.get("runs_scored"),
        "away_score": safe.get("away_score") or safe.get("away_runs") or safe.get("runs_allowed"),
        "runs_scored": safe.get("runs_scored"),
        "runs_allowed": safe.get("runs_allowed"),
        "winner": _choose_text(safe.get("winner") or safe.get("winning_team")),
        "final_result": _choose_text(safe.get("final_result") or safe.get("result") or safe.get("outcome")),
        "game_type": _choose_text(safe.get("game_type") or safe.get("season_type")),
        "playoff_round": _choose_text(safe.get("playoff_round")),
        "postseason_flag": safe.get("postseason_flag"),
        "postseason_label": _choose_text(safe.get("postseason_label")),
        "pitcher": _choose_text(safe.get("pitcher") or safe.get("pitcher_name")),
        "batter": _choose_text(safe.get("batter") or safe.get("batter_name")),
        "pitch_type": _choose_text(safe.get("pitch_type")),
        "pitch_number": safe.get("pitch_number"),
        "launch_speed": safe.get("launch_speed") or safe.get("exit_velocity"),
        "launch_angle": safe.get("launch_angle"),
        "batting_order": safe.get("batting_order"),
        "lineup_slot": safe.get("lineup_slot"),
        "position": _choose_text(safe.get("position") or safe.get("fielding_position")),
        "status": _choose_text(safe.get("status") or safe.get("report_status")),
        "injury_status": _choose_text(safe.get("injury_status") or safe.get("injury_note")),
        "manager_name": _choose_text(safe.get("manager_name") or safe.get("staff_name")),
        "franchID": _choose_text(safe.get("franchID")),
        "park_id": _choose_text(safe.get("park_id") or safe.get("venue_id")),
        "park_name": _choose_text(safe.get("park_name") or safe.get("venue_name")),
        "stadium": _choose_text(safe.get("stadium") or safe.get("venue")),
        "temperature": safe.get("temperature") or safe.get("temp"),
        "wind_speed": safe.get("wind_speed") or safe.get("wind"),
        "moneyline": safe.get("moneyline"),
        "spread_line": safe.get("spread_line"),
        "total_line": safe.get("total_line"),
        "wikidata_qid": _choose_text(safe.get("wikidata_qid")),
        "wikipedia_title": _choose_text(safe.get("wikipedia_title")),
        "source_label": _choose_text(safe.get("source_label")) or source.get("source_name"),
        "source_license": _choose_text(safe.get("source_license")) or source.get("license_status"),
        "validation_status": "available",
        "blocked_reason": "available",
        "data_kind": "real_open_data",
        "is_synthetic": False,
        "raw_payload_included": False,
    }
    for key, value in safe.items():
        if key not in compact and value not in (None, "", [], {}):
            compact[key] = value
    return compact


class MlbOpenDataAdapter:
    def __init__(self, source: dict[str, Any]):
        self.source = source

    @property
    def user_agent(self) -> str:
        return HTTP_USER_AGENT

    @property
    def spoofing_used(self) -> bool:
        return False

    @property
    def browser_impersonation_used(self) -> bool:
        return False

    @property
    def raw_html_persisted(self) -> bool:
        return False

    def describe_source(self) -> dict[str, Any]:
        return {
            "source_id": self.source.get("source_id"),
            "source_family": self.source.get("source_family"),
            "source_kind": self.source.get("source_kind"),
            "data_category": self.source.get("data_category"),
            "approval_status": self.source.get("approval_status"),
            "terms_review_status": self.source.get("terms_review_status"),
            "license_status": self.source.get("license_status"),
            "user_agent": self.user_agent,
            "spoofs_user_agent": False,
            "browser_impersonation_used": False,
            "raw_html_persisted": False,
        }

    def resolve_source_metadata(self) -> dict[str, Any]:
        return {
            "source_id": self.source.get("source_id"),
            "source_name": self.source.get("source_name"),
            "source_family": self.source.get("source_family"),
            "source_kind": self.source.get("source_kind"),
            "expected_fields": list(self.source.get("expected_fields") or []),
            "expected_join_keys": list(self.source.get("expected_join_keys") or []),
            "expected_granularity": self.source.get("expected_granularity"),
            "likely_supported_features": list(self.source.get("likely_supported_features") or []),
            "blocked_features": list(self.source.get("blocked_features") or []),
            "blockers": list(self.source.get("blockers") or []),
            "approval_status": self.source.get("approval_status"),
        }

    def list_expected_fields(self) -> list[str]:
        return list(self.source.get("expected_fields") or [])

    def validate_sample_shape(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        required = [field for field in (self.source.get("expected_join_keys") or []) if field]
        present = set()
        for row in records:
            present.update({str(key) for key, value in row.items() if _real_value(value)})
        missing = [field for field in required if field not in present]
        ok = not missing
        return {
            "ok": ok,
            "missing_required_fields": missing,
            "required_fields": required,
            "present_fields": sorted(present),
        }

    def normalize_records(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [_canonicalize_row(row, self.source, index=index) for index, row in enumerate(rows)]

    def _blocked(self, gate: str, blocker: str, *, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        return mlb_safe_payload(
            {
                "ok": False,
                "status": "blocked",
                "schema_version": MLB_OPEN_DATA_ADAPTER_SCHEMA_VERSION,
                "created_at": utc_now_iso(),
                "run_id": sanitize_filename(f"mlb_{gate}_{self.source['source_id']}_{uuid4().hex[:8]}"),
                "source_id": self.source.get("source_id"),
                "source_name": self.source.get("source_name"),
                "source_family": self.source.get("source_family"),
                "data_category": self.source.get("data_category"),
                "module": MLB_MODULE,
                "gate": gate,
                "blocked_reason": blocker if blocker in BLOCKED_REASONS else "unsupported_source",
                "metadata": metadata or self.resolve_source_metadata(),
                "records_validated": 0,
                "records_rejected": 0,
                "sample_rows": [],
                "fields_available": [],
                "field_types": {},
                "field_count": 0,
                "seasons_available": [],
                "seasons_backfilled": [],
                "downloads_attempted": 0,
                "downloads_succeeded": 0,
                "provider_calls_attempted": 0,
                "provider_calls_succeeded": 0,
                "provider_calls_failed": 0,
                "next_safe_action": "resolve blocker before retrying",
            }
        )

    def _read_rows_from_input(
        self,
        *,
        input_path: str | Path | None = None,
        input_rows: list[dict[str, Any]] | None = None,
        fetch_fn: Callable[[str], Any] | None = None,
        season: int | str | None = None,
        max_records: int | None = None,
        allow_download: bool = False,
        allow_structured_seed: bool = False,
        allow_manual_import: bool = False,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        source_kind = str(self.source.get("source_kind") or "")
        if input_rows is not None:
            return [row for row in input_rows if isinstance(row, dict)], {"fetch_attempted": False, "downloads_attempted": 0, "downloads_succeeded": 0, "provider_calls_attempted": 0}
        if input_path:
            path = Path(input_path)
            if path.suffix.lower() == ".csv":
                return _read_csv(path), {"fetch_attempted": False, "downloads_attempted": 0, "downloads_succeeded": 0, "provider_calls_attempted": 0}
            if path.suffix.lower() in {".json", ".jsonl"}:
                rows = _read_json_rows(path)
                return rows, {"fetch_attempted": False, "downloads_attempted": 0, "downloads_succeeded": 0, "provider_calls_attempted": 0}
        if source_kind == "manual_csv":
            if not allow_manual_import:
                raise PermissionError("manual import not authorized")
            import_dir = Path(input_path) if input_path else None
            rows: list[dict[str, Any]] = []
            if import_dir and import_dir.exists() and import_dir.is_file():
                rows = _read_csv(import_dir)
            elif import_dir and import_dir.exists() and import_dir.is_dir():
                for csv_path in sorted(import_dir.glob("*.csv")):
                    rows.extend(_read_csv(csv_path))
            return rows, {"fetch_attempted": False, "downloads_attempted": 0, "downloads_succeeded": 0, "provider_calls_attempted": 0}
        if source_kind == "structured_open_data":
            if not allow_structured_seed:
                raise PermissionError("structured seed disabled by default")
            payload = fetch_fn(self.source["source_id"]) if fetch_fn else None
            if payload is None and fetch_fn is None:
                rows, meta = _fetch_open_mlb_rows(self.source, season=season, max_records=max_records)
                return rows, meta
            if isinstance(payload, dict):
                for key in ("items", "records", "rows", "data", "bindings"):
                    if isinstance(payload.get(key), list):
                        rows = [row for row in payload[key] if isinstance(row, dict)]
                        return rows, {"fetch_attempted": True, "downloads_attempted": 0, "downloads_succeeded": 0, "provider_calls_attempted": 1}
            if isinstance(payload, list):
                return [row for row in payload if isinstance(row, dict)], {"fetch_attempted": True, "downloads_attempted": 0, "downloads_succeeded": 0, "provider_calls_attempted": 1}
            raise ConnectionError("structured_seed_fetch_error")
        if not allow_download:
            raise PermissionError("download not allowed")
        if fetch_fn is None:
            rows, meta = _fetch_open_mlb_rows(self.source, season=season, max_records=max_records)
            if rows or meta.get("downloads_attempted") or meta.get("provider_calls_attempted"):
                return rows, meta
            raise NotImplementedError("download not implemented")
        payload = fetch_fn(self.source["source_id"])
        if isinstance(payload, list):
            rows = [row for row in payload if isinstance(row, dict)]
        elif isinstance(payload, dict):
            rows = []
            for key in ("items", "records", "rows", "data", "games", "results", "people", "teams"):
                if isinstance(payload.get(key), list):
                    rows = [row for row in payload[key] if isinstance(row, dict)]
                    break
        else:
            rows = []
        return rows, {"fetch_attempted": True, "downloads_attempted": 1, "downloads_succeeded": int(bool(rows)), "provider_calls_attempted": 1}

    def _build_result(
        self,
        *,
        gate: str,
        rows: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
        allow_download: bool = False,
        allow_structured_seed: bool = False,
        allow_manual_import: bool = False,
        blocked_reason: str | None = None,
        downloads_attempted: int = 0,
        downloads_succeeded: int = 0,
        provider_calls_attempted: int = 0,
        provider_calls_succeeded: int = 0,
        provider_calls_failed: int = 0,
        season: int | str | None = None,
    ) -> dict[str, Any]:
        normalized = self.normalize_records(rows)
        valid_rows = [row for row in normalized if row.get("validation_status") == "available"]
        rejected_rows = [row for row in normalized if row.get("validation_status") != "available"]
        fields_seen: set[str] = set()
        field_types: dict[str, Counter[str]] = defaultdict(Counter)
        seasons: set[str] = set()
        teams: set[str] = set()
        players: set[str] = set()
        games: set[str] = set()
        sample_rows = valid_rows[:MAX_SAMPLE_ROWS_TO_PERSIST]
        for row in valid_rows:
            for key, value in row.items():
                if key == "raw_payload_included":
                    continue
                if _real_value(value):
                    fields_seen.add(str(key))
                    field_types[str(key)][_field_type(value)] += 1
            if _real_value(row.get("season")):
                seasons.add(str(row["season"]))
            if _real_value(row.get("team")):
                teams.add(str(row["team"]))
            if _real_value(row.get("player_id")):
                players.add(str(row["player_id"]))
            if _real_value(row.get("game_id")):
                games.add(str(row["game_id"]))
        sample_shape = self.validate_sample_shape(valid_rows)
        status = "ok"
        if blocked_reason and valid_rows:
            status = "partial"
        elif blocked_reason:
            status = "blocked"
        elif gate == "metadata_check":
            status = "metadata_ready"
        elif gate == "tiny_sample":
            status = "sample_ready"
        elif gate == "one_season_import":
            status = "one_season_import_complete"
        elif gate == "small_window_import":
            status = "small_window_import_complete"
        elif gate == "full_available_backfill":
            status = "full_backfill_complete"
        record_count = len(valid_rows)
        return mlb_safe_payload(
            {
                "ok": bool(valid_rows) or gate == "metadata_check" or blocked_reason is not None,
                "status": status,
                "schema_version": MLB_OPEN_DATA_ADAPTER_SCHEMA_VERSION,
                "created_at": utc_now_iso(),
                "run_id": sanitize_filename(f"mlb_{gate}_{self.source['source_id']}_{uuid4().hex[:8]}"),
                "source_id": self.source.get("source_id"),
                "source_name": self.source.get("source_name"),
                "source_family": self.source.get("source_family"),
                "data_category": self.source.get("data_category"),
                "module": MLB_MODULE,
                "gate": gate,
                "season": str(season) if season is not None else None,
                "blocked_reason": blocked_reason,
                "metadata": metadata or self.resolve_source_metadata(),
                "records_validated": record_count,
                "records_rejected": len(rejected_rows),
                "sample_rows": sample_rows,
                "fields_available": sorted(fields_seen),
                "field_types": {field: counts.most_common(1)[0][0] for field, counts in field_types.items()},
                "field_count": len(fields_seen),
                "seasons_available": sorted(seasons),
                "seasons_backfilled": sorted(seasons),
                "teams_covered": sorted(teams),
                "players_covered": sorted(players),
                "games_covered": sorted(games),
                "sample_shape": sample_shape,
                "downloads_attempted": downloads_attempted,
                "downloads_succeeded": downloads_succeeded,
                "provider_calls_attempted": provider_calls_attempted,
                "provider_calls_succeeded": provider_calls_succeeded,
                "provider_calls_failed": provider_calls_failed,
                "next_safe_action": "continue next gate" if not blocked_reason else "resolve blocker before retrying",
            }
        )

    def run_metadata_check(self) -> dict[str, Any]:
        blocker = _source_gate(self.source)
        return self._build_result(gate="metadata_check", rows=[], metadata=self.resolve_source_metadata(), blocked_reason=blocker)

    def run_tiny_sample(
        self,
        *,
        allow_download: bool = False,
        season: int | str | None = None,
        max_records: int | None = None,
        input_path: str | Path | None = None,
        input_rows: list[dict[str, Any]] | None = None,
        fetch_fn: Callable[[str], Any] | None = None,
        allow_structured_seed: bool = False,
        allow_manual_import: bool = False,
    ) -> dict[str, Any]:
        blocker = _source_gate(self.source)
        if blocker:
            return self._blocked("tiny_sample", blocker)
        try:
            rows, meta = self._read_rows_from_input(
                input_path=input_path,
                input_rows=input_rows,
                fetch_fn=fetch_fn,
                season=season,
                max_records=max_records,
                allow_download=allow_download,
                allow_structured_seed=allow_structured_seed,
                allow_manual_import=allow_manual_import,
            )
        except PermissionError as exc:
            return self._blocked("tiny_sample", "download_not_allowed" if "download" in str(exc).lower() else "manual_import_not_authorized" if "manual" in str(exc).lower() else "structured_seed_disabled_by_default")
        except NotImplementedError:
            return self._blocked("tiny_sample", "download_not_implemented")
        except ConnectionError:
            return self._blocked("tiny_sample", "structured_seed_fetch_error")
        if max_records is not None:
            rows = rows[: int(max_records)]
        return self._build_result(
            gate="tiny_sample",
            rows=rows,
            metadata=self.resolve_source_metadata(),
            blocked_reason=None if rows else "no_records_found",
            downloads_attempted=int(meta.get("downloads_attempted", 0) or 0),
            downloads_succeeded=int(meta.get("downloads_succeeded", 0) or 0),
            provider_calls_attempted=int(meta.get("provider_calls_attempted", 0) or 0),
            provider_calls_succeeded=int(bool(rows)) if meta.get("provider_calls_attempted") else 0,
            provider_calls_failed=max(
                0,
                int(meta.get("provider_calls_attempted", 0) or 0) - (1 if rows and meta.get("provider_calls_attempted") else 0),
            ),
        )

    def run_one_season_import(
        self,
        *,
        season: int | str | None,
        allow_download: bool = False,
        input_path: str | Path | None = None,
        input_rows: list[dict[str, Any]] | None = None,
        fetch_fn: Callable[[str], Any] | None = None,
        allow_structured_seed: bool = False,
        allow_manual_import: bool = False,
        season_filter: str | None = None,
    ) -> dict[str, Any]:
        if season is None or str(season).strip() == "":
            return self._blocked("one_season_import", "missing_season")
        try:
            rows, meta = self._read_rows_from_input(
                input_path=input_path,
                input_rows=input_rows,
                fetch_fn=fetch_fn,
                season=season,
                max_records=None,
                allow_download=allow_download,
                allow_structured_seed=allow_structured_seed,
                allow_manual_import=allow_manual_import,
            )
        except PermissionError as exc:
            return self._blocked("one_season_import", "download_not_allowed" if "download" in str(exc).lower() else "manual_import_not_authorized" if "manual" in str(exc).lower() else "structured_seed_disabled_by_default")
        except NotImplementedError:
            return self._blocked("one_season_import", "download_not_implemented")
        except ConnectionError:
            return self._blocked("one_season_import", "structured_seed_fetch_error")
        rows = [row for row in list(rows or []) if str(row.get("season") or row.get("year") or row.get("yearID") or "") == str(season)]
        if season_filter:
            rows = [row for row in rows if str(row.get("season") or "") == season_filter]
        if not rows:
            return self._blocked("one_season_import", "no_records_found")
        result = self._build_result(
            gate="one_season_import",
            rows=rows,
            metadata=self.resolve_source_metadata(),
            season=season,
            downloads_attempted=int(meta.get("downloads_attempted", 0) or 0),
            downloads_succeeded=int(meta.get("downloads_succeeded", 0) or 0),
            provider_calls_attempted=int(meta.get("provider_calls_attempted", 0) or 0),
            provider_calls_succeeded=int(bool(rows)) if meta.get("provider_calls_attempted") else 0,
            provider_calls_failed=max(0, int(meta.get("provider_calls_attempted", 0) or 0) - (1 if rows and meta.get("provider_calls_attempted") else 0)),
        )
        result["one_season"] = str(season)
        return result

    def run_small_window_import(
        self,
        *,
        season: int | str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        allow_download: bool = False,
        input_path: str | Path | None = None,
        input_rows: list[dict[str, Any]] | None = None,
        fetch_fn: Callable[[str], Any] | None = None,
        allow_structured_seed: bool = False,
        allow_manual_import: bool = False,
    ) -> dict[str, Any]:
        try:
            rows, meta = self._read_rows_from_input(
                input_path=input_path,
                input_rows=input_rows,
                fetch_fn=fetch_fn,
                season=season,
                max_records=None,
                allow_download=allow_download,
                allow_structured_seed=allow_structured_seed,
                allow_manual_import=allow_manual_import,
            )
        except PermissionError as exc:
            return self._blocked("small_window_import", "download_not_allowed" if "download" in str(exc).lower() else "manual_import_not_authorized" if "manual" in str(exc).lower() else "structured_seed_disabled_by_default")
        except NotImplementedError:
            return self._blocked("small_window_import", "download_not_implemented")
        except ConnectionError:
            return self._blocked("small_window_import", "structured_seed_fetch_error")
        filtered_rows = []
        for row in list(rows or []):
            event_date = row.get("event_date")
            if start_date and event_date and str(event_date) < str(start_date):
                continue
            if end_date and event_date and str(event_date) > str(end_date):
                continue
            filtered_rows.append(row)
        if not filtered_rows:
            return self._blocked("small_window_import", "no_records_found")
        return self._build_result(
            gate="small_window_import",
            rows=filtered_rows,
            metadata=self.resolve_source_metadata(),
            downloads_attempted=int(meta.get("downloads_attempted", 0) or 0),
            downloads_succeeded=int(meta.get("downloads_succeeded", 0) or 0),
            provider_calls_attempted=int(meta.get("provider_calls_attempted", 0) or 0),
            provider_calls_succeeded=int(bool(filtered_rows)) if meta.get("provider_calls_attempted") else 0,
            provider_calls_failed=max(0, int(meta.get("provider_calls_attempted", 0) or 0) - (1 if filtered_rows and meta.get("provider_calls_attempted") else 0)),
        )

    def run_full_available_backfill(
        self,
        *,
        season: int | str | None = None,
        allow_download: bool = False,
        input_path: str | Path | None = None,
        input_rows: list[dict[str, Any]] | None = None,
        fetch_fn: Callable[[str], Any] | None = None,
        allow_structured_seed: bool = False,
        allow_manual_import: bool = False,
        max_full_assets: int | None = None,
        seasons: list[int | str] | None = None,
    ) -> dict[str, Any]:
        try:
            rows, meta = self._read_rows_from_input(
                input_path=input_path,
                input_rows=input_rows,
                fetch_fn=fetch_fn,
                season=season,
                max_records=None,
                allow_download=allow_download,
                allow_structured_seed=allow_structured_seed,
                allow_manual_import=allow_manual_import,
            )
        except PermissionError as exc:
            return self._blocked("full_available_backfill", "download_not_allowed" if "download" in str(exc).lower() else "manual_import_not_authorized" if "manual" in str(exc).lower() else "structured_seed_disabled_by_default")
        except NotImplementedError:
            return self._blocked("full_available_backfill", "download_not_implemented")
        except ConnectionError:
            return self._blocked("full_available_backfill", "structured_seed_fetch_error")
        rows = list(rows or [])
        if seasons:
            seasons_set = {str(season) for season in seasons}
            rows = [row for row in rows if str(row.get("season") or "") in seasons_set]
        if max_full_assets is not None:
            rows = rows[: int(max_full_assets)]
        if not rows:
            return self._blocked("full_available_backfill", "no_records_found")
        result = self._build_result(
            gate="full_available_backfill",
            rows=rows,
            metadata=self.resolve_source_metadata(),
            downloads_attempted=int(meta.get("downloads_attempted", 0) or 0),
            downloads_succeeded=int(meta.get("downloads_succeeded", 0) or 0),
            provider_calls_attempted=int(meta.get("provider_calls_attempted", 0) or 0),
            provider_calls_succeeded=int(bool(rows)) if meta.get("provider_calls_attempted") else 0,
            provider_calls_failed=max(0, int(meta.get("provider_calls_attempted", 0) or 0) - (1 if rows and meta.get("provider_calls_attempted") else 0)),
        )
        result["seasons_requested"] = [str(season) for season in seasons or []]
        return result

    def write_compact_validated_rows(self, report: dict[str, Any], *, base_data_dir: str | Path | None = None) -> dict[str, str]:
        rows = [row for row in list(report.get("sample_rows") or []) if isinstance(row, dict)]
        root = mlb_validated_root(str(self.source.get("source_id")), base_data_dir)
        run_id = sanitize_filename(str(report.get("run_id") or f"mlb_validated_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"))
        latest_json = root / "latest.json"
        latest_md = root / "latest.md"
        item_json = root / "items" / f"{run_id}.json"
        paths = {
            "latest_json_path": mlb_rel(latest_json, base_data_dir),
            "latest_markdown_path": mlb_rel(latest_md, base_data_dir),
            "item_json_path": mlb_rel(item_json, base_data_dir),
        }
        payload = mlb_safe_payload(
            {
                **report,
                **paths,
                "sample_rows": rows[:MAX_SAMPLE_ROWS_TO_PERSIST],
                "validated_rows": rows,
            }
        )
        by_season: dict[str, list[dict[str, Any]]] = defaultdict(list)
        by_team: dict[str, list[dict[str, Any]]] = defaultdict(list)
        by_player: dict[str, list[dict[str, Any]]] = defaultdict(list)
        by_game: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            if _real_value(row.get("season")):
                by_season[str(row["season"])].append(row)
            if _real_value(row.get("team")):
                by_team[str(row["team"])].append(row)
            if _real_value(row.get("player_id")):
                by_player[str(row["player_id"])].append(row)
            if _real_value(row.get("game_id")):
                by_game[str(row["game_id"])].append(row)
        mlb_atomic_write_json(latest_json, payload)
        mlb_atomic_write_text(latest_md, _render_validated_markdown(payload))
        mlb_atomic_write_json(item_json, payload)
        for season, season_rows in sorted(by_season.items()):
            season_path = root / "by_season" / f"{sanitize_filename(season)}.json"
            mlb_atomic_write_json(season_path, mlb_safe_payload({**payload, "scope": "season", "scope_value": season, "sample_rows": season_rows[:MAX_SAMPLE_ROWS_TO_PERSIST], "records_validated": len(season_rows)}))
            paths.setdefault("by_season_paths", []).append(mlb_rel(season_path, base_data_dir))
        for team, team_rows in sorted(by_team.items()):
            team_path = root / "by_team" / f"{sanitize_filename(team)}.json"
            mlb_atomic_write_json(team_path, mlb_safe_payload({**payload, "scope": "team", "scope_value": team, "sample_rows": team_rows[:MAX_SAMPLE_ROWS_TO_PERSIST], "records_validated": len(team_rows)}))
            paths.setdefault("by_team_paths", []).append(mlb_rel(team_path, base_data_dir))
        for player, player_rows in sorted(by_player.items()):
            player_path = root / "by_player" / f"{sanitize_filename(player)}.json"
            mlb_atomic_write_json(player_path, mlb_safe_payload({**payload, "scope": "player", "scope_value": player, "sample_rows": player_rows[:MAX_SAMPLE_ROWS_TO_PERSIST], "records_validated": len(player_rows)}))
            paths.setdefault("by_player_paths", []).append(mlb_rel(player_path, base_data_dir))
        for game_id, game_rows in sorted(by_game.items()):
            game_path = root / "by_game" / f"{sanitize_filename(game_id)}.json"
            mlb_atomic_write_json(game_path, mlb_safe_payload({**payload, "scope": "game", "scope_value": game_id, "sample_rows": game_rows[:MAX_SAMPLE_ROWS_TO_PERSIST], "records_validated": len(game_rows)}))
            paths.setdefault("by_game_paths", []).append(mlb_rel(game_path, base_data_dir))
        return paths

    def build_compact_report(self, *, base_data_dir: str | Path | None = None) -> dict[str, Any]:
        metadata = self.resolve_source_metadata()
        blocker = _source_gate(self.source)
        report = self._build_result(gate="metadata_check", rows=[], metadata=metadata, blocked_reason=blocker)
        report.update(
            {
                "no_predictive_claim": True,
                "spoofing_used": False,
                "browser_impersonation_used": False,
                "raw_html_persisted": False,
                "provider_write": False,
                "execution_allowed": False,
                "enabled_source_count": 0,
                "paid_source_enabled_count": 0,
            }
        )
        return report


class WikidataMlbSeedAdapter(MlbOpenDataAdapter):
    def build_wikidata_query(self, *, max_records: int = 500) -> str:
        return f"""
SELECT ?item ?itemLabel ?itemDescription ?instance_of ?instance_ofLabel ?article ?website ?lat ?lon ?inception ?dissolution WHERE {{
  VALUES ?instance_of {{ wd:Q13393265 wd:Q321749 wd:Q847017 }}
  ?item wdt:P31 ?instance_of .
  OPTIONAL {{ ?item sitelinks:enwiki ?article. }}
  OPTIONAL {{ ?item wdt:P856 ?website. }}
  OPTIONAL {{ ?item wdt:P625 ?coord. BIND(geof:latitude(?coord) AS ?lat) BIND(geof:longitude(?coord) AS ?lon) }}
  OPTIONAL {{ ?item wdt:P571 ?inception. }}
  OPTIONAL {{ ?item wdt:P576 ?dissolution. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
LIMIT {int(max_records)}
"""

    def normalize_wikidata_records(self, bindings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for binding in bindings:
            qid = _choose_text((binding.get("item") or {}).get("value"))
            if qid and "/" in qid:
                qid = qid.rsplit("/", 1)[-1]
            rows.append(
                {
                    "wikidata_qid": qid,
                    "label": _choose_text((binding.get("itemLabel") or {}).get("value")),
                    "description": _choose_text((binding.get("itemDescription") or {}).get("value")),
                    "instance_of": _choose_text((binding.get("instance_ofLabel") or {}).get("value")),
                    "wikipedia_title": _choose_text((binding.get("article") or {}).get("value")),
                    "official_website": _choose_text((binding.get("website") or {}).get("value")),
                    "latitude": _choose_text((binding.get("lat") or {}).get("value")),
                    "longitude": _choose_text((binding.get("lon") or {}).get("value")),
                    "inception": _choose_text((binding.get("inception") or {}).get("value")),
                    "dissolution": _choose_text((binding.get("dissolution") or {}).get("value")),
                    "source_license": "cc0",
                    "source_label": self.source.get("source_name"),
                }
            )
        return rows

    def run_structured_seed_import(
        self,
        *,
        allow_structured_seed: bool = False,
        max_records: int | None = None,
        fetch_fn: Callable[[str], Any] | None = None,
        persist_preview: bool = False,
        base_data_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        blocker = _source_gate(self.source)
        if blocker:
            return self._blocked("structured_seed_import", blocker)
        if not allow_structured_seed:
            return self._blocked("structured_seed_import", "structured_seed_disabled_by_default")
        cap = int(max_records) if max_records is not None else 250
        query = self.build_wikidata_query(max_records=cap)
        try:
            payload = fetch_fn(query) if fetch_fn else None
        except Exception as exc:
            return self._blocked("structured_seed_import", "structured_seed_fetch_error", metadata={"error": type(exc).__name__})
        bindings = []
        if isinstance(payload, dict) and isinstance(payload.get("results"), dict) and isinstance(payload["results"].get("bindings"), list):
            bindings = [row for row in payload["results"]["bindings"] if isinstance(row, dict)]
        rows = self.normalize_wikidata_records(bindings)[:cap]
        if not rows:
            return self._blocked("structured_seed_import", "no_records_found")
        result = self._build_result(
            gate="structured_seed_import",
            rows=rows,
            metadata=self.resolve_source_metadata(),
            allow_structured_seed=True,
            provider_calls_attempted=1 if fetch_fn or payload is not None else 0,
            provider_calls_succeeded=1 if rows else 0,
            provider_calls_failed=0 if rows else 1,
        )
        result["license_status"] = "cc0"
        result["structured_seed"] = "wikidata"
        if persist_preview:
            result.update(self.write_compact_validated_rows(result, base_data_dir=base_data_dir))
        return result

    def run_tiny_sample(self, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("allow_structured_seed", True)
        kwargs.setdefault("max_records", 10)
        return self.run_structured_seed_import(**kwargs)

    def build_compact_report(self, *, base_data_dir: str | Path | None = None) -> dict[str, Any]:
        report = super().build_compact_report(base_data_dir=base_data_dir)
        report["license_status"] = "cc0"
        report["structured_seed"] = "wikidata"
        return report


class WikipediaMlbSeedAdapter(MlbOpenDataAdapter):
    def build_attribution_note(self) -> dict[str, Any]:
        return {
            "source_id": self.source.get("source_id"),
            "license_status": "cc_by_sa",
            "attribution_required": True,
            "attribution_text": "Content derived from Wikipedia, licensed CC BY-SA.",
            "usage": "supplemental_page_title_and_provenance_only",
            "parses_article_prose": False,
            "persists_raw_text": False,
        }

    def run_structured_seed_import(self, **kwargs: Any) -> dict[str, Any]:
        return mlb_safe_payload(
            {
                "ok": True,
                "status": "blocked",
                "schema_version": MLB_OPEN_DATA_ADAPTER_SCHEMA_VERSION,
                "created_at": utc_now_iso(),
                "run_id": sanitize_filename(f"mlb_structured_seed_{self.source['source_id']}_{uuid4().hex[:8]}"),
                "source_id": self.source.get("source_id"),
                "source_family": self.source.get("source_family"),
                "data_category": self.source.get("data_category"),
                "module": MLB_MODULE,
                "gate": "structured_seed_import",
                "blocked_reason": "supplemental_only_no_record_ingestion",
                "metadata": self.resolve_source_metadata(),
                "attribution": self.build_attribution_note(),
                "records_validated": 0,
                "records_rejected": 0,
                "sample_rows": [],
                "fields_available": [],
                "field_count": 0,
                "provider_calls_attempted": 0,
                "downloads_attempted": 0,
                "downloads_succeeded": 0,
                "provider_write": False,
                "execution_allowed": False,
                "no_predictive_claim": True,
                "parses_article_prose": False,
            }
        )


class ManualCsvImportAdapter(MlbOpenDataAdapter):
    def run_manual_import(
        self,
        *,
        input_path: str | Path | None = None,
        allow_manual_import: bool = False,
        max_records: int | None = None,
        persist_preview: bool = False,
        base_data_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        blocker = _source_gate(self.source)
        if blocker:
            return self._blocked("manual_import", blocker)
        if not allow_manual_import:
            return self._blocked("manual_import", "manual_import_not_authorized")
        rows: list[dict[str, Any]] = []
        paths: list[Path] = []
        if input_path:
            path = Path(input_path)
            if path.is_file():
                paths = [path]
            elif path.is_dir():
                paths = sorted(path.glob("*.csv"))
        if not paths:
            return self._blocked("manual_import", "no_records_found")
        rejected = 0
        for path in paths:
            try:
                for raw in _read_csv(path):
                    if not _clean(raw.get("source_license")):
                        rejected += 1
                        continue
                    rows.append(raw)
                    if max_records is not None and len(rows) >= int(max_records):
                        break
            except (csv.Error, OSError, UnicodeDecodeError):
                rejected += 1
        if not rows:
            return self._blocked("manual_import", "no_records_found")
        result = self._build_result(
            gate="manual_import",
            rows=rows,
            metadata=self.resolve_source_metadata(),
            blocked_reason=None,
        )
        result["records_rejected"] = rejected
        result["manual_import"] = True
        if persist_preview:
            result.update(self.write_compact_validated_rows(result, base_data_dir=base_data_dir))
        return result


def _render_validated_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# MLB Open Data Validated Source",
            "",
            f"1. source_id: {report.get('source_id')}",
            f"2. gate: {report.get('gate')}",
            f"3. status: {report.get('status')}",
            f"4. records_validated: {report.get('records_validated')}",
            f"5. records_rejected: {report.get('records_rejected')}",
            f"6. fields_available: {', '.join(report.get('fields_available') or []) if report.get('fields_available') else 'none'}",
            f"7. seasons_backfilled: {', '.join(report.get('seasons_backfilled') or []) if report.get('seasons_backfilled') else 'none'}",
            "8. safety: provider_write=false; execution_allowed=false; raw_payload_included=false; raw_html_persisted=false; secrets_included=false",
            "",
        ]
    )


def build_adapters() -> list[MlbOpenDataAdapter]:
    adapters: list[MlbOpenDataAdapter] = []
    for source in mlb_open_data_sources():
        if source.get("source_kind") == "structured_open_data":
            adapters.append(WikidataMlbSeedAdapter(source))
        elif source.get("source_kind") == "manual_csv":
            adapters.append(ManualCsvImportAdapter(source))
        else:
            adapters.append(MlbOpenDataAdapter(source))
    return adapters


def adapter_by_id(source_id: str) -> MlbOpenDataAdapter | None:
    source = source_by_id(source_id)
    if not source:
        return None
    if source.get("source_kind") == "structured_open_data":
        return WikidataMlbSeedAdapter(source)
    if source.get("source_kind") == "manual_csv":
        return ManualCsvImportAdapter(source)
    return MlbOpenDataAdapter(source)


def load_validated_mlb_rows(*, base_data_dir: str | Path | None = None) -> list[dict[str, Any]]:
    root = mlb_root(base_data_dir) / "validated"
    if not root.exists():
        return []
    rows: list[dict[str, Any]] = []
    for latest in root.glob("*/latest.json"):
        payload = mlb_read_json(latest)
        if isinstance(payload, dict):
            for row in payload.get("validated_rows") or payload.get("sample_rows") or []:
                if isinstance(row, dict):
                    rows.append(row)
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--gate", default="metadata_check")
    parser.add_argument("--season", default=str(DEFAULT_ONE_SEASON))
    parser.add_argument("--max-records", type=int, default=DEFAULT_TINY_SAMPLE_RECORDS)
    parser.add_argument("--input-path", default=None)
    parser.add_argument("--allow-download", action="store_true")
    parser.add_argument("--allow-structured-seed", action="store_true")
    parser.add_argument("--allow-manual-import", action="store_true")
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    adapter = adapter_by_id(args.source_id)
    if adapter is None:
        print(json.dumps(mlb_safe_payload({"ok": False, "status": "blocked", "blocked_reason": "unsupported_source"}), indent=2, sort_keys=True))
        return 1
    if args.gate == "metadata_check":
        report = adapter.run_metadata_check()
    elif args.gate == "tiny_sample":
        report = adapter.run_tiny_sample(
            allow_download=args.allow_download,
            max_records=args.max_records,
            input_path=args.input_path,
            allow_structured_seed=args.allow_structured_seed,
            allow_manual_import=args.allow_manual_import,
        )
    elif args.gate == "one_season_import":
        report = adapter.run_one_season_import(
            season=args.season,
            allow_download=args.allow_download,
            input_path=args.input_path,
            allow_structured_seed=args.allow_structured_seed,
            allow_manual_import=args.allow_manual_import,
        )
    elif args.gate == "small_window_import":
        report = adapter.run_small_window_import(
            allow_download=args.allow_download,
            input_path=args.input_path,
            allow_structured_seed=args.allow_structured_seed,
            allow_manual_import=args.allow_manual_import,
        )
    elif args.gate == "full_available_backfill":
        report = adapter.run_full_available_backfill(
            allow_download=args.allow_download,
            input_path=args.input_path,
            allow_structured_seed=args.allow_structured_seed,
            allow_manual_import=args.allow_manual_import,
        )
    elif args.gate == "manual_import" and isinstance(adapter, ManualCsvImportAdapter):
        report = adapter.run_manual_import(
            input_path=args.input_path,
            allow_manual_import=args.allow_manual_import,
            max_records=args.max_records,
        )
    elif args.gate == "structured_seed_import" and isinstance(adapter, WikidataMlbSeedAdapter):
        report = adapter.run_structured_seed_import(
            allow_structured_seed=args.allow_structured_seed,
            max_records=args.max_records,
        )
    else:
        report = adapter._blocked(str(args.gate), "unsupported_source")
    paths: dict[str, str] = {}
    if args.persist and report.get("gate"):
        paths = adapter.write_compact_validated_rows(report)
        report.update(paths)
    print(
        json.dumps(
            {
                "ok": bool(report.get("ok")),
                "status": report.get("status"),
                "source_id": report.get("source_id"),
                "gate": report.get("gate"),
                "blocked_reason": report.get("blocked_reason"),
                "records_validated": int(report.get("records_validated", 0) or 0),
                "records_rejected": int(report.get("records_rejected", 0) or 0),
                "fields_available": report.get("fields_available"),
                "seasons_backfilled": report.get("seasons_backfilled"),
                "downloads_attempted": int(report.get("downloads_attempted", 0) or 0),
                "downloads_succeeded": int(report.get("downloads_succeeded", 0) or 0),
                "provider_calls_attempted": int(report.get("provider_calls_attempted", 0) or 0),
                "enabled_source_count": 0,
                "paid_source_enabled_count": 0,
                "provider_write": False,
                "execution_allowed": False,
                "raw_payload_included": False,
                "raw_html_persisted": False,
                "secrets_included": False,
                "latest_json_path": paths.get("latest_json_path"),
                "latest_markdown_path": paths.get("latest_markdown_path"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

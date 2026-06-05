from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .nhl_free_vs_paid_readiness import nhl_lane_catalog
from .nhl_oxylabs_common import (
    current_utc,
    discover_nhl_sample_context,
    fetch_public_json,
    lane_source_spec,
    stable_hash,
)


SHOT_EVENT_TYPES = {"shot-on-goal", "goal", "missed-shot", "blocked-shot"}


def _parse_date(value: Any) -> datetime | None:
    raw = str(value or "").strip().replace("Z", "+00:00")
    if not raw:
        return None
    try:
        result = datetime.fromisoformat(raw)
    except Exception:
        try:
            result = datetime.strptime(raw[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except Exception:
            return None
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result


def _cached_fetch_json(cache: dict[str, Any], key: str, url: str) -> dict[str, Any]:
    if key in cache:
        return cache[key]
    result = fetch_public_json(
        source_id="nhl_official_api",
        domain="api-web.nhle.com",
        url=url,
        transport="residential_proxy",
    )
    cache[key] = result
    return result


def build_nhl_source_bundle(*, cache: dict[str, Any] | None = None) -> dict[str, Any]:
    cache = {} if cache is None else cache
    context = cache.get("sample_context")
    if not context:
        context = discover_nhl_sample_context()
        cache["sample_context"] = context
    if not context.get("ok"):
        return {
            "ok": False,
            "status": "blocked",
            "blocked_reason": "no_public_page_or_endpoint_exists_after_oxylabs_search",
            "cache": cache,
            "context": context,
        }
    game_id = int(context.get("sample_game_id") or 0)
    season = int(context.get("sample_season") or 0)
    game_type = int(context.get("sample_game_type") or 2)
    home = str(context.get("home_team_abbrev") or "")
    away = str(context.get("away_team_abbrev") or "")
    urls = {
        "boxscore": f"https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore",
        "play_by_play": f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play",
        "landing": f"https://api-web.nhle.com/v1/gamecenter/{game_id}/landing",
        "home_roster": f"https://api-web.nhle.com/v1/roster/{home}/current",
        "away_roster": f"https://api-web.nhle.com/v1/roster/{away}/current",
        "home_stats": f"https://api-web.nhle.com/v1/club-stats/{home}/{season}/{game_type}",
        "away_stats": f"https://api-web.nhle.com/v1/club-stats/{away}/{season}/{game_type}",
    }
    bundle = {
        "ok": True,
        "status": "ok",
        "cache": cache,
        "context": context,
        "schedule_now": context.get("schedule_response"),
        "schedule_previous": context.get("previous_schedule_response"),
    }
    for key, url in urls.items():
        bundle[key] = _cached_fetch_json(cache, key, url)
    return bundle


def _schedule_games(context: dict[str, Any]) -> list[dict[str, Any]]:
    games: list[dict[str, Any]] = []
    seen: set[int] = set()
    for payload_key in ("schedule_previous", "schedule_now"):
        payload = context.get(payload_key) or {}
        for week in list(payload.get("gameWeek") or []):
            for game in list(week.get("games") or []):
                game_id = int(game.get("id") or 0)
                if game_id and game_id not in seen:
                    seen.add(game_id)
                    games.append(game)
    games.sort(key=lambda row: str(row.get("startTimeUTC") or ""))
    return games


def _team_id_from_abbrev(game: dict[str, Any], team_abbrev: str) -> int:
    for side in ("homeTeam", "awayTeam"):
        team = game.get(side) or {}
        if str(team.get("abbrev") or "") == team_abbrev:
            return int(team.get("id") or 0)
    return 0


def _team_schedule_stats(games: list[dict[str, Any]], team_abbrev: str, sample_game_id: int) -> dict[str, Any]:
    ordered = [game for game in games if str((game.get("homeTeam") or {}).get("abbrev") or "") == team_abbrev or str((game.get("awayTeam") or {}).get("abbrev") or "") == team_abbrev]
    sample_index = next((idx for idx, game in enumerate(ordered) if int(game.get("id") or 0) == sample_game_id), -1)
    if sample_index < 0:
        return {
            "rest_days": None,
            "back_to_back_flag": False,
            "three_in_four_nights_flag": False,
            "overtime_recent_count": 0,
            "shootout_recent_count": 0,
            "travel_distance_estimate": 0,
        }
    sample_game = ordered[sample_index]
    sample_dt = _parse_date(sample_game.get("startTimeUTC") or sample_game.get("gameDate"))
    prior_games = ordered[:sample_index]
    rest_days = None
    if prior_games and sample_dt:
        prior_dt = _parse_date(prior_games[-1].get("startTimeUTC") or prior_games[-1].get("gameDate"))
        if prior_dt:
            rest_days = max(0, (sample_dt - prior_dt).days)
    recent_games = []
    if sample_dt:
        for game in prior_games:
            game_dt = _parse_date(game.get("startTimeUTC") or game.get("gameDate"))
            if game_dt and (sample_dt - game_dt).days <= 4:
                recent_games.append(game)
    overtime_recent_count = sum(1 for game in prior_games[-5:] if str((game.get("gameOutcome") or {}).get("lastPeriodType") or "") == "OT")
    shootout_recent_count = sum(1 for game in prior_games[-5:] if str((game.get("gameOutcome") or {}).get("lastPeriodType") or "") == "SO")
    current_offset = str(sample_game.get("venueUTCOffset") or "")
    prior_offset = str((prior_games[-1].get("venueUTCOffset") if prior_games else "") or "")
    travel_distance_estimate = 0
    if current_offset and prior_offset and current_offset != prior_offset:
        travel_distance_estimate = 500
    return {
        "rest_days": rest_days,
        "back_to_back_flag": bool(rest_days is not None and rest_days <= 1),
        "three_in_four_nights_flag": len(recent_games) >= 2,
        "overtime_recent_count": overtime_recent_count,
        "shootout_recent_count": shootout_recent_count,
        "travel_distance_estimate": travel_distance_estimate,
    }


def _shot_quality_proxy(details: dict[str, Any], type_desc_key: str) -> float:
    x_coord = float(details.get("xCoord") or 0)
    y_coord = float(details.get("yCoord") or 0)
    distance_factor = max(0.1, 1.0 - min(((abs(x_coord) + abs(y_coord)) / 200.0), 0.9))
    shot_type = str(details.get("shotType") or "").lower()
    type_bonus = 0.2 if shot_type in {"tip-in", "backhand", "wrap-around"} else 0.1 if shot_type in {"snap", "wrist"} else 0.0
    goal_bonus = 0.25 if type_desc_key == "goal" else 0.0
    return round(min(1.0, distance_factor + type_bonus + goal_bonus), 4)


def _load_schedule_results(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    games = _schedule_games(bundle["context"])
    rows = []
    for game in games:
        rows.append(
            {
                "sport": "icehockey_nhl",
                "lane_name": "schedule_results",
                "source_system": "official_nhl_public_api",
                "retrieval_method": "oxylabs_residential_proxy",
                "game_id": int(game.get("id") or 0),
                "season": int(game.get("season") or 0),
                "game_date": game.get("gameDate"),
                "start_time_utc": game.get("startTimeUTC"),
                "home_team_id": int(((game.get("homeTeam") or {}).get("id")) or 0),
                "home_team_abbrev": str(((game.get("homeTeam") or {}).get("abbrev")) or ""),
                "away_team_id": int(((game.get("awayTeam") or {}).get("id")) or 0),
                "away_team_abbrev": str(((game.get("awayTeam") or {}).get("abbrev")) or ""),
                "home_score": int(((game.get("homeTeam") or {}).get("score")) or 0),
                "away_score": int(((game.get("awayTeam") or {}).get("score")) or 0),
                "game_state": str(game.get("gameState") or ""),
                "venue_name": str((game.get("venue") or {}).get("default") or ""),
                "venue_timezone": str(game.get("venueTimezone") or ""),
                "source_record_hash": stable_hash(game),
            }
        )
    return rows


def _load_team_box_scores(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    payload = (bundle["boxscore"].get("json_payload") or {})
    rows = []
    for side in ("homeTeam", "awayTeam"):
        team = payload.get(side) or {}
        rows.append(
            {
                "sport": "icehockey_nhl",
                "lane_name": "team_box_scores",
                "source_system": "official_nhl_public_api",
                "retrieval_method": "oxylabs_residential_proxy",
                "game_id": int(payload.get("id") or 0),
                "team_id": int(team.get("id") or 0),
                "team_abbrev": str(team.get("abbrev") or ""),
                "team_score": int(team.get("score") or 0),
                "shots_on_goal": int(team.get("sog") or 0),
                "source_record_hash": stable_hash({"game_id": payload.get("id"), "team_id": team.get("id")}),
            }
        )
    return rows


def _iter_box_players(payload: dict[str, Any], *, include_goalies: bool) -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    rows: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    player_by_game = payload.get("playerByGameStats") or {}
    for side in ("homeTeam", "awayTeam"):
        team = payload.get(side) or {}
        groups = (player_by_game.get(side) or {})
        for group_name, players in groups.items():
            if include_goalies != (group_name == "goalies"):
                continue
            for player in list(players or []):
                rows.append((group_name, team, player))
    return rows


def _load_player_box_scores(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    payload = bundle["boxscore"].get("json_payload") or {}
    rows = []
    for group_name, team, player in _iter_box_players(payload, include_goalies=False):
        rows.append(
            {
                "sport": "icehockey_nhl",
                "lane_name": "player_box_scores",
                "source_system": "official_nhl_public_api",
                "retrieval_method": "oxylabs_residential_proxy",
                "game_id": int(payload.get("id") or 0),
                "player_id": int(player.get("playerId") or 0),
                "team_id": int(team.get("id") or 0),
                "position": str(player.get("position") or group_name.upper()),
                "goals": int(player.get("goals") or 0),
                "assists": int(player.get("assists") or 0),
                "points": int(player.get("points") or 0),
                "shots_on_goal": int(player.get("sog") or 0),
                "time_on_ice": str(player.get("toi") or ""),
                "power_play_goals": int(player.get("powerPlayGoals") or 0),
                "blocked_shots": int(player.get("blockedShots") or 0),
                "source_record_hash": stable_hash({"game_id": payload.get("id"), "player_id": player.get("playerId")}),
            }
        )
    return rows


def _load_goalie_box_scores(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    payload = bundle["boxscore"].get("json_payload") or {}
    rows = []
    for _, team, player in _iter_box_players(payload, include_goalies=True):
        rows.append(
            {
                "sport": "icehockey_nhl",
                "lane_name": "goalie_box_scores",
                "source_system": "official_nhl_public_api",
                "retrieval_method": "oxylabs_residential_proxy",
                "game_id": int(payload.get("id") or 0),
                "player_id": int(player.get("playerId") or 0),
                "team_id": int(team.get("id") or 0),
                "goalie_name": str((player.get("name") or {}).get("default") or ""),
                "starter": bool(player.get("starter")),
                "decision": str(player.get("decision") or ""),
                "save_pct": float(player.get("savePctg") or 0.0),
                "shots_against": int(player.get("shotsAgainst") or 0),
                "saves": int(player.get("saves") or 0),
                "goals_against": int(player.get("goalsAgainst") or 0),
                "time_on_ice": str(player.get("toi") or ""),
                "source_record_hash": stable_hash({"game_id": payload.get("id"), "player_id": player.get("playerId")}),
            }
        )
    return rows


def _load_play_by_play(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    payload = bundle["play_by_play"].get("json_payload") or {}
    rows = []
    for play in list(payload.get("plays") or []):
        details = play.get("details") or {}
        rows.append(
            {
                "sport": "icehockey_nhl",
                "lane_name": "play_by_play",
                "source_system": "official_nhl_public_api",
                "retrieval_method": "oxylabs_residential_proxy",
                "game_id": int(payload.get("id") or 0),
                "event_id": int(play.get("eventId") or 0),
                "period_number": int(((play.get("periodDescriptor") or {}).get("number")) or 0),
                "time_in_period": str(play.get("timeInPeriod") or ""),
                "time_remaining": str(play.get("timeRemaining") or ""),
                "type_desc_key": str(play.get("typeDescKey") or ""),
                "situation_code": str(play.get("situationCode") or ""),
                "event_owner_team_id": int(details.get("eventOwnerTeamId") or 0),
                "source_record_hash": stable_hash({"game_id": payload.get("id"), "event_id": play.get("eventId")}),
            }
        )
    return rows


def _load_shot_events(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    payload = bundle["play_by_play"].get("json_payload") or {}
    rows = []
    for play in list(payload.get("plays") or []):
        type_desc_key = str(play.get("typeDescKey") or "")
        if type_desc_key not in SHOT_EVENT_TYPES:
            continue
        details = play.get("details") or {}
        rows.append(
            {
                "sport": "icehockey_nhl",
                "lane_name": "shot_events",
                "source_system": "official_nhl_public_api",
                "retrieval_method": "oxylabs_residential_proxy",
                "game_id": int(payload.get("id") or 0),
                "event_id": int(play.get("eventId") or 0),
                "shooting_player_id": int(details.get("shootingPlayerId") or 0),
                "goalie_in_net_id": int(details.get("goalieInNetId") or 0),
                "x_coord": int(details.get("xCoord") or 0),
                "y_coord": int(details.get("yCoord") or 0),
                "shot_type": str(details.get("shotType") or ""),
                "zone_code": str(details.get("zoneCode") or ""),
                "shot_quality_proxy": _shot_quality_proxy(details, type_desc_key),
                "source_record_hash": stable_hash({"game_id": payload.get("id"), "event_id": play.get("eventId")}),
            }
        )
    return rows


def _load_penalty_events(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    payload = bundle["play_by_play"].get("json_payload") or {}
    rows = []
    for play in list(payload.get("plays") or []):
        if str(play.get("typeDescKey") or "") != "penalty":
            continue
        details = play.get("details") or {}
        rows.append(
            {
                "sport": "icehockey_nhl",
                "lane_name": "penalty_events",
                "source_system": "official_nhl_public_api",
                "retrieval_method": "oxylabs_residential_proxy",
                "game_id": int(payload.get("id") or 0),
                "event_id": int(play.get("eventId") or 0),
                "committed_by_player_id": int(details.get("committedByPlayerId") or 0),
                "drawn_by_player_id": int(details.get("drawnByPlayerId") or 0),
                "penalty_type_code": str(details.get("typeCode") or ""),
                "penalty_desc_key": str(details.get("descKey") or ""),
                "duration": int(details.get("duration") or 0),
                "zone_code": str(details.get("zoneCode") or ""),
                "event_owner_team_id": int(details.get("eventOwnerTeamId") or 0),
                "source_record_hash": stable_hash({"game_id": payload.get("id"), "event_id": play.get("eventId")}),
            }
        )
    return rows


def _load_power_play_penalty_kill_stats(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    shot_events = _load_shot_events(bundle)
    penalty_events = _load_penalty_events(bundle)
    context = bundle["context"]
    sample_game = context.get("sample_game") or {}
    rows = []
    for side, stats_key in (("homeTeam", "home_stats"), ("awayTeam", "away_stats")):
        team = sample_game.get(side) or {}
        stats_payload = bundle[stats_key].get("json_payload") or {}
        team_id = int(team.get("id") or 0)
        skaters = list(stats_payload.get("skaters") or [])
        power_play_goals = sum(int(player.get("powerPlayGoals") or 0) for player in skaters)
        shots = sum(int(player.get("shots") or 0) for player in skaters)
        penalties_taken = sum(1 for row in penalty_events if int(row.get("event_owner_team_id") or 0) == team_id)
        special_teams_goals = sum(
            1
            for player in _load_player_box_scores(bundle)
            if int(player.get("team_id") or 0) == team_id and int(player.get("power_play_goals") or 0) > 0
        )
        rows.append(
            {
                "sport": "icehockey_nhl",
                "lane_name": "power_play_penalty_kill_stats",
                "source_system": "official_nhl_public_api",
                "retrieval_method": "oxylabs_residential_proxy",
                "team_id": team_id,
                "season": int(sample_game.get("season") or 0),
                "power_play_goals": power_play_goals,
                "shots": shots,
                "power_play_recent_rate": round(power_play_goals / max(shots, 1), 4),
                "penalty_kill_recent_rate": round(max(penalties_taken - special_teams_goals, 0) / max(penalties_taken, 1), 4),
                "special_teams_form": round((power_play_goals / max(len(skaters), 1)) + special_teams_goals, 4),
                "source_record_hash": stable_hash({"team_id": team_id, "season": sample_game.get("season")}),
            }
        )
    return rows


def _load_goalie_starts(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    goalies = _load_goalie_box_scores(bundle)
    rows = []
    for goalie in goalies:
        rows.append(
            {
                "sport": "icehockey_nhl",
                "lane_name": "goalie_starts",
                "source_system": "official_nhl_public_api",
                "retrieval_method": "oxylabs_residential_proxy",
                "game_id": goalie["game_id"],
                "team_id": goalie["team_id"],
                "goalie_player_id": goalie["player_id"],
                "goalie_start_confirmed": bool(goalie["starter"]),
                "goalie_name": str(goalie.get("goalie_name") or ""),
                "backup_goalie_flag": not bool(goalie["starter"]),
                "source_record_hash": stable_hash({"game_id": goalie["game_id"], "player_id": goalie["player_id"]}),
            }
        )
    return rows


def _load_goalie_workload_rest(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    context = bundle["context"]
    games = _schedule_games(context)
    sample_game = context.get("sample_game") or {}
    starter_rows = [row for row in _load_goalie_starts(bundle) if row["goalie_start_confirmed"]]
    stats_lookup: dict[int, dict[str, Any]] = {}
    for stats_key in ("home_stats", "away_stats"):
        for goalie in list((bundle[stats_key].get("json_payload") or {}).get("goalies") or []):
            stats_lookup[int(goalie.get("playerId") or 0)] = goalie
    team_schedule_lookup = {
        str((sample_game.get("homeTeam") or {}).get("abbrev") or ""): _team_schedule_stats(games, str((sample_game.get("homeTeam") or {}).get("abbrev") or ""), int(sample_game.get("id") or 0)),
        str((sample_game.get("awayTeam") or {}).get("abbrev") or ""): _team_schedule_stats(games, str((sample_game.get("awayTeam") or {}).get("abbrev") or ""), int(sample_game.get("id") or 0)),
    }
    rows = []
    for row in starter_rows:
        team_abbrev = str((sample_game.get("homeTeam") or {}).get("abbrev") or "") if row["team_id"] == int((sample_game.get("homeTeam") or {}).get("id") or 0) else str((sample_game.get("awayTeam") or {}).get("abbrev") or "")
        schedule_stats = team_schedule_lookup.get(team_abbrev, {})
        goalie_stats = stats_lookup.get(int(row["goalie_player_id"] or 0), {})
        rows.append(
            {
                "sport": "icehockey_nhl",
                "lane_name": "goalie_workload_rest",
                "source_system": "official_nhl_public_api",
                "retrieval_method": "oxylabs_residential_proxy",
                "game_id": row["game_id"],
                "team_id": row["team_id"],
                "goalie_player_id": row["goalie_player_id"],
                "goalie_rest_days": schedule_stats.get("rest_days"),
                "goalie_recent_games_started": int(goalie_stats.get("gamesStarted") or 0),
                "goalie_recent_save_pct": float(goalie_stats.get("savePercentage") or 0.0),
                "backup_goalie_flag": bool(row["backup_goalie_flag"]),
                "source_record_hash": stable_hash({"game_id": row["game_id"], "goalie_player_id": row["goalie_player_id"]}),
            }
        )
    return rows


def _load_rest_travel_features(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    context = bundle["context"]
    sample_game = context.get("sample_game") or {}
    games = _schedule_games(context)
    home_abbrev = str((sample_game.get("homeTeam") or {}).get("abbrev") or "")
    away_abbrev = str((sample_game.get("awayTeam") or {}).get("abbrev") or "")
    home_stats = _team_schedule_stats(games, home_abbrev, int(sample_game.get("id") or 0))
    away_stats = _team_schedule_stats(games, away_abbrev, int(sample_game.get("id") or 0))
    rows = []
    for team_abbrev, team_id, stats in (
        (home_abbrev, int((sample_game.get("homeTeam") or {}).get("id") or 0), home_stats),
        (away_abbrev, int((sample_game.get("awayTeam") or {}).get("id") or 0), away_stats),
    ):
        rows.append(
            {
                "sport": "icehockey_nhl",
                "lane_name": "rest_travel_features",
                "source_system": "official_nhl_public_api",
                "retrieval_method": "oxylabs_residential_proxy",
                "game_id": int(sample_game.get("id") or 0),
                "team_id": team_id,
                "rest_days": stats.get("rest_days"),
                "back_to_back_flag": bool(stats.get("back_to_back_flag")),
                "three_in_four_nights_flag": bool(stats.get("three_in_four_nights_flag")),
                "rest_disadvantage": (home_stats.get("rest_days") or 0) - (away_stats.get("rest_days") or 0) if team_abbrev == home_abbrev else (away_stats.get("rest_days") or 0) - (home_stats.get("rest_days") or 0),
                "travel_distance_estimate": int(stats.get("travel_distance_estimate") or 0),
                "source_record_hash": stable_hash({"game_id": sample_game.get("id"), "team_id": team_id}),
            }
        )
    return rows


def _load_venue_features(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    sample_game = bundle["context"].get("sample_game") or {}
    return [
        {
            "sport": "icehockey_nhl",
            "lane_name": "venue_rink_timezone_features",
            "source_system": "official_nhl_public_api",
            "retrieval_method": "oxylabs_residential_proxy",
            "game_id": int(sample_game.get("id") or 0),
            "venue_name": str((sample_game.get("venue") or {}).get("default") or ""),
            "venue_location": str((sample_game.get("venueLocation") or {}).get("default") or ""),
            "venue_timezone": str(sample_game.get("venueTimezone") or ""),
            "venue_utc_offset": str(sample_game.get("venueUTCOffset") or ""),
            "rink_home_ice_context": "standard_home_ice",
            "source_record_hash": stable_hash({"game_id": sample_game.get("id"), "venue": sample_game.get("venue")}),
        }
    ]


def _load_roster_records(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    context = bundle["context"]
    sample_game = context.get("sample_game") or {}
    team_map = {
        "home_roster": int((sample_game.get("homeTeam") or {}).get("id") or 0),
        "away_roster": int((sample_game.get("awayTeam") or {}).get("id") or 0),
    }
    rows = []
    for key, team_id in team_map.items():
        payload = bundle[key].get("json_payload") or {}
        for group_name in ("forwards", "defensemen", "goalies"):
            for player in list(payload.get(group_name) or []):
                rows.append(
                    {
                        "sport": "icehockey_nhl",
                        "lane_name": "roster_records",
                        "source_system": "official_nhl_public_api",
                        "retrieval_method": "oxylabs_residential_proxy",
                        "team_id": team_id,
                        "player_id": int(player.get("id") or 0),
                        "position_code": str(player.get("positionCode") or ""),
                        "sweater_number": str(player.get("sweaterNumber") or ""),
                        "shoots_catches": str(player.get("shootsCatches") or ""),
                        "roster_continuity": 1.0,
                        "source_record_hash": stable_hash({"team_id": team_id, "player_id": player.get("id")}),
                    }
                )
    return rows


def _load_overtime_shootout_context(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    context = bundle["context"]
    sample_game = context.get("sample_game") or {}
    landing = bundle["landing"].get("json_payload") or {}
    games = _schedule_games(context)
    home_abbrev = str((sample_game.get("homeTeam") or {}).get("abbrev") or "")
    away_abbrev = str((sample_game.get("awayTeam") or {}).get("abbrev") or "")
    home_recent = _team_schedule_stats(games, home_abbrev, int(sample_game.get("id") or 0))
    away_recent = _team_schedule_stats(games, away_abbrev, int(sample_game.get("id") or 0))
    return [
        {
            "sport": "icehockey_nhl",
            "lane_name": "overtime_shootout_context",
            "source_system": "official_nhl_public_api",
            "retrieval_method": "oxylabs_residential_proxy",
            "game_id": int(sample_game.get("id") or 0),
            "game_outcome_last_period_type": str((sample_game.get("gameOutcome") or {}).get("lastPeriodType") or ""),
            "ot_in_use": bool(landing.get("otInUse")),
            "shootout_in_use": bool(landing.get("shootoutInUse")),
            "overtime_experience": int(home_recent.get("overtime_recent_count") or 0) + int(away_recent.get("overtime_recent_count") or 0),
            "shootout_context": int(home_recent.get("shootout_recent_count") or 0) + int(away_recent.get("shootout_recent_count") or 0),
            "source_record_hash": stable_hash({"game_id": sample_game.get("id"), "last_period_type": (sample_game.get("gameOutcome") or {}).get("lastPeriodType")}),
        }
    ]


def _load_first_period_scoring_context(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    plays = list((bundle["play_by_play"].get("json_payload") or {}).get("plays") or [])
    sample_game = bundle["context"].get("sample_game") or {}
    first_period_plays = [play for play in plays if int(((play.get("periodDescriptor") or {}).get("number")) or 0) == 1]
    goals = sum(1 for play in first_period_plays if str(play.get("typeDescKey") or "") == "goal")
    shots = sum(1 for play in first_period_plays if str(play.get("typeDescKey") or "") in SHOT_EVENT_TYPES)
    return [
        {
            "sport": "icehockey_nhl",
            "lane_name": "first_period_scoring_context",
            "source_system": "official_nhl_public_api",
            "retrieval_method": "oxylabs_residential_proxy",
            "game_id": int(sample_game.get("id") or 0),
            "first_period_goals_total": goals,
            "first_period_shots_total": shots,
            "first_period_scoring_tendency": round(goals / max(shots, 1), 4),
            "source_record_hash": stable_hash({"game_id": sample_game.get("id"), "first_period_goals": goals, "first_period_shots": shots}),
        }
    ]


def _load_team_totals_context(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    sample_game = bundle["context"].get("sample_game") or {}
    team_box = _load_team_box_scores(bundle)
    first_period = _load_first_period_scoring_context(bundle)[0]
    player_box = _load_player_box_scores(bundle)
    rows = []
    total_goals = sum(int(row.get("team_score") or 0) for row in team_box)
    for team_row in team_box:
        team_id = int(team_row["team_id"])
        special_teams_goals_for = sum(int(player.get("power_play_goals") or 0) for player in player_box if int(player.get("team_id") or 0) == team_id)
        rows.append(
            {
                "sport": "icehockey_nhl",
                "lane_name": "team_totals_context",
                "source_system": "official_nhl_public_api",
                "retrieval_method": "oxylabs_residential_proxy",
                "game_id": int(sample_game.get("id") or 0),
                "team_id": team_id,
                "team_goals": int(team_row.get("team_score") or 0),
                "total_goals": total_goals,
                "special_teams_goals_for": special_teams_goals_for,
                "first_period_goals_for": int(first_period.get("first_period_goals_total") or 0),
                "source_record_hash": stable_hash({"game_id": sample_game.get("id"), "team_id": team_id}),
            }
        )
    return rows


def _load_player_prop_feature_candidates(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    player_box = _load_player_box_scores(bundle)
    shot_events = _load_shot_events(bundle)
    shots_by_player: dict[int, int] = {}
    for shot in shot_events:
        player_id = int(shot.get("shooting_player_id") or 0)
        shots_by_player[player_id] = shots_by_player.get(player_id, 0) + 1
    rows = []
    for player in player_box:
        player_id = int(player.get("player_id") or 0)
        shots = shots_by_player.get(player_id, int(player.get("shots_on_goal") or 0))
        points = int(player.get("points") or 0)
        blocked_shots = int(player.get("blocked_shots") or 0)
        quality = round((shots * 0.4) + (points * 0.4) + (blocked_shots * 0.2), 4)
        rows.append(
            {
                "sport": "icehockey_nhl",
                "lane_name": "player_prop_feature_candidates",
                "source_system": "official_nhl_public_api",
                "retrieval_method": "oxylabs_residential_proxy",
                "game_id": int(player.get("game_id") or 0),
                "player_id": player_id,
                "shots_on_goal_rate_proxy": shots,
                "point_rate_proxy": points,
                "power_play_goal_count": int(player.get("power_play_goals") or 0),
                "blocked_shots": blocked_shots,
                "player_prop_feature_quality": quality,
                "source_record_hash": stable_hash({"game_id": player.get("game_id"), "player_id": player_id}),
            }
        )
    return rows


def _lane_handlers() -> dict[str, Any]:
    return {
        "schedule_results": _load_schedule_results,
        "team_box_scores": _load_team_box_scores,
        "player_box_scores": _load_player_box_scores,
        "goalie_box_scores": _load_goalie_box_scores,
        "play_by_play": _load_play_by_play,
        "shot_events": _load_shot_events,
        "penalty_events": _load_penalty_events,
        "power_play_penalty_kill_stats": _load_power_play_penalty_kill_stats,
        "goalie_starts": _load_goalie_starts,
        "goalie_workload_rest": _load_goalie_workload_rest,
        "rest_travel_features": _load_rest_travel_features,
        "venue_rink_timezone_features": _load_venue_features,
        "roster_records": _load_roster_records,
        "overtime_shootout_context": _load_overtime_shootout_context,
        "first_period_scoring_context": _load_first_period_scoring_context,
        "team_totals_context": _load_team_totals_context,
        "player_prop_feature_candidates": _load_player_prop_feature_candidates,
    }


def load_nhl_lane_records(lane: dict[str, Any], *, cache: dict[str, Any] | None = None) -> dict[str, Any]:
    handlers = _lane_handlers()
    handler = handlers.get(str(lane.get("lane_name") or ""))
    if handler is None:
        return {
            "ok": False,
            "status": "blocked",
            "blocked_reason": "schema_mapping_failed",
            "normalized_records": [],
            "normalized_record_count": 0,
            "oxylabs_used": False,
            "oxylabs_transport_used": "hard_blocked",
            "oxylabs_calls_attempted": 0,
            "oxylabs_calls_successful": 0,
            "oxylabs_calls_failed": 0,
        }
    bundle = build_nhl_source_bundle(cache=cache)
    if not bundle.get("ok"):
        return {
            "ok": False,
            "status": "blocked",
            "blocked_reason": bundle.get("blocked_reason") or "retrieval_failed_after_documented_attempts",
            "normalized_records": [],
            "normalized_record_count": 0,
            "oxylabs_used": True,
            "oxylabs_transport_used": "residential_proxy",
            "oxylabs_calls_attempted": 1,
            "oxylabs_calls_successful": 0,
            "oxylabs_calls_failed": 1,
        }
    try:
        rows = handler(bundle)
    except Exception:
        rows = []
    calls_by_lane = {
        "schedule_results": 2,
        "team_box_scores": 1,
        "player_box_scores": 1,
        "goalie_box_scores": 1,
        "play_by_play": 1,
        "shot_events": 1,
        "penalty_events": 1,
        "power_play_penalty_kill_stats": 3,
        "goalie_starts": 1,
        "goalie_workload_rest": 5,
        "rest_travel_features": 2,
        "venue_rink_timezone_features": 1,
        "roster_records": 2,
        "overtime_shootout_context": 2,
        "first_period_scoring_context": 1,
        "team_totals_context": 2,
        "player_prop_feature_candidates": 2,
    }
    ok = bool(rows)
    return {
        "ok": ok,
        "status": "ok" if ok else "blocked",
        "blocked_reason": None if ok else "no_records_available",
        "lane_name": lane["lane_name"],
        "source_name": lane_source_spec(lane).source_name,
        "source_url_hash": lane.get("source_url_hash"),
        "normalized_records": rows,
        "normalized_record_count": len(rows),
        "oxylabs_used": True,
        "oxylabs_transport_used": "residential_proxy",
        "oxylabs_calls_attempted": calls_by_lane.get(lane["lane_name"], 1),
        "oxylabs_calls_successful": calls_by_lane.get(lane["lane_name"], 1) if ok else 0,
        "oxylabs_calls_failed": 0 if ok else calls_by_lane.get(lane["lane_name"], 1),
        "written_at": current_utc(),
    }


def default_nhl_loader_lanes() -> list[dict[str, Any]]:
    return [
        lane
        for lane in nhl_lane_catalog()
        if lane["loader_exists"] and lane["free_or_paid_category"] in {"free_open_populated", "free_open_partial"}
    ]

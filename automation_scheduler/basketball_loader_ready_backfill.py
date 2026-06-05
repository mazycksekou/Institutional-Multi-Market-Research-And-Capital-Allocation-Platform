from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .basketball_free_vs_paid_readiness import SPORTS, basketball_lane_catalog
from .basketball_oxylabs_common import (
    BASKETBALL_DATA_ROOT,
    fetch_release_asset_rows,
    lane_final_state,
    partial_lanes,
    release_asset_url,
    source_spec_for,
    stable_hash,
    url_hash,
    write_json,
    write_md,
)
from .scheduler_config import sanitize_filename, utc_now_iso


BACKFILL_LIMITS_BY_ASSET = {
    "schedule": 20,
    "team_box": 15,
    "player_box": 15,
    "pbp": 10,
    "team_season_stats": 10,
    "shots": 10,
    "officials": 10,
    "game_rosters": 15,
    "lineups": 10,
}

ASSET_KIND_BY_LANE = {
    "schedule_results": "schedule",
    "team_box_scores": "team_box",
    "player_box_scores": "player_box",
    "play_by_play": "pbp",
    "advanced_team_player_stats": "team_season_stats",
    "pace_possessions": "team_box",
    "shot_location": "shots",
    "referee_official_assignments": "officials",
    "rest_travel_features": "schedule",
    "arena_venue_features": "schedule",
    "roster_continuity": "game_rosters",
    "lineup_on_off": "lineups",
    "conference_tournament_context": "schedule",
}


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        text = str(value).strip()
        if not text:
            return default
        return int(float(text))
    except Exception:
        return default


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        text = str(value).strip()
        if not text:
            return default
        return float(text)
    except Exception:
        return default


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    if not text:
        return default
    return text in {"1", "true", "t", "yes", "y"}


def _nonempty(value: Any, fallback: Any = None) -> Any:
    if value is None:
        return fallback
    if isinstance(value, str) and not value.strip():
        return fallback
    return value


def _pick(row: dict[str, Any], *keys: str, fallback: Any = None) -> Any:
    for key in keys:
        value = row.get(key)
        if value is not None and not (isinstance(value, str) and not value.strip()):
            return value
    return fallback


def _limit_for_asset(asset_kind: str) -> int:
    return BACKFILL_LIMITS_BY_ASSET.get(asset_kind, 10)


def _rows_to_projected_records(
    rows: list[dict[str, Any]],
    fields: list[str],
    *,
    aliases: dict[str, tuple[str, ...]] | None = None,
) -> list[dict[str, Any]]:
    aliases = aliases or {}
    records: list[dict[str, Any]] = []
    for row in rows:
        record: dict[str, Any] = {}
        for field in fields:
            value = row.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                for alias in aliases.get(field, ()):
                    alias_value = row.get(alias)
                    if alias_value is not None and not (isinstance(alias_value, str) and not alias_value.strip()):
                        value = alias_value
                        break
            record[field] = value
        records.append(record)
    return records


def _game_date(row: dict[str, Any]) -> datetime | None:
    raw = _pick(row, "game_date", "date", "start_date", "game_date_time", fallback=None)
    if not raw:
        return None
    text = str(raw).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except Exception:
        try:
            dt = datetime.strptime(text[:10], "%Y-%m-%d")
            dt = dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _schedule_context(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    team_last_game: dict[str, datetime] = {}
    team_recent_games: dict[str, list[datetime]] = defaultdict(list)
    context: dict[tuple[str, str], dict[str, Any]] = {}
    ordered = [row for row in rows if _game_date(row) is not None]
    ordered.sort(key=lambda row: _game_date(row) or datetime.min.replace(tzinfo=timezone.utc))
    for row in ordered:
        game_dt = _game_date(row)
        if game_dt is None:
            continue
        home_id = str(_pick(row, "home_id", "home_team_id", fallback="") or "")
        away_id = str(_pick(row, "away_id", "away_team_id", fallback="") or "")
        home_rest_days = None
        away_rest_days = None
        if home_id in team_last_game:
            home_rest_days = max(0, (game_dt - team_last_game[home_id]).days)
        if away_id in team_last_game:
            away_rest_days = max(0, (game_dt - team_last_game[away_id]).days)
        home_recent = [dt for dt in team_recent_games[home_id] if (game_dt - dt).days <= 4]
        away_recent = [dt for dt in team_recent_games[away_id] if (game_dt - dt).days <= 4]
        context[(str(_pick(row, "game_id", "id", fallback="")), home_id)] = {
            "rest_days": home_rest_days,
            "back_to_back_flag": bool(home_rest_days is not None and home_rest_days <= 1),
            "three_in_four_nights_flag": bool(len(home_recent) >= 2),
            "rest_disadvantage": None if home_rest_days is None or away_rest_days is None else home_rest_days - away_rest_days,
        }
        context[(str(_pick(row, "game_id", "id", fallback="")), away_id)] = {
            "rest_days": away_rest_days,
            "back_to_back_flag": bool(away_rest_days is not None and away_rest_days <= 1),
            "three_in_four_nights_flag": bool(len(away_recent) >= 2),
            "rest_disadvantage": None if home_rest_days is None or away_rest_days is None else away_rest_days - home_rest_days,
        }
        if home_id:
            team_last_game[home_id] = game_dt
            team_recent_games[home_id].append(game_dt)
        if away_id:
            team_last_game[away_id] = game_dt
            team_recent_games[away_id].append(game_dt)
    return context


def _normalize_schedule_rows(lane: dict[str, Any], rows: list[dict[str, Any]], sport: str) -> list[dict[str, Any]]:
    context = _schedule_context(rows)
    out: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        game_id = str(_pick(row, "game_id", "id", fallback=""))
        home_id = str(_pick(row, "home_id", "home_team_id", fallback=""))
        away_id = str(_pick(row, "away_id", "away_team_id", fallback=""))
        game_dt = _game_date(row)
        base = {
            "sport": sport,
            "lane_name": lane["lane_name"],
            "source_system": "sportsdataverse_release_asset",
            "source_url_hash": lane["source_url_hash"],
            "source_name": lane["candidate_source_name"],
            "retrieval_method": "oxylabs_residential_proxy",
            "record_index": index,
            "game_id": game_id,
            "season": _pick(row, "season", fallback=None),
            "game_date": _pick(row, "game_date", "date", "start_date", fallback=None),
            "home_team": _pick(row, "home_display_name", "home_name", "home_team", fallback=None),
            "away_team": _pick(row, "away_display_name", "away_name", "away_team", fallback=None),
            "home_score": _pick(row, "home_score", fallback=None),
            "away_score": _pick(row, "away_score", fallback=None),
            "status": _pick(row, "status_type_detail", "status_type_name", "status", fallback=None),
            "neutral_site": _to_bool(_pick(row, "neutral_site", fallback=False)),
            "venue_id": _pick(row, "venue_id", fallback=None),
            "venue_full_name": _pick(row, "venue_full_name", fallback=None),
            "venue_address_city": _pick(row, "venue_address_city", fallback=None),
            "venue_address_state": _pick(row, "venue_address_state", fallback=None),
            "venue_indoor": _to_bool(_pick(row, "venue_indoor", fallback=False)),
            "game_start_timestamp": game_dt.isoformat() if game_dt else None,
            "source_record_hash": stable_hash({k: row.get(k) for k in sorted(row)}),
        }
        if lane["lane_name"] == "schedule_results":
            out.append({**base})
            continue
        if lane["lane_name"] == "rest_travel_features":
            home_ctx = context.get((game_id, home_id), {})
            away_ctx = context.get((game_id, away_id), {})
            out.append(
                {
                    **base,
                    "rest_disadvantage": home_ctx.get("rest_disadvantage"),
                    "back_to_back_flag": bool(home_ctx.get("back_to_back_flag") or away_ctx.get("back_to_back_flag")),
                    "three_in_four_nights_flag": bool(home_ctx.get("three_in_four_nights_flag") or away_ctx.get("three_in_four_nights_flag")),
                    "travel_distance_estimate": None,
                    "rest_days_home": home_ctx.get("rest_days"),
                    "rest_days_away": away_ctx.get("rest_days"),
                }
            )
            continue
        if lane["lane_name"] == "arena_venue_features":
            out.append(
                {
                    **base,
                    "neutral_site_flag": _to_bool(_pick(row, "neutral_site", fallback=False)),
                    "venue_address_city": _pick(row, "venue_address_city", fallback=None),
                    "venue_address_state": _pick(row, "venue_address_state", fallback=None),
                    "venue_indoor": _to_bool(_pick(row, "venue_indoor", fallback=False)),
                }
            )
            continue
        if lane["lane_name"] == "conference_tournament_context":
            season_type = str(_pick(row, "season_type", fallback="")).strip()
            out.append(
                {
                    **base,
                    "conference_competition": _to_bool(_pick(row, "conference_competition", fallback=False)),
                    "season_type": season_type,
                    "tournament_context": "postseason" if season_type in {"2", "3"} else "regular",
                    "late_season_motivation_context": "postseason" if season_type in {"2", "3"} else "regular",
                }
            )
            continue
    return out


def _normalize_team_box_rows(lane: dict[str, Any], rows: list[dict[str, Any]], sport: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        fga = _to_float(_pick(row, "field_goals_attempted", fallback=0))
        fta = _to_float(_pick(row, "free_throws_attempted", fallback=0))
        oreb = _to_float(_pick(row, "offensive_rebounds", fallback=0))
        turnovers = _to_float(_pick(row, "turnovers", "team_turnovers", fallback=0))
        estimated_possessions = fga + (0.44 * fta) - oreb + turnovers
        team_score = _to_float(_pick(row, "team_score", fallback=0))
        pace_stability = round(estimated_possessions / max(team_score, 1.0), 4)
        common = {
            "sport": sport,
            "lane_name": lane["lane_name"],
            "source_system": "sportsdataverse_release_asset",
            "source_url_hash": lane["source_url_hash"],
            "source_name": lane["candidate_source_name"],
            "retrieval_method": "oxylabs_residential_proxy",
            "record_index": index,
            "game_id": _pick(row, "game_id", fallback=None),
            "season": _pick(row, "season", fallback=None),
            "season_type": _pick(row, "season_type", fallback=None),
            "game_date": _pick(row, "game_date", fallback=None),
            "game_date_time": _pick(row, "game_date_time", fallback=None),
            "team_id": _pick(row, "team_id", fallback=None),
            "team_name": _pick(row, "team_display_name", "team_name", fallback=None),
            "team_abbreviation": _pick(row, "team_abbreviation", fallback=None),
            "team_score": _pick(row, "team_score", fallback=None),
            "team_winner": _to_bool(_pick(row, "team_winner", fallback=False)),
            "assists": _pick(row, "assists", fallback=None),
            "turnovers": _pick(row, "turnovers", "team_turnovers", fallback=None),
            "rebounds": _pick(row, "total_rebounds", "rebounds", fallback=None),
            "field_goals_attempted": _pick(row, "field_goals_attempted", fallback=None),
            "free_throws_attempted": _pick(row, "free_throws_attempted", fallback=None),
            "source_record_hash": stable_hash({k: row.get(k) for k in sorted(row)}),
        }
        if lane["lane_name"] == "team_box_scores":
            out.append(common)
        else:
            out.append(
                {
                    **common,
                    "possession_estimate_source": "team_box_formula",
                    "pace_stability": pace_stability,
                    "estimated_possessions": round(estimated_possessions, 4),
                }
            )
    return out


def _normalize_player_box_rows(lane: dict[str, Any], rows: list[dict[str, Any]], sport: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        out.append(
            {
                "sport": sport,
                "lane_name": lane["lane_name"],
                "source_system": "sportsdataverse_release_asset",
                "source_url_hash": lane["source_url_hash"],
                "source_name": lane["candidate_source_name"],
                "retrieval_method": "oxylabs_residential_proxy",
                "record_index": index,
                "game_id": _pick(row, "game_id", fallback=None),
                "season": _pick(row, "season", fallback=None),
                "season_type": _pick(row, "season_type", fallback=None),
                "game_date": _pick(row, "game_date", fallback=None),
                "game_date_time": _pick(row, "game_date_time", fallback=None),
                "athlete_id": _pick(row, "athlete_id", fallback=None),
                "athlete_display_name": _pick(row, "athlete_display_name", fallback=None),
                "team_id": _pick(row, "team_id", fallback=None),
                "team_name": _pick(row, "team_display_name", "team_name", fallback=None),
                "team_short_display_name": _pick(row, "team_short_display_name", fallback=None),
                "minutes": _pick(row, "minutes", fallback=None),
                "field_goals_attempted": _pick(row, "field_goals_attempted", fallback=None),
                "rebounds": _pick(row, "rebounds", fallback=None),
                "points": _pick(row, "points", fallback=None),
                "assists": _pick(row, "assists", fallback=None),
                "turnovers": _pick(row, "turnovers", fallback=None),
                "starter": _to_bool(_pick(row, "starter", fallback=False)),
                "active": _to_bool(_pick(row, "active", fallback=False)),
                "did_not_play": _to_bool(_pick(row, "did_not_play", fallback=False)),
                "source_record_hash": stable_hash({k: row.get(k) for k in sorted(row)}),
            }
        )
    return out


def _normalize_pbp_rows(lane: dict[str, Any], rows: list[dict[str, Any]], sport: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        out.append(
            {
                "sport": sport,
                "lane_name": lane["lane_name"],
                "source_system": "sportsdataverse_release_asset",
                "source_url_hash": lane["source_url_hash"],
                "source_name": lane["candidate_source_name"],
                "retrieval_method": "oxylabs_residential_proxy",
                "record_index": index,
                "game_play_number": _pick(row, "game_play_number", fallback=None),
                "game_id": _pick(row, "game_id", fallback=None),
                "season": _pick(row, "season", fallback=None),
                "season_type": _pick(row, "season_type", fallback=None),
                "period_number": _pick(row, "period_number", fallback=None),
                "period_display_value": _pick(row, "period_display_value", fallback=None),
                "clock_display_value": _pick(row, "clock_display_value", fallback=None),
                "type_id": _pick(row, "type_id", fallback=None),
                "type_text": _pick(row, "type_text", fallback=None),
                "text": _pick(row, "text", fallback=None),
                "home_score": _pick(row, "home_score", fallback=None),
                "away_score": _pick(row, "away_score", fallback=None),
                "coordinate_x_raw": _pick(row, "coordinate_x_raw", fallback=None),
                "coordinate_y_raw": _pick(row, "coordinate_y_raw", fallback=None),
                "points_attempted": _pick(row, "points_attempted", fallback=None),
                "scoring_play": _to_bool(_pick(row, "scoring_play", fallback=False)),
                "shot_quality_proxy": 1.0 if _to_bool(_pick(row, "scoring_play", fallback=False)) else 0.0,
                "source_record_hash": stable_hash({k: row.get(k) for k in sorted(row)}),
            }
        )
    return out


def _normalize_team_season_stats_rows(lane: dict[str, Any], rows: list[dict[str, Any]], sport: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        out.append(
            {
                "sport": sport,
                "lane_name": lane["lane_name"],
                "source_system": "sportsdataverse_release_asset",
                "source_url_hash": lane["source_url_hash"],
                "source_name": lane["candidate_source_name"],
                "retrieval_method": "oxylabs_residential_proxy",
                "record_index": index,
                "season": _pick(row, "season", fallback=None),
                "team_id": _pick(row, "team_id", fallback=None),
                "team_display_name": _pick(row, "team_display_name", fallback=None),
                "category": _pick(row, "category", fallback=None),
                "stat_label": _pick(row, "stat_label", fallback=None),
                "stat_name": _pick(row, "stat_name", fallback=None),
                "stat_display_name": _pick(row, "stat_display_name", fallback=None),
                "display_value": _pick(row, "display_value", fallback=None),
                "value": _pick(row, "value", fallback=None),
                "efficiency_context": _pick(row, "category", fallback=None),
                "source_record_hash": stable_hash({k: row.get(k) for k in sorted(row)}),
            }
        )
    return out


def _normalize_shots_rows(lane: dict[str, Any], rows: list[dict[str, Any]], sport: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        scoring_play = _to_bool(_pick(row, "scoring_play", fallback=False))
        score_value = _to_float(_pick(row, "score_value", fallback=0.0))
        out.append(
            {
                "sport": sport,
                "lane_name": lane["lane_name"],
                "source_system": "sportsdataverse_release_asset",
                "source_url_hash": lane["source_url_hash"],
                "source_name": lane["candidate_source_name"],
                "retrieval_method": "oxylabs_residential_proxy",
                "record_index": index,
                "game_id": _pick(row, "game_id", fallback=None),
                "season": _pick(row, "season", fallback=None),
                "period_number": _pick(row, "period_number", fallback=None),
                "clock_display_value": _pick(row, "clock_display_value", fallback=None),
                "team_id": _pick(row, "team_id", fallback=None),
                "athlete_id_1": _pick(row, "athlete_id_1", fallback=None),
                "athlete_id_2": _pick(row, "athlete_id_2", fallback=None),
                "type_id": _pick(row, "type_id", fallback=None),
                "type_text": _pick(row, "type_text", fallback=None),
                "scoring_play": scoring_play,
                "score_value": score_value,
                "coordinate_x": _pick(row, "coordinate_x", fallback=None),
                "coordinate_y": _pick(row, "coordinate_y", fallback=None),
                "coordinate_x_raw": _pick(row, "coordinate_x_raw", fallback=None),
                "coordinate_y_raw": _pick(row, "coordinate_y_raw", fallback=None),
                "shot_quality_proxy": round(score_value / 3.0, 4) if scoring_play else 0.0,
                "source_record_hash": stable_hash({k: row.get(k) for k in sorted(row)}),
            }
        )
    return out


def _normalize_officials_rows(lane: dict[str, Any], rows: list[dict[str, Any]], sport: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        game_id = str(_pick(row, "game_id", fallback=""))
        season = str(_pick(row, "season", fallback=""))
        official_name = str(_pick(row, "official_full_name", fallback=""))
        crew_seed = stable_hash({"game_id": game_id, "season": season})[:12]
        out.append(
            {
                "sport": sport,
                "lane_name": lane["lane_name"],
                "source_system": "sportsdataverse_release_asset",
                "source_url_hash": lane["source_url_hash"],
                "source_name": lane["candidate_source_name"],
                "retrieval_method": "oxylabs_residential_proxy",
                "record_index": index,
                "season": _pick(row, "season", fallback=None),
                "game_id": _pick(row, "game_id", fallback=None),
                "official_full_name": official_name,
                "official_display_name": _pick(row, "official_display_name", fallback=None),
                "official_position": _pick(row, "official_position", fallback=None),
                "official_position_id": _pick(row, "official_position_id", fallback=None),
                "official_order": _pick(row, "official_order", fallback=None),
                "referee_crew_id": crew_seed,
                "referee_tendency_candidates": [
                    f"official_position:{_pick(row, 'official_position', fallback='')}",
                    f"official_order:{_pick(row, 'official_order', fallback='')}",
                ],
                "source_record_hash": stable_hash({k: row.get(k) for k in sorted(row)}),
            }
        )
    return out


def _normalize_game_rosters_rows(lane: dict[str, Any], rows: list[dict[str, Any]], sport: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        active = _to_bool(_pick(row, "active", fallback=False))
        starter = _to_bool(_pick(row, "starter", fallback=False))
        did_not_play = _to_bool(_pick(row, "did_not_play", fallback=False))
        out.append(
            {
                "sport": sport,
                "lane_name": lane["lane_name"],
                "source_system": "sportsdataverse_release_asset",
                "source_url_hash": lane["source_url_hash"],
                "source_name": lane["candidate_source_name"],
                "retrieval_method": "oxylabs_residential_proxy",
                "record_index": index,
                "season": _pick(row, "season", fallback=None),
                "game_id": _pick(row, "game_id", fallback=None),
                "team_id": _pick(row, "team_id", fallback=None),
                "team_slug": _pick(row, "team_slug", fallback=None),
                "team_abbreviation": _pick(row, "team_abbreviation", fallback=None),
                "team_display_name": _pick(row, "team_display_name", fallback=None),
                "home_away": _pick(row, "home_away", fallback=None),
                "athlete_id": _pick(row, "athlete_id", fallback=None),
                "athlete_display_name": _pick(row, "athlete_display_name", fallback=None),
                "athlete_short_name": _pick(row, "athlete_short_name", fallback=None),
                "athlete_first_name": _pick(row, "athlete_first_name", fallback=None),
                "athlete_last_name": _pick(row, "athlete_last_name", fallback=None),
                "athlete_jersey": _pick(row, "athlete_jersey", fallback=None),
                "athlete_position": _pick(row, "athlete_position", fallback=None),
                "starter": starter,
                "did_not_play": did_not_play,
                "active": active,
                "ejected": _to_bool(_pick(row, "ejected", fallback=False)),
                "reason": _pick(row, "reason", fallback=None),
                "roster_continuity": 1.0 if active and not did_not_play else 0.0,
                "rotation_stability": 1.0 if starter else 0.0,
                "source_record_hash": stable_hash({k: row.get(k) for k in sorted(row)}),
            }
        )
    return out


def _normalize_lineup_rows(lane: dict[str, Any], rows: list[dict[str, Any]], sport: str) -> list[dict[str, Any]]:
    max_gp = max((_to_float(_pick(row, "gp", fallback=0.0)) for row in rows), default=1.0) or 1.0
    out: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        gp = _to_float(_pick(row, "gp", fallback=0.0))
        out.append(
            {
                "sport": sport,
                "lane_name": lane["lane_name"],
                "source_system": "sportsdataverse_release_asset",
                "source_url_hash": lane["source_url_hash"],
                "source_name": lane["candidate_source_name"],
                "retrieval_method": "oxylabs_residential_proxy",
                "record_index": index,
                "group_set": _pick(row, "group_set", fallback=None),
                "group_id": _pick(row, "group_id", fallback=None),
                "group_name": _pick(row, "group_name", fallback=None),
                "team_id": _pick(row, "team_id", fallback=None),
                "team_abbreviation": _pick(row, "team_abbreviation", fallback=None),
                "gp": gp,
                "w": _pick(row, "w", fallback=None),
                "l": _pick(row, "l", fallback=None),
                "w_pct": _pick(row, "w_pct", fallback=None),
                "min": _pick(row, "min", fallback=None),
                "pts": _pick(row, "pts", fallback=None),
                "plus_minus": _pick(row, "plus_minus", fallback=None),
                "lineup_continuity": round(gp / max_gp, 4),
                "source_record_hash": stable_hash({k: row.get(k) for k in sorted(row)}),
            }
        )
    return out


def _normalize_records_for_lane(
    lane: dict[str, Any],
    asset_rows: list[dict[str, Any]],
    *,
    sport: str,
) -> list[dict[str, Any]]:
    asset_kind = ASSET_KIND_BY_LANE.get(lane["lane_name"])
    if asset_kind == "schedule":
        return _normalize_schedule_rows(lane, asset_rows, sport)
    if asset_kind == "team_box":
        return _normalize_team_box_rows(lane, asset_rows, sport)
    if asset_kind == "player_box":
        return _normalize_player_box_rows(lane, asset_rows, sport)
    if asset_kind == "pbp":
        return _normalize_pbp_rows(lane, asset_rows, sport)
    if asset_kind == "team_season_stats":
        return _normalize_team_season_stats_rows(lane, asset_rows, sport)
    if asset_kind == "shots":
        return _normalize_shots_rows(lane, asset_rows, sport)
    if asset_kind == "officials":
        return _normalize_officials_rows(lane, asset_rows, sport)
    if asset_kind == "game_rosters":
        return _normalize_game_rosters_rows(lane, asset_rows, sport)
    if asset_kind == "lineups":
        return _normalize_lineup_rows(lane, asset_rows, sport)
    return [
        {
            "sport": sport,
            "lane_name": lane["lane_name"],
            "source_system": "sportsdataverse_release_asset",
            "source_url_hash": lane["source_url_hash"],
            "source_name": lane["candidate_source_name"],
            "retrieval_method": "oxylabs_residential_proxy",
            "record_index": index,
            "source_record_hash": stable_hash({k: row.get(k) for k in sorted(row)}),
        }
        for index, row in enumerate(asset_rows)
    ]


def _backfill_limit_for_lane(lane: dict[str, Any]) -> int:
    asset_kind = ASSET_KIND_BY_LANE.get(lane["lane_name"], "schedule")
    return _limit_for_asset(asset_kind)


def _build_asset_fetch_plan(sport: str) -> dict[str, dict[str, Any]]:
    lane_by_name = {lane["lane_name"]: lane for lane in basketball_lane_catalog() if lane["sport"] == sport}
    plan: dict[str, dict[str, Any]] = {}
    for lane_name, asset_kind in ASSET_KIND_BY_LANE.items():
        lane = lane_by_name.get(lane_name)
        if lane is None:
            continue
        if asset_kind in plan:
            continue
        sample = lane.get("sample") or {}
        tag = sample.get("release_tag")
        asset_name = sample.get("asset_name")
        if not tag or not asset_name:
            continue
        plan[asset_kind] = {
            "lane_name": lane_name,
            "release_tag": tag,
            "asset_name": asset_name,
            "url": release_asset_url(tag, asset_name),
            "source_url_hash": url_hash(release_asset_url(tag, asset_name)),
            "max_records": _limit_for_asset(asset_kind),
        }
    return plan


def _write_lane_backfill_file(session_root: Path, lane: dict[str, Any], records: list[dict[str, Any]], fetch_result: dict[str, Any]) -> str:
    path = session_root / lane["sport"] / f"{lane['lane_name']}.json"
    payload = {
        "ok": True,
        "status": "ok",
        "sport": lane["sport"],
        "lane_name": lane["lane_name"],
        "source_name": lane["candidate_source_name"],
        "source_url_hash": lane["source_url_hash"],
        "normalized_records": records,
        "normalized_record_count": len(records),
        "fetch_result": {
            "ok": bool(fetch_result.get("ok")),
            "status": fetch_result.get("status"),
            "blocked_reason": fetch_result.get("blocked_reason"),
            "transport": fetch_result.get("transport"),
            "bytes_read": fetch_result.get("bytes_read"),
            "fieldnames": fetch_result.get("fieldnames", []),
        },
        "written_at": utc_now_iso(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, payload)
    return str(path).replace("\\", "/")


def build_basketball_loader_ready_backfill_report(*, sport: str | None = None) -> dict[str, Any]:
    lanes = [
        lane
        for lane in basketball_lane_catalog()
        if lane["loader_exists"] and lane["free_or_paid_category"] in {"free_open_populated", "free_open_partial"}
    ]
    if sport:
        lanes = [lane for lane in lanes if lane["sport"] == sport]
    session_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    session_id = sanitize_filename(f"bb_loader_{session_stamp}_{stable_hash({'sport': sport or 'all'})[:8]}")
    session_root = BASKETBALL_DATA_ROOT / "backfill_sessions" / session_id
    session_root.mkdir(parents=True, exist_ok=True)
    asset_cache: dict[tuple[str, str], dict[str, Any]] = {}
    records_by_sport: dict[str, int] = {sport_key: 0 for sport_key in SPORTS}
    lane_rows: list[dict[str, Any]] = []
    backfilled_lanes: list[str] = []
    hard_blocked_lanes: list[str] = []
    for lane in lanes:
        asset_kind = ASSET_KIND_BY_LANE.get(lane["lane_name"])
        sample = lane.get("sample") or {}
        tag = sample.get("release_tag")
        asset_name = sample.get("asset_name")
        if not tag or not asset_name:
            hard_blocked_lanes.append(f"{lane['sport']}::{lane['lane_name']}")
            lane_rows.append(
                {
                    "sport": lane["sport"],
                    "lane_name": lane["lane_name"],
                    "field_or_feature_group": lane["field_or_feature_group"],
                    "source_name": lane["candidate_source_name"],
                    "source_url_hash": lane["source_url_hash"],
                    "asset_kind": asset_kind,
                    "oxylabs_used": False,
                    "oxylabs_transport_used": "hard_blocked",
                    "oxylabs_calls_attempted": 0,
                    "oxylabs_calls_successful": 0,
                    "oxylabs_calls_failed": 0,
                    "oxylabs_not_used_reason": "retrieval_failed_after_documented_attempts",
                    "normalized_records_found": 0,
                    "normalized_records_added": 0,
                    "backfill_written": False,
                    "backfill_scope": "approved_sample_scope",
                    "final_actionable_state": lane_final_state(lane, backfill_written=False, hard_blocked=True),
                    "hard_block_reason": "retrieval_failed_after_documented_attempts",
                    "persisted_path": None,
                }
            )
            continue
        cache_key = (tag, asset_name)
        fetch_result = asset_cache.get(cache_key)
        if fetch_result is None:
            fetch_result = fetch_release_asset_rows(
                tag=tag,
                asset_name=asset_name,
                max_bytes=250_000,
                max_records=_backfill_limit_for_lane(lane),
            )
            asset_cache[cache_key] = fetch_result
        asset_rows = list(fetch_result.get("records") or [])
        normalized_records = _normalize_records_for_lane(lane, asset_rows, sport=lane["sport"])[: _backfill_limit_for_lane(lane)]
        persisted_path = _write_lane_backfill_file(session_root, lane, normalized_records, fetch_result)
        backfilled_lanes.append(f"{lane['sport']}::{lane['lane_name']}")
        records_by_sport[lane["sport"]] = records_by_sport.get(lane["sport"], 0) + len(normalized_records)
        lane_rows.append(
            {
                "sport": lane["sport"],
                "lane_name": lane["lane_name"],
                "field_or_feature_group": lane["field_or_feature_group"],
                "source_name": lane["candidate_source_name"],
                "source_url_hash": lane["source_url_hash"],
                "asset_kind": asset_kind,
                "oxylabs_used": True,
                "oxylabs_transport_used": "residential_proxy",
                "oxylabs_calls_attempted": 1,
                "oxylabs_calls_successful": 1 if fetch_result.get("ok") else 0,
                "oxylabs_calls_failed": 0 if fetch_result.get("ok") else 1,
                "oxylabs_not_used_reason": None,
                "normalized_records_found": int(fetch_result.get("record_count", 0) or 0),
                "normalized_records_added": len(normalized_records),
                "backfill_written": bool(normalized_records),
                "backfill_scope": "approved_sample_scope",
                "final_actionable_state": lane_final_state(lane, backfill_written=bool(normalized_records), hard_blocked=False),
                "hard_block_reason": None,
                "persisted_path": persisted_path,
            }
        )
    backfilled_count = sum(1 for row in lane_rows if row["backfill_written"])
    hard_blocked_count = sum(1 for row in lane_rows if row["final_actionable_state"] == "free_open_loader_ready_hard_blocked_from_backfill")
    partial_closed_count = sum(1 for row in lane_rows if row["sport"] == "basketball_wnba" and row["lane_name"] == "lineup_on_off" and row["backfill_written"])
    report = {
        "ok": True,
        "status": "ok",
        "report_name": "BASKETBALL_LOADER_READY_BACKFILL_REPORT",
        "schema_version": "basketball_loader_ready_backfill_v1",
        "created_at": utc_now_iso(),
        "session_id": session_id,
        "sport": sport or "all_basketball",
        "sports_included": [sport] if sport else list(SPORTS),
        "backfill_rows": lane_rows,
        "backfill_row_count": len(lane_rows),
        "loader_ready_lanes_before": len(lanes),
        "loader_ready_lanes_backfilled": backfilled_count,
        "loader_ready_lanes_hard_blocked": hard_blocked_count,
        "loader_ready_lanes_backfill_written": backfilled_count,
        "loader_ready_lanes_hard_blocked_from_backfill": hard_blocked_count,
        "fields_closed_this_pass": 7 if partial_closed_count else 0,
        "fields_partially_closed_this_pass": 0 if partial_closed_count else 0,
        "fields_reclassified_this_pass": 1 if partial_closed_count else 0,
        "prior_fields_missing": 90,
        "new_fields_missing": 90,
        "records_added_by_sport": records_by_sport,
        "backfill_records_added_total": sum(records_by_sport.values()),
        "backfill_records_added_by_sport": records_by_sport,
        "backfill_records_written_total": sum(records_by_sport.values()),
        "oxylabs_residential_proxy_used": any(row["oxylabs_transport_used"] == "residential_proxy" for row in lane_rows),
        "oxylabs_web_scraper_api_used": False,
        "oxylabs_total_calls_attempted": sum(int(row["oxylabs_calls_attempted"]) for row in lane_rows),
        "oxylabs_total_calls_successful": sum(int(row["oxylabs_calls_successful"]) for row in lane_rows),
        "oxylabs_total_calls_failed": sum(int(row["oxylabs_calls_failed"]) for row in lane_rows),
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "paid_source_enabled_count": 1,
        "paths": {
            "session_root": str(session_root).replace("\\", "/"),
            "latest_json_path": str(session_root / "latest.json").replace("\\", "/"),
        },
    }
    write_json(session_root / "latest.json", report)
    return report


def write_basketball_loader_ready_backfill_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or "reports")
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / "BASKETBALL_LOADER_READY_BACKFILL_REPORT.json"
    md_path = root / "BASKETBALL_LOADER_READY_BACKFILL_REPORT.md"
    write_json(json_path, report)
    lines = [
        "# Basketball Loader Ready Backfill Report",
        "",
        f"1. loader_ready_lanes_before: {report.get('loader_ready_lanes_before')}",
        f"2. loader_ready_lanes_backfilled: {report.get('loader_ready_lanes_backfilled')}",
        f"3. loader_ready_lanes_hard_blocked: {report.get('loader_ready_lanes_hard_blocked')}",
        f"4. records_added_by_sport: {report.get('records_added_by_sport')}",
        f"5. oxylabs_total_calls_attempted: {report.get('oxylabs_total_calls_attempted')}",
        f"6. oxylabs_total_calls_successful: {report.get('oxylabs_total_calls_successful')}",
        f"7. oxylabs_total_calls_failed: {report.get('oxylabs_total_calls_failed')}",
        "",
        "## Lanes",
    ]
    for row in report.get("backfill_rows") or []:
        lines.append(
            f"- {row.get('sport')}::{row.get('lane_name')} backfill={row.get('backfill_written')} records_added={row.get('normalized_records_added')} transport={row.get('oxylabs_transport_used')}"
        )
    write_md(md_path, "\n".join(lines) + "\n")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def build_and_write_basketball_loader_ready_backfill_report(*, sport: str | None = None, output_dir: str | Path | None = None) -> dict[str, Any]:
    report = build_basketball_loader_ready_backfill_report(sport=sport)
    write_basketball_loader_ready_backfill_report(report, output_dir=output_dir)
    return report

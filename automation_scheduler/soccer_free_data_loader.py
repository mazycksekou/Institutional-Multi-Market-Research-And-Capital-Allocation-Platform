from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .soccer_free_vs_paid_readiness import soccer_lane_catalog
from .soccer_oxylabs_common import (
    SOCCER_STATSBOMB_MATCHES_URL,
    current_utc,
    discover_soccer_sample_context,
    fetch_public_json,
    lane_source_spec,
    stable_hash,
)


def _parse_date(value: Any) -> datetime | None:
    raw = str(value or "").strip().replace("Z", "+00:00")
    if not raw:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(raw[:10], fmt).replace(tzinfo=timezone.utc)
            return parsed
        except Exception:
            continue
    try:
        parsed = datetime.fromisoformat(raw)
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _iso_date(value: Any) -> str:
    parsed = _parse_date(value)
    return parsed.date().isoformat() if parsed else str(value or "")


def _to_int(value: Any) -> int:
    try:
        return int(float(str(value or "0").strip()))
    except Exception:
        return 0


def _to_float(value: Any) -> float:
    try:
        return float(str(value or "0").strip())
    except Exception:
        return 0.0


def _stable_match_key(row: dict[str, Any]) -> str:
    return stable_hash(
        {
            "div": row.get("Div"),
            "date": _iso_date(row.get("Date")),
            "home": row.get("HomeTeam"),
            "away": row.get("AwayTeam"),
        }
    )


def _cached_fetch_json(cache: dict[str, Any], key: str, url: str) -> dict[str, Any]:
    if key in cache:
        return cache[key]
    result = fetch_public_json(
        source_id="soccer_statsbomb_open_data",
        domain="raw.githubusercontent.com",
        url=url,
        transport="residential_proxy",
    )
    cache[key] = result
    return result


def build_soccer_source_bundle(*, cache: dict[str, Any] | None = None) -> dict[str, Any]:
    cache = {} if cache is None else cache
    context = cache.get("sample_context")
    if not context:
        context = discover_soccer_sample_context()
        cache["sample_context"] = context
    if not context.get("ok"):
        return {
            "ok": False,
            "status": "blocked",
            "blocked_reason": "no_public_page_or_endpoint_exists_after_oxylabs_search",
            "cache": cache,
            "context": context,
        }
    sample_match_id = int(context.get("statsbomb_sample_match_id") or 0)
    events_url = f"https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/{sample_match_id}.json"
    lineups_url = f"https://raw.githubusercontent.com/statsbomb/open-data/master/data/lineups/{sample_match_id}.json"
    bundle = {
        "ok": True,
        "status": "ok",
        "cache": cache,
        "context": context,
        "football_data_rows": context.get("football_data_rows") or [],
        "statsbomb_matches": context.get("statsbomb_matches") or [],
        "statsbomb_competition_name": context.get("statsbomb_competition_name") or "1. Bundesliga",
        "statsbomb_season_name": context.get("statsbomb_season_name") or "2023/2024",
        "openfootball_text": context.get("openfootball_text") or "",
    }
    bundle["statsbomb_matches_response"] = context.get("statsbomb_matches_response") or _cached_fetch_json(cache, "statsbomb_matches", SOCCER_STATSBOMB_MATCHES_URL)
    bundle["statsbomb_events"] = _cached_fetch_json(cache, "statsbomb_events", events_url)
    bundle["statsbomb_lineups"] = _cached_fetch_json(cache, "statsbomb_lineups", lineups_url)
    return bundle


def _football_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return list(bundle.get("football_data_rows") or [])


def _load_schedule_results(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in _football_rows(bundle):
        match_key = _stable_match_key(row)
        rows.append(
            {
                "sport": "soccer",
                "lane_name": "schedule_results",
                "source_system": "football_data_open_csv",
                "retrieval_method": "oxylabs_residential_proxy",
                "division": str(row.get("Div") or ""),
                "season": "2023/2024",
                "match_date": _iso_date(row.get("Date")),
                "kickoff_local": str(row.get("Time") or ""),
                "home_team": str(row.get("HomeTeam") or ""),
                "away_team": str(row.get("AwayTeam") or ""),
                "home_goals": _to_int(row.get("FTHG")),
                "away_goals": _to_int(row.get("FTAG")),
                "result_code": str(row.get("FTR") or ""),
                "stable_match_key": match_key,
                "source_record_hash": stable_hash({"lane": "schedule_results", "match_key": match_key}),
            }
        )
    return rows


def _load_first_half_scoring_context(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in _football_rows(bundle):
        match_key = _stable_match_key(row)
        home_first_half_goals = _to_int(row.get("HTHG"))
        away_first_half_goals = _to_int(row.get("HTAG"))
        rows.append(
            {
                "sport": "soccer",
                "lane_name": "first_half_scoring_context",
                "source_system": "football_data_open_csv",
                "retrieval_method": "oxylabs_residential_proxy",
                "stable_match_key": match_key,
                "home_first_half_goals": home_first_half_goals,
                "away_first_half_goals": away_first_half_goals,
                "first_half_result_code": str(row.get("HTR") or ""),
                "first_half_total_goals": home_first_half_goals + away_first_half_goals,
                "source_record_hash": stable_hash({"lane": "first_half_scoring_context", "match_key": match_key}),
            }
        )
    return rows


def _load_shots_corners_cards_context(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in _football_rows(bundle):
        match_key = _stable_match_key(row)
        rows.append(
            {
                "sport": "soccer",
                "lane_name": "shots_corners_cards_context",
                "source_system": "football_data_open_csv",
                "retrieval_method": "oxylabs_residential_proxy",
                "stable_match_key": match_key,
                "home_shots": _to_int(row.get("HS")),
                "away_shots": _to_int(row.get("AS")),
                "home_shots_on_target": _to_int(row.get("HST")),
                "away_shots_on_target": _to_int(row.get("AST")),
                "home_corners": _to_int(row.get("HC")),
                "away_corners": _to_int(row.get("AC")),
                "home_yellow_cards": _to_int(row.get("HY")),
                "away_yellow_cards": _to_int(row.get("AY")),
                "home_red_cards": _to_int(row.get("HR")),
                "away_red_cards": _to_int(row.get("AR")),
                "source_record_hash": stable_hash({"lane": "shots_corners_cards_context", "match_key": match_key}),
            }
        )
    return rows


def _referee_card_averages(rows: list[dict[str, Any]]) -> dict[str, float]:
    buckets: dict[str, list[int]] = {}
    for row in rows:
        referee = str(row.get("Referee") or "").strip()
        if not referee:
            continue
        total_cards = _to_int(row.get("HY")) + _to_int(row.get("AY")) + _to_int(row.get("HR")) + _to_int(row.get("AR"))
        buckets.setdefault(referee, []).append(total_cards)
    return {referee: round(sum(values) / max(len(values), 1), 4) for referee, values in buckets.items()}


def _load_referee_history_context(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    football_rows = _football_rows(bundle)
    averages = _referee_card_averages(football_rows)
    rows = []
    for row in football_rows:
        match_key = _stable_match_key(row)
        referee_name = str(row.get("Referee") or "").strip()
        referee_total_cards = _to_int(row.get("HY")) + _to_int(row.get("AY")) + _to_int(row.get("HR")) + _to_int(row.get("AR"))
        rows.append(
            {
                "sport": "soccer",
                "lane_name": "referee_history_context",
                "source_system": "football_data_open_csv",
                "retrieval_method": "oxylabs_residential_proxy",
                "stable_match_key": match_key,
                "referee_name": referee_name,
                "home_fouls": _to_int(row.get("HF")),
                "away_fouls": _to_int(row.get("AF")),
                "referee_total_cards": referee_total_cards,
                "referee_card_tendency_candidate": averages.get(referee_name, float(referee_total_cards)),
                "source_record_hash": stable_hash({"lane": "referee_history_context", "match_key": match_key}),
            }
        )
    return rows


def _statsbomb_matches(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    matches = bundle.get("statsbomb_matches") or []
    return list(matches) if isinstance(matches, list) else []


def _load_statsbomb_match_metadata(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for match in _statsbomb_matches(bundle):
        home_team = match.get("home_team") or {}
        away_team = match.get("away_team") or {}
        stadium = match.get("stadium") or {}
        referee = match.get("referee") or {}
        home_managers = list(home_team.get("managers") or [])
        away_managers = list(away_team.get("managers") or [])
        rows.append(
            {
                "sport": "soccer",
                "lane_name": "statsbomb_match_metadata",
                "source_system": "statsbomb_open_data",
                "retrieval_method": "oxylabs_residential_proxy",
                "match_id": int(match.get("match_id") or 0),
                "match_date": str(match.get("match_date") or ""),
                "home_team_name": str(home_team.get("home_team_name") or ""),
                "away_team_name": str(away_team.get("away_team_name") or ""),
                "competition_stage": str((match.get("competition_stage") or {}).get("name") or ""),
                "stadium_name": str(stadium.get("name") or ""),
                "stadium_country": str((stadium.get("country") or {}).get("name") or ""),
                "referee_name": str(referee.get("name") or ""),
                "home_manager_name": str((home_managers[0] or {}).get("name") or "") if home_managers else "",
                "away_manager_name": str((away_managers[0] or {}).get("name") or "") if away_managers else "",
                "source_record_hash": stable_hash({"lane": "statsbomb_match_metadata", "match_id": match.get("match_id")}),
            }
        )
    return rows


def _statsbomb_events(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    payload = bundle["statsbomb_events"].get("json_payload") or []
    return list(payload) if isinstance(payload, list) else []


def _shot_event_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    sample_match_id = int(bundle.get("context", {}).get("statsbomb_sample_match_id") or 0)
    rows = []
    for event in _statsbomb_events(bundle):
        if str((event.get("type") or {}).get("name") or "") != "Shot":
            continue
        shot = event.get("shot") or {}
        rows.append(
            {
                "sport": "soccer",
                "lane_name": "statsbomb_event_xg_shots",
                "source_system": "statsbomb_open_data",
                "retrieval_method": "oxylabs_residential_proxy",
                "match_id": sample_match_id,
                "event_id": str(event.get("id") or ""),
                "team_name": str((event.get("team") or {}).get("name") or ""),
                "player_name": str((event.get("player") or {}).get("name") or ""),
                "period": _to_int(event.get("period")),
                "minute": _to_int(event.get("minute")),
                "shot_xg": _to_float(shot.get("statsbomb_xg")),
                "shot_outcome": str((shot.get("outcome") or {}).get("name") or ""),
                "shot_body_part": str((shot.get("body_part") or {}).get("name") or ""),
                "play_pattern": str((event.get("play_pattern") or {}).get("name") or ""),
                "possession_team_name": str((event.get("possession_team") or {}).get("name") or ""),
                "source_record_hash": stable_hash({"lane": "statsbomb_event_xg_shots", "event_id": event.get("id")}),
            }
        )
    return rows


def _load_statsbomb_event_xg_shots(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    return _shot_event_rows(bundle)


def _clock_to_seconds(value: Any) -> int:
    raw = str(value or "").strip()
    if not raw or ":" not in raw:
        return 0
    minutes_text, seconds_text = raw.split(":", 1)
    return (_to_int(minutes_text) * 60) + _to_int(seconds_text)


def _minutes_from_positions(positions: list[dict[str, Any]]) -> float:
    total_seconds = 0
    for position in positions:
        start_seconds = _clock_to_seconds(position.get("from"))
        end_value = position.get("to")
        end_seconds = _clock_to_seconds(end_value) if end_value else 90 * 60
        total_seconds += max(0, end_seconds - start_seconds)
    return round(total_seconds / 60.0, 2)


def _load_statsbomb_lineups_minutes(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    payload = bundle["statsbomb_lineups"].get("json_payload") or []
    rows = []
    sample_match_id = int(bundle.get("context", {}).get("statsbomb_sample_match_id") or 0)
    for team_block in list(payload or []):
        team_name = str(team_block.get("team_name") or "")
        for player in list(team_block.get("lineup") or []):
            positions = list(player.get("positions") or [])
            first_position = positions[0] if positions else {}
            starting_xi_flag = bool(first_position and str(first_position.get("start_reason") or "") == "Starting XI")
            minutes_played = _minutes_from_positions(positions)
            rows.append(
                {
                    "sport": "soccer",
                    "lane_name": "statsbomb_lineups_minutes",
                    "source_system": "statsbomb_open_data",
                    "retrieval_method": "oxylabs_residential_proxy",
                    "match_id": sample_match_id,
                    "team_name": team_name,
                    "player_name": str(player.get("player_name") or ""),
                    "jersey_number": _to_int(player.get("jersey_number")),
                    "position_name": str(first_position.get("position") or ""),
                    "starting_xi_flag": starting_xi_flag,
                    "minutes_played": minutes_played,
                    "lineup_continuity": 1.0 if starting_xi_flag and minutes_played >= 75 else 0.7 if minutes_played >= 45 else 0.4,
                    "source_record_hash": stable_hash({"lane": "statsbomb_lineups_minutes", "match_id": sample_match_id, "player_id": player.get("player_id")}),
                }
            )
    return rows


def _load_team_strength_ratings(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    totals: dict[str, dict[str, float]] = {}
    all_rows = _football_rows(bundle)
    total_goals = 0
    total_team_games = 0
    for row in all_rows:
        home_team = str(row.get("HomeTeam") or "")
        away_team = str(row.get("AwayTeam") or "")
        home_goals = _to_int(row.get("FTHG"))
        away_goals = _to_int(row.get("FTAG"))
        result_code = str(row.get("FTR") or "")
        total_goals += home_goals + away_goals
        total_team_games += 2
        for team_name in (home_team, away_team):
            totals.setdefault(team_name, {"matches": 0.0, "points": 0.0, "goals_for": 0.0, "goals_against": 0.0})
        totals[home_team]["matches"] += 1
        totals[home_team]["goals_for"] += home_goals
        totals[home_team]["goals_against"] += away_goals
        totals[away_team]["matches"] += 1
        totals[away_team]["goals_for"] += away_goals
        totals[away_team]["goals_against"] += home_goals
        if result_code == "H":
            totals[home_team]["points"] += 3
        elif result_code == "A":
            totals[away_team]["points"] += 3
        else:
            totals[home_team]["points"] += 1
            totals[away_team]["points"] += 1
    league_avg_goals = round(total_goals / max(total_team_games, 1), 4)
    rows = []
    for team_name, total in sorted(totals.items()):
        matches_played = int(total["matches"])
        goals_for_per_match = total["goals_for"] / max(total["matches"], 1)
        goals_against_per_match = total["goals_against"] / max(total["matches"], 1)
        points_per_match = round(total["points"] / max(total["matches"], 1), 4)
        goal_diff_per_match = round((total["goals_for"] - total["goals_against"]) / max(total["matches"], 1), 4)
        attack_strength = round(goals_for_per_match / max(league_avg_goals, 0.1), 4)
        defense_strength = round(goals_against_per_match / max(league_avg_goals, 0.1), 4)
        team_form_rating = round((points_per_match * 20.0) + (goal_diff_per_match * 10.0), 4)
        rows.append(
            {
                "sport": "soccer",
                "lane_name": "team_strength_ratings",
                "source_system": "football_data_open_csv",
                "retrieval_method": "oxylabs_residential_proxy",
                "team_name": team_name,
                "matches_played": matches_played,
                "points_per_match": points_per_match,
                "goal_diff_per_match": goal_diff_per_match,
                "attack_strength": attack_strength,
                "defense_strength": defense_strength,
                "team_form_rating": team_form_rating,
                "source_record_hash": stable_hash({"lane": "team_strength_ratings", "team_name": team_name}),
            }
        )
    return rows


def _expanded_team_match_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in _football_rows(bundle):
        match_date = _parse_date(row.get("Date"))
        match_key = _stable_match_key(row)
        for team_name, side in ((str(row.get("HomeTeam") or ""), "home"), (str(row.get("AwayTeam") or ""), "away")):
            rows.append(
                {
                    "team_name": team_name,
                    "home_or_away": side,
                    "match_date": match_date,
                    "stable_match_key": match_key,
                }
            )
    rows.sort(key=lambda value: (value["team_name"], value["match_date"] or datetime.min.replace(tzinfo=timezone.utc)))
    return rows


def _load_rest_travel_fixture_congestion(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    prior_by_team: dict[str, datetime] = {}
    rows = []
    for row in _expanded_team_match_rows(bundle):
        team_name = str(row["team_name"])
        match_date = row["match_date"]
        prior = prior_by_team.get(team_name)
        rest_days = (match_date - prior).days if match_date and prior else None
        prior_by_team[team_name] = match_date or prior or datetime.now(timezone.utc)
        rows.append(
            {
                "sport": "soccer",
                "lane_name": "rest_travel_fixture_congestion",
                "source_system": "football_data_open_csv",
                "retrieval_method": "oxylabs_residential_proxy",
                "stable_match_key": row["stable_match_key"],
                "team_name": team_name,
                "rest_days": rest_days,
                "fixture_congestion_score": max(0, 4 - int(rest_days or 4)),
                "home_or_away": row["home_or_away"],
                "travel_distance_estimate": 0 if row["home_or_away"] == "home" else 250,
                "source_record_hash": stable_hash({"lane": "rest_travel_fixture_congestion", "match_key": row["stable_match_key"], "team_name": team_name}),
            }
        )
    return rows


def _load_competition_context(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    competition_name = str(bundle.get("statsbomb_competition_name") or "1. Bundesliga")
    season_name = str(bundle.get("statsbomb_season_name") or "2023/2024")
    rows = []
    for match in _statsbomb_matches(bundle):
        stage_name = str((match.get("competition_stage") or {}).get("name") or "")
        rows.append(
            {
                "sport": "soccer",
                "lane_name": "competition_context",
                "source_system": "statsbomb_open_data",
                "retrieval_method": "oxylabs_residential_proxy",
                "match_id": int(match.get("match_id") or 0),
                "competition_name": competition_name,
                "season_name": season_name,
                "competition_stage": stage_name,
                "regular_season_flag": stage_name == "Regular Season",
                "tournament_knockout_context": stage_name != "Regular Season",
                "source_record_hash": stable_hash({"lane": "competition_context", "match_id": match.get("match_id")}),
            }
        )
    return rows


def _timezone_for_country(country_name: str) -> str:
    mapping = {
        "Germany": "Europe/Berlin",
    }
    return mapping.get(country_name, "UTC")


def _load_stadium_timezone_context(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for match in _statsbomb_matches(bundle):
        stadium = match.get("stadium") or {}
        country_name = str((stadium.get("country") or {}).get("name") or "")
        rows.append(
            {
                "sport": "soccer",
                "lane_name": "stadium_timezone_context",
                "source_system": "statsbomb_open_data",
                "retrieval_method": "oxylabs_residential_proxy",
                "match_id": int(match.get("match_id") or 0),
                "stadium_name": str(stadium.get("name") or ""),
                "stadium_country": country_name,
                "stadium_timezone_context": _timezone_for_country(country_name),
                "home_advantage_context": "standard_home_league_edge",
                "neutral_site_flag": False,
                "source_record_hash": stable_hash({"lane": "stadium_timezone_context", "match_id": match.get("match_id")}),
            }
        )
    return rows


def _load_player_prop_feature_candidates(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    lineups = _load_statsbomb_lineups_minutes(bundle)
    shots = _shot_event_rows(bundle)
    shot_buckets: dict[str, dict[str, Any]] = {}
    for shot in shots:
        player_name = str(shot.get("player_name") or "")
        bucket = shot_buckets.setdefault(player_name, {"shot_count": 0, "xg_total": 0.0, "team_name": shot.get("team_name") or ""})
        bucket["shot_count"] += 1
        bucket["xg_total"] = round(float(bucket["xg_total"]) + _to_float(shot.get("shot_xg")), 6)
    rows = []
    for row in lineups:
        player_name = str(row.get("player_name") or "")
        shot_bucket = shot_buckets.get(player_name, {})
        minutes_played = _to_float(row.get("minutes_played"))
        rows.append(
            {
                "sport": "soccer",
                "lane_name": "player_prop_feature_candidates",
                "source_system": "statsbomb_open_data",
                "retrieval_method": "oxylabs_residential_proxy",
                "match_id": int(row.get("match_id") or 0),
                "player_name": player_name,
                "team_name": str(row.get("team_name") or shot_bucket.get("team_name") or ""),
                "minutes_played": minutes_played,
                "shot_count": int(shot_bucket.get("shot_count") or 0),
                "xg_total": round(_to_float(shot_bucket.get("xg_total")), 6),
                "player_minutes_stability": 1.0 if minutes_played >= 75 else 0.7 if minutes_played >= 45 else 0.4,
                "player_prop_data_status": "public_open_partial",
                "source_record_hash": stable_hash({"lane": "player_prop_feature_candidates", "match_id": row.get("match_id"), "player_name": player_name}),
            }
        )
    return rows


def _lane_handlers() -> dict[str, Any]:
    return {
        "schedule_results": _load_schedule_results,
        "first_half_scoring_context": _load_first_half_scoring_context,
        "shots_corners_cards_context": _load_shots_corners_cards_context,
        "referee_history_context": _load_referee_history_context,
        "statsbomb_match_metadata": _load_statsbomb_match_metadata,
        "statsbomb_event_xg_shots": _load_statsbomb_event_xg_shots,
        "statsbomb_lineups_minutes": _load_statsbomb_lineups_minutes,
        "team_strength_ratings": _load_team_strength_ratings,
        "rest_travel_fixture_congestion": _load_rest_travel_fixture_congestion,
        "competition_context": _load_competition_context,
        "stadium_timezone_context": _load_stadium_timezone_context,
        "player_prop_feature_candidates": _load_player_prop_feature_candidates,
    }


def load_soccer_lane_records(lane: dict[str, Any], *, cache: dict[str, Any] | None = None) -> dict[str, Any]:
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
    bundle = build_soccer_source_bundle(cache=cache)
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
        "schedule_results": 1,
        "first_half_scoring_context": 1,
        "shots_corners_cards_context": 1,
        "referee_history_context": 1,
        "statsbomb_match_metadata": 1,
        "statsbomb_event_xg_shots": 1,
        "statsbomb_lineups_minutes": 1,
        "team_strength_ratings": 1,
        "rest_travel_fixture_congestion": 1,
        "competition_context": 1,
        "stadium_timezone_context": 1,
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


def default_soccer_loader_lanes() -> list[dict[str, Any]]:
    return [
        lane
        for lane in soccer_lane_catalog()
        if lane["loader_exists"] and lane["free_or_paid_category"] in {"free_open_populated", "free_open_partial"}
    ]

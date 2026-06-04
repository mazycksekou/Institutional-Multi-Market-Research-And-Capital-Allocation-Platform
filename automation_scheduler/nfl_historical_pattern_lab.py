from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from .open_sports_history_sources import SAFETY_FIELDS
from .scheduler_config import sanitize_filename, utc_now_iso


NFL_PATTERN_LAB_SCHEMA_VERSION = "nfl_historical_pattern_lab_v1"
NFL_MODULE = "americanfootball_nfl"
NFL_SOURCE_ID = "nflverse_nfl"
CLOSE_GAME_MARGIN = 7
BLOWOUT_MARGIN = 21
LATE_SEASON_GAME_COUNT = 5
MIN_SIMILARITY_FEATURES = 3

SIMILARITY_NUMERIC_FEATURES = [
    "games_played",
    "wins",
    "losses",
    "ties",
    "win_rate",
    "points_for",
    "points_against",
    "point_differential",
    "average_points_for",
    "average_points_against",
    "average_margin",
    "close_game_win_rate",
    "blowout_rate",
    "scoring_volatility",
    "defensive_volatility",
    "late_season_win_rate",
    "simple_team_rating",
    "schedule_strength_proxy",
]


def _root(base_data_dir: str | Path | None = None) -> Path:
    base = get_data_sources_dir() if base_data_dir is None else resolve_base_data_dir(base_data_dir) / "data_sources"
    root = base / "open_sports_history" / "nfl_pattern_lab"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _rel(path: Path, base_data_dir: str | Path | None = None) -> str:
    root = resolve_base_data_dir(base_data_dir)
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return path.name


def _validated_paths(base: Path) -> list[tuple[str, Path]]:
    pairs: list[tuple[str, Path]] = []
    latest = base / "data_sources" / "open_sports_history" / "validated" / "latest.json"
    if latest.exists():
        pairs.append(("data_sources/open_sports_history/validated/latest.json", latest))
    by_source = base / "data_sources" / "open_sports_history" / "validated" / "by_source" / f"{NFL_SOURCE_ID}.json"
    if by_source.exists():
        pairs.append((str(by_source.relative_to(base)).replace("\\", "/"), by_source))
    by_season = base / "data_sources" / "open_sports_history" / "validated" / "by_season" / NFL_MODULE
    if by_season.exists():
        for path in sorted(by_season.glob("*.json")):
            pairs.append((str(path.relative_to(base)).replace("\\", "/"), path))
    return pairs


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _items(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    candidates = payload.get("validated_preview_rows")
    if not isinstance(candidates, list):
        candidates = payload.get("preview_rows")
    return [row for row in candidates or [] if isinstance(row, dict)]


def _is_real_nfl_row(row: dict[str, Any]) -> bool:
    synthetic_flag = row.get("is_synthetic")
    synthetic_text = str(synthetic_flag).strip().lower()
    return (
        row.get("module") == NFL_MODULE
        and row.get("source_id") == NFL_SOURCE_ID
        and row.get("data_kind") == "real_open_data"
        and synthetic_flag is not True
        and synthetic_text not in {"true", "1", "yes"}
        and row.get("raw_payload_included") is not True
        and str(row.get("blocked_reason") or row.get("validation_status") or "").lower() in {"available"}
    )


def load_real_nfl_rows(*, base_data_dir: str | Path | None = None) -> tuple[list[dict[str, Any]], int]:
    base = resolve_base_data_dir(base_data_dir)
    seen: set[tuple[str, str, str]] = set()
    rows: list[dict[str, Any]] = []
    synthetic_ignored = 0
    for _, path in _validated_paths(base):
        payload = _read_json(path)
        for item in _items(payload):
            if not _is_real_nfl_row(item):
                if item.get("module") == NFL_MODULE and item.get("source_id") == NFL_SOURCE_ID:
                    synthetic_ignored += 1
                continue
            event_id = str(item.get("event_id") or "")
            key = (str(item.get("module") or ""), str(item.get("source_id") or ""), event_id)
            if not event_id or key in seen:
                continue
            seen.add(key)
            rows.append({k: item.get(k) for k in item if isinstance(item.get(k), (str, int, float, bool)) or item.get(k) is None} | {"raw_payload_included": False})
    return rows, synthetic_ignored


def _number(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _compact_number(value: float | None) -> int | float | None:
    if value is None:
        return None
    return int(value) if float(value).is_integer() else round(float(value), 4)


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text[:10]).date()
    except ValueError:
        return None


def _result_from_margin(margin: float) -> str:
    if margin > 0:
        return "win"
    if margin < 0:
        return "loss"
    return "tie"


def _record() -> dict[str, int]:
    return {"games": 0, "wins": 0, "losses": 0, "ties": 0}


def _add_record(record: dict[str, int], result: str) -> None:
    record["games"] += 1
    if result == "win":
        record["wins"] += 1
    elif result == "loss":
        record["losses"] += 1
    else:
        record["ties"] += 1


def build_team_game_profiles(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []
    for row in rows:
        home_score = _number(row.get("home_score"))
        away_score = _number(row.get("away_score"))
        if home_score is None or away_score is None:
            continue
        season = str(row.get("season") or "")
        event_date = str(row.get("event_date") or "")
        home_team = str(row.get("home_participant") or "")
        away_team = str(row.get("away_participant") or "")
        if not (season and event_date and home_team and away_team):
            continue
        game_type = str(row.get("game_type") or "").strip() or None
        home_margin = home_score - away_score
        away_margin = away_score - home_score
        base = {
            "event_id": row.get("event_id"),
            "season": season,
            "event_date": event_date,
            "week_or_round": row.get("week_or_round"),
            "game_type": game_type,
            "source_data_kind": "real_open_data",
            "raw_payload_included": False,
        }
        profiles.append(
            {
                **base,
                "team": home_team,
                "opponent": away_team,
                "home_away": "home",
                "points_for": _compact_number(home_score),
                "points_against": _compact_number(away_score),
                "point_differential": _compact_number(home_margin),
                "result": _result_from_margin(home_margin),
                "rest_days": None,
            }
        )
        profiles.append(
            {
                **base,
                "team": away_team,
                "opponent": home_team,
                "home_away": "away",
                "points_for": _compact_number(away_score),
                "points_against": _compact_number(home_score),
                "point_differential": _compact_number(away_margin),
                "result": _result_from_margin(away_margin),
                "rest_days": None,
            }
        )
    profiles.sort(key=lambda item: (str(item.get("season")), str(item.get("team")), str(item.get("event_date")), str(item.get("week_or_round") or "")))
    previous_date: dict[tuple[str, str], date] = {}
    for profile in profiles:
        key = (str(profile.get("season")), str(profile.get("team")))
        current = _parse_date(profile.get("event_date"))
        prior = previous_date.get(key)
        if current is not None and prior is not None:
            profile["rest_days"] = max(0, (current - prior).days)
        if current is not None:
            previous_date[key] = current
    return profiles


def build_matchup_profiles(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matchups: list[dict[str, Any]] = []
    for row in rows:
        home_score = _number(row.get("home_score"))
        away_score = _number(row.get("away_score"))
        if home_score is None or away_score is None:
            continue
        matchups.append(
            {
                "event_id": row.get("event_id"),
                "season": str(row.get("season") or ""),
                "event_date": row.get("event_date"),
                "week_or_round": row.get("week_or_round"),
                "game_type": row.get("game_type"),
                "home_team": row.get("home_participant"),
                "away_team": row.get("away_participant"),
                "home_score": _compact_number(home_score),
                "away_score": _compact_number(away_score),
                "home_margin": _compact_number(home_score - away_score),
                "total_score": _compact_number(home_score + away_score),
                "source_data_kind": "real_open_data",
                "raw_payload_included": False,
            }
        )
    return matchups


def _win_rate(record: dict[str, int]) -> float | None:
    games = int(record.get("games", 0) or 0)
    if games <= 0:
        return None
    return round((record.get("wins", 0) + 0.5 * record.get("ties", 0)) / games, 4)


def build_team_season_profiles(team_games: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for game in team_games:
        grouped[(str(game.get("season") or ""), str(game.get("team") or ""))].append(game)
    profiles: list[dict[str, Any]] = []
    for (season, team), games in sorted(grouped.items(), key=lambda item: (_season_key(item[0][0]), item[0][1])):
        games = sorted(games, key=lambda item: (str(item.get("event_date")), str(item.get("week_or_round") or "")))
        record = _record()
        home_record = _record()
        away_record = _record()
        close_record = _record()
        points_for_values: list[float] = []
        points_against_values: list[float] = []
        margins: list[float] = []
        blowout_wins = 0
        blowout_losses = 0
        game_types = [str(game.get("game_type") or "").strip() for game in games]
        all_game_types_available = all(game_type for game_type in game_types)
        for game in games:
            pf = _number(game.get("points_for"))
            pa = _number(game.get("points_against"))
            margin = _number(game.get("point_differential"))
            if pf is None or pa is None or margin is None:
                continue
            result = str(game.get("result") or _result_from_margin(margin))
            _add_record(record, result)
            _add_record(home_record if game.get("home_away") == "home" else away_record, result)
            if abs(margin) <= CLOSE_GAME_MARGIN:
                _add_record(close_record, result)
            if margin >= BLOWOUT_MARGIN:
                blowout_wins += 1
            if margin <= -BLOWOUT_MARGIN:
                blowout_losses += 1
            points_for_values.append(pf)
            points_against_values.append(pa)
            margins.append(margin)
        games_played = len(points_for_values)
        late_games = games[-LATE_SEASON_GAME_COUNT:]
        late_record = _record()
        late_margin = 0.0
        for game in late_games:
            margin = _number(game.get("point_differential"))
            if margin is None:
                continue
            late_margin += margin
            _add_record(late_record, str(game.get("result") or _result_from_margin(margin)))
        playoff_game_count = None
        postseason_flag = None
        super_bowl_flag = None
        blockers: list[str] = []
        if all_game_types_available:
            playoff_game_count = sum(1 for game_type in game_types if game_type != "REG")
            postseason_flag = playoff_game_count > 0
            super_bowl_flag = any(game_type == "SB" for game_type in game_types)
        else:
            blockers.extend(["playoff_round_labels_missing", "super_bowl_label_missing"])
        profile = {
            "season": season,
            "team": team,
            "games_played": games_played,
            "wins": record["wins"],
            "losses": record["losses"],
            "ties": record["ties"],
            "win_rate": _win_rate(record),
            "points_for": _compact_number(sum(points_for_values)),
            "points_against": _compact_number(sum(points_against_values)),
            "point_differential": _compact_number(sum(margins)),
            "average_points_for": _compact_number(sum(points_for_values) / games_played if games_played else None),
            "average_points_against": _compact_number(sum(points_against_values) / games_played if games_played else None),
            "average_margin": _compact_number(sum(margins) / games_played if games_played else None),
            "home_record": {**home_record, "win_rate": _win_rate(home_record)},
            "away_record": {**away_record, "win_rate": _win_rate(away_record)},
            "close_game_record": {**close_record, "win_rate": _win_rate(close_record)},
            "close_game_win_rate": _win_rate(close_record),
            "blowout_wins": blowout_wins,
            "blowout_losses": blowout_losses,
            "blowout_rate": _compact_number((blowout_wins + blowout_losses) / games_played if games_played else None),
            "scoring_volatility": _compact_number(statistics.pstdev(points_for_values) if len(points_for_values) > 1 else 0.0 if points_for_values else None),
            "defensive_volatility": _compact_number(statistics.pstdev(points_against_values) if len(points_against_values) > 1 else 0.0 if points_against_values else None),
            "late_season_form": {
                **late_record,
                "games_used": late_record["games"],
                "point_differential": _compact_number(late_margin),
                "win_rate": _win_rate(late_record),
            },
            "late_season_win_rate": _win_rate(late_record),
            "simple_team_rating": _compact_number(sum(margins) / games_played if games_played else None),
            "schedule_strength_proxy": None,
            "playoff_game_count": playoff_game_count,
            "postseason_flag": postseason_flag,
            "super_bowl_flag": super_bowl_flag,
            "game_type_labels_available": bool(all_game_types_available),
            "game_types_seen": sorted({game_type for game_type in game_types if game_type}),
            "blocked_reasons": blockers,
            "source_data_kind": "real_open_data",
            "raw_payload_included": False,
        }
        profiles.append(profile)
    by_team_season = {(profile["season"], profile["team"]): profile for profile in profiles}
    opponent_rates: dict[tuple[str, str], list[float]] = defaultdict(list)
    for game in team_games:
        key = (str(game.get("season") or ""), str(game.get("team") or ""))
        opponent = by_team_season.get((str(game.get("season") or ""), str(game.get("opponent") or "")))
        rate = _number(opponent.get("win_rate")) if opponent else None
        if rate is not None:
            opponent_rates[key].append(rate)
    for profile in profiles:
        rates = opponent_rates.get((profile["season"], profile["team"]), [])
        profile["schedule_strength_proxy"] = _compact_number(sum(rates) / len(rates) if rates else None)
    return profiles


def _season_key(value: Any) -> int:
    try:
        return int(str(value))
    except ValueError:
        return -1


def build_pattern_candidate_profiles(team_season_profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for profile in team_season_profiles:
        candidates.append(
            {
                "season": profile.get("season"),
                "team": profile.get("team"),
                "games_played": profile.get("games_played"),
                "win_rate": profile.get("win_rate"),
                "average_points_for": profile.get("average_points_for"),
                "average_points_against": profile.get("average_points_against"),
                "average_margin": profile.get("average_margin"),
                "scoring_volatility": profile.get("scoring_volatility"),
                "defensive_volatility": profile.get("defensive_volatility"),
                "late_season_win_rate": profile.get("late_season_win_rate"),
                "simple_team_rating": profile.get("simple_team_rating"),
                "schedule_strength_proxy": profile.get("schedule_strength_proxy"),
                "postseason_flag": profile.get("postseason_flag"),
                "super_bowl_flag": profile.get("super_bowl_flag"),
                "blocked_reasons": profile.get("blocked_reasons") or [],
                "source_data_kind": "real_open_data",
                "raw_payload_included": False,
            }
        )
    return candidates


def build_similarity_feature_catalog(team_season_profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    available = {feature for feature in SIMILARITY_NUMERIC_FEATURES if any(_number(profile.get(feature)) is not None for profile in team_season_profiles)}
    grouped = [
        ("scoring profile", ["points_for", "average_points_for"]),
        ("defensive profile", ["points_against", "average_points_against"]),
        ("margin profile", ["point_differential", "average_margin", "simple_team_rating"]),
        ("volatility profile", ["scoring_volatility", "defensive_volatility"]),
        ("home/away profile", ["win_rate", "close_game_win_rate"]),
        ("late-season form", ["late_season_win_rate"]),
        ("opponent strength proxy", ["schedule_strength_proxy"]),
        ("postseason profile", ["playoff_game_count", "postseason_flag", "super_bowl_flag"]),
    ]
    catalog: list[dict[str, Any]] = []
    for group, features in grouped:
        for feature in features:
            status = "available" if feature in available or feature in {"playoff_game_count", "postseason_flag", "super_bowl_flag"} and any(profile.get(feature) is not None for profile in team_season_profiles) else "blocked"
            catalog.append(
                {
                    "group": group,
                    "feature_name": feature,
                    "status": status,
                    "blocked_reason": None if status == "available" else "requires_available_real_nfl_history",
                }
            )
    blocked_future = [
        ("market profile", "market_price_or_odds", "requires_odds_or_market_source"),
        ("roster continuity", "roster_continuity", "requires_additional_source"),
        ("injury/lineup profile", "injury_lineup_profile", "requires_additional_source"),
        ("pace/advanced efficiency", "pace_or_advanced_efficiency", "requires_additional_source"),
    ]
    for group, feature, reason in blocked_future:
        catalog.append({"group": group, "feature_name": feature, "status": "blocked", "blocked_reason": reason})
    return catalog


def compute_team_profile_similarity(profile_a: dict[str, Any], profile_b: dict[str, Any]) -> dict[str, Any]:
    features_compared: list[str] = []
    features_missing: list[str] = []
    similarities: list[float] = []
    for feature in SIMILARITY_NUMERIC_FEATURES:
        a = _number(profile_a.get(feature))
        b = _number(profile_b.get(feature))
        if a is None or b is None or not (math.isfinite(a) and math.isfinite(b)):
            features_missing.append(feature)
            continue
        denom = max(abs(a), abs(b), 1.0)
        similarities.append(max(0.0, 1.0 - (abs(a - b) / denom)))
        features_compared.append(feature)
    if len(features_compared) < MIN_SIMILARITY_FEATURES:
        return {
            "similarity_score": None,
            "features_compared": features_compared,
            "features_missing": features_missing,
            "confidence": "insufficient",
            "blocked_reason": "insufficient_data",
            "predictive_claim_made": False,
            "provider_write": False,
            "execution_allowed": False,
        }
    return {
        "similarity_score": round(sum(similarities) / len(similarities), 4),
        "features_compared": features_compared,
        "features_missing": features_missing,
        "confidence": "medium" if len(features_compared) >= 8 else "low",
        "blocked_reason": None,
        "predictive_claim_made": False,
        "provider_write": False,
        "execution_allowed": False,
    }


def build_nfl_historical_pattern_lab_report(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    base = resolve_base_data_dir(base_data_dir)
    rows, synthetic_ignored = load_real_nfl_rows(base_data_dir=base)
    team_games = build_team_game_profiles(rows)
    matchups = build_matchup_profiles(rows)
    team_seasons = build_team_season_profiles(team_games)
    candidates = build_pattern_candidate_profiles(team_seasons)
    catalog = build_similarity_feature_catalog(team_seasons)
    available_features = sorted({row["feature_name"] for row in catalog if row["status"] == "available"})
    blocked_features = sorted({row["feature_name"] for row in catalog if row["status"] == "blocked"})
    label_profiles = [profile for profile in team_seasons if profile.get("game_type_labels_available")]
    label_status = "available" if team_seasons and len(label_profiles) == len(team_seasons) else "partial" if label_profiles else "blocked"
    label_blockers = []
    if label_status != "available":
        label_blockers = ["playoff_round_labels_missing", "super_bowl_label_missing"]
    seasons = sorted({str(profile.get("season")) for profile in team_seasons}, key=_season_key)
    teams = sorted({str(profile.get("team")) for profile in team_seasons})
    example_similarity = None
    if len(team_seasons) >= 2:
        example_similarity = compute_team_profile_similarity(team_seasons[0], team_seasons[1])
    readiness_status = (
        "profile_scaffold_ready_no_predictive_validation"
        if team_seasons and len(available_features) >= MIN_SIMILARITY_FEATURES
        else "blocked_insufficient_real_history"
    )
    return {
        **SAFETY_FIELDS,
        "ok": True,
        "status": "ok",
        "schema_version": NFL_PATTERN_LAB_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "run_id": sanitize_filename(f"nfl_pattern_lab_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
        "runtime_data_dir": str(base),
        "report_root": str(base / "data_sources" / "open_sports_history" / "nfl_pattern_lab"),
        "reports_consumed": [relative for relative, path in _validated_paths(base) if path.exists()],
        "seasons_analyzed": seasons,
        "teams_profiled": teams,
        "real_rows_consumed": len(rows),
        "synthetic_rows_ignored": synthetic_ignored,
        "team_season_profiles_created": len(team_seasons),
        "team_game_profiles_created": len(team_games),
        "matchup_profiles_created": len(matchups),
        "pattern_candidate_profiles_created": len(candidates),
        "team_season_profiles": team_seasons,
        "team_game_profiles": team_games,
        "matchup_profiles": matchups,
        "pattern_candidate_profiles": candidates,
        "similarity_feature_catalog": catalog,
        "similarity_features_available": available_features,
        "similarity_features_blocked": blocked_features,
        "example_similarity": example_similarity,
        "playoff_super_bowl_labels_available": label_status,
        "label_blockers": label_blockers,
        "backtest_readiness_status": readiness_status,
        "predictive_claim_made": False,
        "betting_decision_made": False,
        "outcome_store_written": False,
        "paper_ledger_written": False,
        "kalshi_calibration_mutated": False,
        "provider_calls_attempted": 0,
        "provider_calls_succeeded": 0,
        "provider_calls_failed": 0,
        "downloads_attempted": 0,
        "downloads_succeeded": 0,
        "outcome_persistence_attempted": False,
        "import_or_persist_endpoint_called": False,
        "persisted_outcomes": False,
        "recommended_next_step": "add deterministic validation labels from approved open postseason/roster/market sources before predictive claims",
        "storage_health": get_storage_health(),
    }


def render_nfl_pattern_lab_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# NFL Historical Pattern Lab",
        "",
        f"1. seasons_analyzed: {', '.join(report.get('seasons_analyzed') or []) if report.get('seasons_analyzed') else 'none'}",
        f"2. teams_profiled: {len(report.get('teams_profiled') or [])}",
        f"3. team_season_profiles_created: {report.get('team_season_profiles_created')}",
        f"4. similarity_features_available: {', '.join(report.get('similarity_features_available') or []) if report.get('similarity_features_available') else 'none'}",
        f"5. similarity_features_blocked: {', '.join(report.get('similarity_features_blocked') or []) if report.get('similarity_features_blocked') else 'none'}",
        f"6. playoff_super_bowl_labels_available: {report.get('playoff_super_bowl_labels_available')}",
        f"7. backtest_readiness_status: {report.get('backtest_readiness_status')}",
        "8. raw_payload_included=false",
        "9. secrets_included=false",
        "10. provider_write=false",
        "11. execution_allowed=false",
        f"12. recommended_next_step: {report.get('recommended_next_step')}",
        "",
    ]
    return "\n".join(lines)


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def write_nfl_historical_pattern_lab_report(
    report: dict[str, Any],
    *,
    base_data_dir: str | Path | None = None,
) -> dict[str, str]:
    root = _root(base_data_dir)
    run_id = sanitize_filename(str(report.get("run_id") or f"nfl_pattern_lab_{uuid4().hex[:8]}"))
    latest_json = root / "latest.json"
    latest_md = root / "latest.md"
    item_json = root / "items" / f"{run_id}.json"
    item_md = root / "items" / f"{run_id}.md"
    paths = {
        "latest_json_path": _rel(latest_json, base_data_dir),
        "latest_markdown_path": _rel(latest_md, base_data_dir),
        "item_json_path": _rel(item_json, base_data_dir),
        "item_markdown_path": _rel(item_md, base_data_dir),
    }
    payload = {**SAFETY_FIELDS, **report, **paths, "raw_payload_included": False, "secrets_included": False}
    markdown = render_nfl_pattern_lab_markdown(payload)
    _atomic_write_json(latest_json, payload)
    _atomic_write_text(latest_md, markdown)
    _atomic_write_json(item_json, payload)
    _atomic_write_text(item_md, markdown)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    report = build_nfl_historical_pattern_lab_report()
    paths: dict[str, str] = {}
    if args.persist:
        paths = write_nfl_historical_pattern_lab_report(report)
        report.update(paths)
    print(
        json.dumps(
            {
                "ok": report["ok"],
                "status": report["status"],
                "seasons_analyzed": report["seasons_analyzed"],
                "teams_profiled": len(report["teams_profiled"]),
                "team_season_profiles_created": report["team_season_profiles_created"],
                "team_game_profiles_created": report["team_game_profiles_created"],
                "matchup_profiles_created": report["matchup_profiles_created"],
                "similarity_features_available": report["similarity_features_available"],
                "similarity_features_blocked": report["similarity_features_blocked"],
                "playoff_super_bowl_labels_available": report["playoff_super_bowl_labels_available"],
                "backtest_readiness_status": report["backtest_readiness_status"],
                "provider_calls_attempted": 0,
                "downloads_attempted": 0,
                "downloads_succeeded": 0,
                "enabled_source_count": 0,
                "paid_source_enabled_count": 0,
                "provider_write": False,
                "execution_allowed": False,
                "raw_payload_included": False,
                "secrets_included": False,
                "latest_json_path": paths.get("latest_json_path"),
                "latest_markdown_path": paths.get("latest_markdown_path"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

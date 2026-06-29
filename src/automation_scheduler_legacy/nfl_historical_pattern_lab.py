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

from src.data.data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from .nfl_coaching_feature_builders import coaching_readiness_flags
from .nfl_cutoff_week_features import cutoff_feature_availability_summary
from .nfl_open_data_feature_builders import (
    build_expanded_feature_readiness,
    build_nfl_feature_builder_report,
)
from .nfl_open_data_source_exhaustion import build_nfl_source_exhaustion_report
from .open_sports_history_sources import SAFETY_FIELDS
from src.services.scheduler_config import sanitize_filename, utc_now_iso


NFL_PATTERN_LAB_SCHEMA_VERSION = "nfl_historical_pattern_lab_v2"
NFL_MODULE = "americanfootball_nfl"
NFL_SOURCE_ID = "nflverse_nfl"
CLOSE_GAME_MARGIN = 7
BLOWOUT_MARGIN = 21
LATE_SEASON_GAME_COUNT = 5
MIN_SIMILARITY_FEATURES = 3
MINIMUM_COMPS_REQUIRED = 30
HOLDOUT_K_VALUES = [5, 10, 20]
MINIMUM_HOLDOUT_ANCHORS = 30

GAME_TYPE_ROUND_LABELS = {
    "REG": "regular_season",
    "WC": "wild_card",
    "DIV": "divisional",
    "CON": "conference_championship",
    "SB": "super_bowl",
}
POSTSEASON_GAME_TYPES = {"WC", "DIV", "CON", "SB"}
SUPER_BOWL_GAME_TYPES = {"SB"}
LABEL_BLOCKERS = [
    "playoff_round_labels_missing",
    "super_bowl_label_missing",
    "compact_game_type_missing",
    "source_field_missing",
    "insufficient_label_fields",
]

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

HOLDOUT_ALLOWED_SIMILARITY_FEATURES = [
    "win_rate",
    "average_points_for",
    "average_points_against",
    "average_margin",
    "point_differential",
    "close_game_win_rate",
    "scoring_volatility",
    "defensive_volatility",
    "late_season_win_rate",
    "schedule_strength_proxy",
    "simple_team_rating",
    "home_win_rate",
    "away_win_rate",
    "average_rest_days",
]

HOLDOUT_BLOCKED_LEAKAGE_FEATURES = [
    "postseason_flag",
    "playoff_game_count",
    "super_bowl_flag",
    "postseason_games",
    "postseason_wins",
    "postseason_losses",
    "reached_playoffs",
    "reached_conference_championship",
    "reached_super_bowl",
    "won_super_bowl",
    "market_price_or_odds",
    "injury_lineup_profile",
    "roster_continuity",
    "pace_or_advanced_efficiency",
    "injury_availability",
    "depth_chart_stability",
    "player_usage_snaps",
    "player_usage_participation",
    "nextgen_efficiency_candidates",
    "market_odds",
]

POSTSEASON_TARGET_LABEL_FIELDS = [
    "made_playoffs",
    "won_playoff_game",
    "reached_conference_championship",
    "reached_super_bowl",
    "won_super_bowl",
]

HOLDOUT_VALIDATION_STATUSES = {
    "insufficient_labels",
    "insufficient_features",
    "insufficient_samples",
    "validation_scaffold_ready_no_predictive_claim",
    "holdout_backtest_ready_no_predictive_claim",
    "historical_signal_candidate_no_predictive_claim",
    "blocked_leakage_detected",
}


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
    ignored_seen: set[tuple[str, str, str]] = set()
    rows: list[dict[str, Any]] = []
    synthetic_ignored = 0
    for _, path in _validated_paths(base):
        payload = _read_json(path)
        for item in _items(payload):
            if not _is_real_nfl_row(item):
                if item.get("module") == NFL_MODULE and item.get("source_id") == NFL_SOURCE_ID:
                    ignored_id = str(item.get("event_id") or item.get("source_record_hash") or "")
                    if not ignored_id:
                        primitive_item = {
                            key: item.get(key)
                            for key in sorted(item)
                            if isinstance(item.get(key), (str, int, float, bool)) or item.get(key) is None
                        }
                        ignored_id = json.dumps(primitive_item, sort_keys=True, separators=(",", ":"))
                    ignored_key = (str(item.get("module") or ""), str(item.get("source_id") or ""), ignored_id)
                    if ignored_key not in ignored_seen:
                        synthetic_ignored += 1
                        ignored_seen.add(ignored_key)
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


def _clean_game_type(value: Any) -> str | None:
    text = str(value or "").strip().upper()
    return text if text in GAME_TYPE_ROUND_LABELS else None


def _explicit_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return None


def derive_nfl_game_labels(row: dict[str, Any]) -> dict[str, Any]:
    game_type = _clean_game_type(row.get("game_type") or row.get("season_type") or row.get("playoff_round"))
    blockers: list[str] = []
    if game_type:
        postseason_flag = game_type in POSTSEASON_GAME_TYPES
        super_bowl_flag = game_type in SUPER_BOWL_GAME_TYPES
        return {
            "game_type": game_type,
            "playoff_round_label": GAME_TYPE_ROUND_LABELS[game_type],
            "postseason_flag": postseason_flag,
            "super_bowl_flag": super_bowl_flag,
            "label_confidence": "source_supported",
            "label_blockers": [],
            "playoff_round_label_method": "explicit_game_type",
            "super_bowl_label_method": "explicit_game_type",
        }

    explicit_postseason = None
    for key in ("postseason_flag", "playoff_flag", "is_postseason", "is_playoff"):
        explicit_postseason = _explicit_bool(row.get(key))
        if explicit_postseason is not None:
            break
    explicit_super_bowl = None
    for key in ("super_bowl_flag", "is_super_bowl"):
        explicit_super_bowl = _explicit_bool(row.get(key))
        if explicit_super_bowl is not None:
            break

    blockers.extend(["compact_game_type_missing", "playoff_round_labels_missing"])
    if explicit_super_bowl is None:
        blockers.append("super_bowl_label_missing")
    if explicit_postseason is None and explicit_super_bowl is None:
        blockers.append("source_field_missing")
    return {
        "game_type": None,
        "playoff_round_label": None,
        "postseason_flag": explicit_postseason,
        "super_bowl_flag": explicit_super_bowl,
        "label_confidence": "partial_source_supported" if explicit_postseason is not None or explicit_super_bowl is not None else "blocked",
        "label_blockers": sorted({blocker for blocker in blockers if blocker in LABEL_BLOCKERS}),
        "playoff_round_label_method": "unavailable",
        "super_bowl_label_method": "explicit_super_bowl_flag" if explicit_super_bowl is not None else "unavailable",
    }


def _winner_from_scores(home_team: Any, away_team: Any, home_score: float, away_score: float) -> str | None:
    if home_score > away_score:
        return str(home_team or "") or None
    if away_score > home_score:
        return str(away_team or "") or None
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
        labels = derive_nfl_game_labels(row)
        home_margin = home_score - away_score
        away_margin = away_score - home_score
        base = {
            "event_id": row.get("event_id"),
            "season": season,
            "event_date": event_date,
            "week_or_round": row.get("week_or_round"),
            "game_type": labels["game_type"],
            "playoff_round_label": labels["playoff_round_label"],
            "postseason_flag": labels["postseason_flag"],
            "super_bowl_flag": labels["super_bowl_flag"],
            "label_confidence": labels["label_confidence"],
            "label_blockers": labels["label_blockers"],
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
        labels = derive_nfl_game_labels(row)
        final_margin = _number(row.get("final_margin"))
        total_points = _number(row.get("total_score"))
        home_team = row.get("home_participant")
        away_team = row.get("away_participant")
        matchups.append(
            {
                "event_id": row.get("event_id"),
                "game_id": row.get("event_id"),
                "season": str(row.get("season") or ""),
                "event_date": row.get("event_date"),
                "game_date": row.get("event_date"),
                "week_or_round": row.get("week_or_round"),
                "game_type": labels["game_type"],
                "playoff_round_label": labels["playoff_round_label"],
                "postseason_flag": labels["postseason_flag"],
                "super_bowl_flag": labels["super_bowl_flag"],
                "label_confidence": labels["label_confidence"],
                "label_blockers": labels["label_blockers"],
                "home_team": home_team,
                "away_team": away_team,
                "home_score": _compact_number(home_score),
                "away_score": _compact_number(away_score),
                "winner": row.get("winner") or _winner_from_scores(home_team, away_team, home_score, away_score),
                "final_margin": _compact_number(final_margin if final_margin is not None else home_score - away_score),
                "total_points": _compact_number(total_points if total_points is not None else home_score + away_score),
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
        label_blockers = sorted(
            {
                blocker
                for game in games
                for blocker in (game.get("label_blockers") or [])
                if blocker in LABEL_BLOCKERS
            }
        )
        supported_label_games = [game for game in games if game.get("postseason_flag") is not None or game.get("super_bowl_flag") is not None]
        all_game_labels_supported = len(supported_label_games) == len(games) and not label_blockers
        labeled_postseason_games = [game for game in supported_label_games if game.get("postseason_flag") is True]
        labeled_conference_championship_games = [
            game for game in supported_label_games if game.get("playoff_round_label") == "conference_championship"
        ]
        labeled_super_bowl_games = [game for game in supported_label_games if game.get("super_bowl_flag") is True]
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
        postseason_games = None
        postseason_wins = None
        postseason_losses = None
        reached_playoffs = None
        reached_conference_championship = None
        reached_super_bowl = None
        won_super_bowl = None
        if supported_label_games:
            postseason_games = len(labeled_postseason_games)
            postseason_wins = sum(1 for game in labeled_postseason_games if game.get("result") == "win")
            postseason_losses = sum(1 for game in labeled_postseason_games if game.get("result") == "loss")
            reached_playoffs = True if labeled_postseason_games else False if all_game_labels_supported else None
            reached_conference_championship = (
                True if labeled_conference_championship_games else False if all_game_labels_supported else None
            )
            reached_super_bowl = True if labeled_super_bowl_games else False if all_game_labels_supported else None
            won_super_bowl = (
                True
                if any(game.get("result") == "win" for game in labeled_super_bowl_games)
                else False
                if reached_super_bowl is True or all_game_labels_supported
                else None
            )
        label_confidence = (
            "source_supported"
            if all_game_labels_supported
            else "partial_source_supported"
            if supported_label_games
            else "blocked"
        )
        if label_confidence != "source_supported" and "insufficient_label_fields" not in label_blockers:
            label_blockers.append("insufficient_label_fields")
        label_blockers = sorted({blocker for blocker in label_blockers if blocker in LABEL_BLOCKERS})
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
            "postseason_games": postseason_games,
            "postseason_wins": postseason_wins,
            "postseason_losses": postseason_losses,
            "reached_playoffs": reached_playoffs,
            "reached_conference_championship": reached_conference_championship,
            "reached_super_bowl": reached_super_bowl,
            "won_super_bowl": won_super_bowl,
            "label_confidence": label_confidence,
            "label_blockers": label_blockers,
            "playoff_game_count": postseason_games,
            "postseason_flag": reached_playoffs,
            "super_bowl_flag": reached_super_bowl,
            "game_type_labels_available": label_confidence == "source_supported",
            "game_types_seen": sorted({game_type for game_type in game_types if game_type}),
            "blocked_reasons": label_blockers,
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
                "postseason_games": profile.get("postseason_games"),
                "postseason_wins": profile.get("postseason_wins"),
                "postseason_losses": profile.get("postseason_losses"),
                "reached_playoffs": profile.get("reached_playoffs"),
                "reached_conference_championship": profile.get("reached_conference_championship"),
                "reached_super_bowl": profile.get("reached_super_bowl"),
                "won_super_bowl": profile.get("won_super_bowl"),
                "label_confidence": profile.get("label_confidence"),
                "label_blockers": profile.get("label_blockers") or [],
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


def _profile_numeric_features(profile: dict[str, Any]) -> list[str]:
    return [
        feature
        for feature in SIMILARITY_NUMERIC_FEATURES
        if (value := _number(profile.get(feature))) is not None and math.isfinite(value)
    ]


def _outcome_label_available(profile: dict[str, Any]) -> bool:
    return any(
        profile.get(field) is not None
        for field in (
            "postseason_games",
            "postseason_wins",
            "postseason_losses",
            "reached_playoffs",
            "reached_conference_championship",
            "reached_super_bowl",
            "won_super_bowl",
        )
    )


def _label_overlap_available(profile_a: dict[str, Any], profile_b: dict[str, Any]) -> bool:
    return _outcome_label_available(profile_a) and _outcome_label_available(profile_b)


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
            "no_predictive_claim": True,
            "label_overlap_available": _label_overlap_available(profile_a, profile_b),
            "outcome_label_available": _outcome_label_available(profile_a) and _outcome_label_available(profile_b),
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
        "no_predictive_claim": True,
        "label_overlap_available": _label_overlap_available(profile_a, profile_b),
        "outcome_label_available": _outcome_label_available(profile_a) and _outcome_label_available(profile_b),
        "provider_write": False,
        "execution_allowed": False,
    }


def build_historical_team_profiles(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return build_team_season_profiles(build_team_game_profiles(rows))


def find_historical_team_comps(
    team_season_profiles: list[dict[str, Any]],
    *,
    anchor_team: str,
    anchor_season: str | int,
    limit: int = 5,
) -> list[dict[str, Any]]:
    anchor = next(
        (
            profile
            for profile in team_season_profiles
            if str(profile.get("team")) == str(anchor_team) and str(profile.get("season")) == str(anchor_season)
        ),
        None,
    )
    if anchor is None:
        return []
    comps: list[dict[str, Any]] = []
    for profile in team_season_profiles:
        if str(profile.get("team")) == str(anchor_team) and str(profile.get("season")) == str(anchor_season):
            continue
        similarity = compute_team_profile_similarity(anchor, profile)
        comps.append(
            {
                "anchor_team": anchor.get("team"),
                "anchor_season": anchor.get("season"),
                "comp_team": profile.get("team"),
                "comp_season": profile.get("season"),
                "similarity_score": similarity.get("similarity_score"),
                "features_compared": similarity.get("features_compared") or [],
                "features_missing": similarity.get("features_missing") or [],
                "label_overlap_available": similarity.get("label_overlap_available"),
                "outcome_label_available": similarity.get("outcome_label_available"),
                "confidence": similarity.get("confidence"),
                "blocked_reason": similarity.get("blocked_reason"),
                "no_predictive_claim": True,
                "predictive_claim_made": False,
                "provider_write": False,
                "execution_allowed": False,
            }
        )
    comps.sort(
        key=lambda item: (
            item.get("similarity_score") is None,
            0.0 if item.get("similarity_score") is None else -float(item.get("similarity_score")),
            str(item.get("comp_season")),
            str(item.get("comp_team")),
        )
    )
    return comps[: max(0, int(limit))]


def _label_coverage_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    playoff_coverage_count = 0
    super_bowl_coverage_count = 0
    blockers: set[str] = set()
    playoff_methods: Counter[str] = Counter()
    super_bowl_methods: Counter[str] = Counter()
    by_season: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "rows": 0,
            "playoff_label_coverage_count": 0,
            "playoff_label_missing_count": 0,
            "super_bowl_label_coverage_count": 0,
            "super_bowl_label_missing_count": 0,
            "game_type_present_count": 0,
            "game_type_missing_count": 0,
            "label_blockers": set(),
        }
    )
    for row in rows:
        labels = derive_nfl_game_labels(row)
        season = str(row.get("season") or "unknown")
        season_item = by_season[season]
        season_item["rows"] += 1
        if labels.get("game_type") is not None:
            season_item["game_type_present_count"] += 1
        else:
            season_item["game_type_missing_count"] += 1
        if labels.get("playoff_round_label") is not None:
            playoff_coverage_count += 1
            season_item["playoff_label_coverage_count"] += 1
            playoff_methods[str(labels.get("playoff_round_label_method") or "unknown")] += 1
        else:
            season_item["playoff_label_missing_count"] += 1
            season_item["label_blockers"].update(labels.get("label_blockers") or [])
            blockers.update(labels.get("label_blockers") or [])
        if labels.get("super_bowl_flag") is not None:
            super_bowl_coverage_count += 1
            season_item["super_bowl_label_coverage_count"] += 1
            super_bowl_methods[str(labels.get("super_bowl_label_method") or "unknown")] += 1
        else:
            season_item["super_bowl_label_missing_count"] += 1
            season_item["label_blockers"].update(labels.get("label_blockers") or [])
            blockers.update(labels.get("label_blockers") or [])
    total = len(rows)
    playoff_missing_count = max(0, total - playoff_coverage_count)
    super_bowl_missing_count = max(0, total - super_bowl_coverage_count)
    status = "available" if total and playoff_missing_count == 0 and super_bowl_missing_count == 0 else "partial" if playoff_coverage_count or super_bowl_coverage_count else "blocked"
    if playoff_missing_count:
        blockers.add("playoff_round_labels_missing")
    if super_bowl_missing_count:
        blockers.add("super_bowl_label_missing")
    if playoff_missing_count or super_bowl_missing_count:
        blockers.add("insufficient_label_fields")
    label_coverage_by_season: dict[str, dict[str, Any]] = {}
    label_blockers_by_season: dict[str, list[str]] = {}
    for season, item in sorted(by_season.items(), key=lambda pair: _season_key(pair[0])):
        season_blockers = sorted({blocker for blocker in item["label_blockers"] if blocker in LABEL_BLOCKERS})
        if item["playoff_label_missing_count"] or item["super_bowl_label_missing_count"]:
            season_blockers = sorted(set(season_blockers) | {"insufficient_label_fields"})
        label_coverage_by_season[season] = {
            "rows": item["rows"],
            "game_type_present_count": item["game_type_present_count"],
            "game_type_missing_count": item["game_type_missing_count"],
            "playoff_label_coverage_count": item["playoff_label_coverage_count"],
            "playoff_label_missing_count": item["playoff_label_missing_count"],
            "super_bowl_label_coverage_count": item["super_bowl_label_coverage_count"],
            "super_bowl_label_missing_count": item["super_bowl_label_missing_count"],
        }
        label_blockers_by_season[season] = season_blockers
    return {
        "postseason_label_status": status,
        "playoff_label_coverage_count": playoff_coverage_count,
        "playoff_label_missing_count": playoff_missing_count,
        "super_bowl_label_coverage_count": super_bowl_coverage_count,
        "super_bowl_label_missing_count": super_bowl_missing_count,
        "playoff_round_label_method": "explicit_game_type" if playoff_methods else "unavailable",
        "super_bowl_label_method": "explicit_game_type" if super_bowl_methods else "unavailable",
        "label_blockers": sorted({blocker for blocker in blockers if blocker in LABEL_BLOCKERS}),
        "label_coverage_by_season": label_coverage_by_season,
        "label_blockers_by_season": label_blockers_by_season,
    }


def build_pattern_validation_scorecard(
    team_season_profiles: list[dict[str, Any]],
    similarity_feature_catalog: list[dict[str, Any]],
) -> dict[str, Any]:
    features_available = sorted({row["feature_name"] for row in similarity_feature_catalog if row.get("status") == "available"})
    features_blocked = sorted({row["feature_name"] for row in similarity_feature_catalog if row.get("status") == "blocked"})
    label_blockers = sorted(
        {
            blocker
            for profile in team_season_profiles
            for blocker in (profile.get("label_blockers") or profile.get("blocked_reasons") or [])
            if blocker in LABEL_BLOCKERS
        }
    )
    target_labels_available = [
        field
        for field in (
            "postseason_games",
            "postseason_wins",
            "postseason_losses",
            "reached_playoffs",
            "reached_conference_championship",
            "reached_super_bowl",
            "won_super_bowl",
        )
        if any(profile.get(field) is not None for profile in team_season_profiles)
    ]
    comparable_profile_count = sum(
        1 for profile in team_season_profiles if len(_profile_numeric_features(profile)) >= MIN_SIMILARITY_FEATURES
    )
    backtest_blockers: list[str] = []
    if len(features_available) < MIN_SIMILARITY_FEATURES:
        backtest_blockers.append("insufficient_features")
    if not target_labels_available:
        backtest_blockers.append("insufficient_labels")
    backtest_blockers.extend(label_blockers)
    if comparable_profile_count < MINIMUM_COMPS_REQUIRED:
        backtest_blockers.append("insufficient_comparable_profiles")
    backtest_blockers = sorted(set(backtest_blockers))
    if len(features_available) < MIN_SIMILARITY_FEATURES:
        validation_status = "insufficient_features"
    elif not target_labels_available:
        validation_status = "insufficient_labels"
    elif backtest_blockers:
        validation_status = "scaffold_ready_no_predictive_claim"
    else:
        validation_status = "backtest_ready_no_predictive_claim"
    return {
        "seasons_analyzed": sorted({str(profile.get("season")) for profile in team_season_profiles}, key=_season_key),
        "teams_analyzed": len({str(profile.get("team")) for profile in team_season_profiles}),
        "features_available": features_available,
        "features_blocked": features_blocked,
        "target_labels_available": target_labels_available,
        "target_labels_blocked": label_blockers,
        "comparable_profile_count": comparable_profile_count,
        "minimum_comps_required": MINIMUM_COMPS_REQUIRED,
        "backtest_ready": validation_status == "backtest_ready_no_predictive_claim",
        "backtest_blockers": backtest_blockers,
        "validation_status": validation_status,
        "no_predictive_claim": True,
        "predictive_claim_made": False,
        "provider_write": False,
        "execution_allowed": False,
    }


def _team_season_key_for_item(item: dict[str, Any]) -> tuple[str, str]:
    return str(item.get("season") or ""), str(item.get("team") or "")


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def _compact_rate(value: float | None) -> float | None:
    return None if value is None else round(float(value), 4)


def build_regular_season_snapshot_profiles(team_games: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for game in team_games:
        if str(game.get("source_data_kind") or "") != "real_open_data":
            continue
        if str(game.get("game_type") or "").upper() != "REG":
            continue
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
        rest_days_values: list[float] = []
        blowout_wins = 0
        blowout_losses = 0
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
            rest_days = _number(game.get("rest_days"))
            if rest_days is not None:
                rest_days_values.append(rest_days)
            points_for_values.append(pf)
            points_against_values.append(pa)
            margins.append(margin)
        games_played = len(points_for_values)
        late_games = games[-LATE_SEASON_GAME_COUNT:]
        late_record = _record()
        for game in late_games:
            margin = _number(game.get("point_differential"))
            if margin is not None:
                _add_record(late_record, str(game.get("result") or _result_from_margin(margin)))
        profile = {
            "season": season,
            "team": team,
            "games_played": games_played,
            "regular_season_games": games_played,
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
            "close_game_win_rate": _win_rate(close_record),
            "scoring_volatility": _compact_number(statistics.pstdev(points_for_values) if len(points_for_values) > 1 else 0.0 if points_for_values else None),
            "defensive_volatility": _compact_number(statistics.pstdev(points_against_values) if len(points_against_values) > 1 else 0.0 if points_against_values else None),
            "late_season_win_rate": _win_rate(late_record),
            "schedule_strength_proxy": None,
            "simple_team_rating": _compact_number(sum(margins) / games_played if games_played else None),
            "home_win_rate": _win_rate(home_record),
            "away_win_rate": _win_rate(away_record),
            "average_rest_days": _compact_number(_mean(rest_days_values)),
            "blowout_wins": blowout_wins,
            "blowout_losses": blowout_losses,
            "source_data_kind": "real_open_data",
            "regular_season_snapshot_only": True,
            "no_predictive_claim": True,
            "raw_payload_included": False,
        }
        profiles.append(profile)

    by_team_season = {(profile["season"], profile["team"]): profile for profile in profiles}
    opponent_rates: dict[tuple[str, str], list[float]] = defaultdict(list)
    for game in team_games:
        if str(game.get("game_type") or "").upper() != "REG":
            continue
        profile_key = (str(game.get("season") or ""), str(game.get("team") or ""))
        opponent = by_team_season.get((str(game.get("season") or ""), str(game.get("opponent") or "")))
        rate = _number(opponent.get("win_rate")) if opponent else None
        if rate is not None:
            opponent_rates[profile_key].append(rate)
    for profile in profiles:
        rates = opponent_rates.get((profile["season"], profile["team"]), [])
        profile["schedule_strength_proxy"] = _compact_number(_mean(rates))
    return profiles


def derive_postseason_target_labels(team_games: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for game in team_games:
        if str(game.get("source_data_kind") or "") != "real_open_data":
            continue
        grouped[(str(game.get("season") or ""), str(game.get("team") or ""))].append(game)

    targets: dict[tuple[str, str], dict[str, Any]] = {}
    for (season, team), games in sorted(grouped.items(), key=lambda item: (_season_key(item[0][0]), item[0][1])):
        missing_game_type = any(not str(game.get("game_type") or "").strip() for game in games)
        values: dict[str, bool | None]
        if missing_game_type:
            values = {target: None for target in POSTSEASON_TARGET_LABEL_FIELDS}
            blockers = {target: "target_label_missing" for target in POSTSEASON_TARGET_LABEL_FIELDS}
        else:
            postseason_games = [game for game in games if str(game.get("game_type") or "").upper() in POSTSEASON_GAME_TYPES]
            conference_games = [game for game in games if str(game.get("game_type") or "").upper() == "CON"]
            super_bowl_games = [game for game in games if str(game.get("game_type") or "").upper() == "SB"]
            values = {
                "made_playoffs": bool(postseason_games),
                "won_playoff_game": any(str(game.get("result") or "") == "win" for game in postseason_games),
                "reached_conference_championship": bool(conference_games),
                "reached_super_bowl": bool(super_bowl_games),
                "won_super_bowl": any(str(game.get("result") or "") == "win" for game in super_bowl_games),
            }
            blockers = {}
        targets[(season, team)] = {
            "season": season,
            "team": team,
            "target_values": values,
            "target_blockers": blockers,
            "labels_available": all(value is not None for value in values.values()),
            "source_supported_by_game_type": not missing_game_type,
            "no_fabricated_labels": True,
        }
    return targets


def _target_label_summaries(target_labels: dict[tuple[str, str], dict[str, Any]]) -> dict[str, dict[str, Any]]:
    summaries: dict[str, dict[str, Any]] = {}
    for target in POSTSEASON_TARGET_LABEL_FIELDS:
        values = [entry.get("target_values", {}).get(target) for entry in target_labels.values()]
        available = [bool(value) for value in values if value is not None]
        positive = sum(1 for value in available if value)
        negative = sum(1 for value in available if not value)
        missing = len(values) - len(available)
        summaries[target] = {
            "target_name": target,
            "labels_available_count": len(available),
            "labels_missing_count": missing,
            "positive_count": positive,
            "negative_count": negative,
            "base_rate": _compact_rate(positive / len(available) if available else None),
            "target_supported": bool(available),
            "target_blocker": None if available else "insufficient_labels",
        }
    return summaries


def _compute_holdout_similarity(
    profile_a: dict[str, Any],
    profile_b: dict[str, Any],
    *,
    allowed_features: list[str],
) -> dict[str, Any]:
    features_compared: list[str] = []
    features_missing: list[str] = []
    similarities: list[float] = []
    for feature in allowed_features:
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
            "blocked_reason": "insufficient_features",
            "no_predictive_claim": True,
        }
    return {
        "similarity_score": round(sum(similarities) / len(similarities), 4),
        "features_compared": features_compared,
        "features_missing": features_missing,
        "confidence": "medium" if len(features_compared) >= 8 else "low",
        "blocked_reason": None,
        "no_predictive_claim": True,
    }


def find_prior_season_comps(
    anchor_profile: dict[str, Any],
    candidate_profiles: list[dict[str, Any]],
    *,
    top_k: int,
    allowed_features: list[str] | None = None,
) -> list[dict[str, Any]]:
    allowed = list(allowed_features or HOLDOUT_ALLOWED_SIMILARITY_FEATURES)
    anchor_season = _season_key(anchor_profile.get("season"))
    comps: list[dict[str, Any]] = []
    for candidate in candidate_profiles:
        candidate_season = _season_key(candidate.get("season"))
        if candidate_season < 0 or anchor_season < 0:
            continue
        if candidate_season >= anchor_season:
            continue
        similarity = _compute_holdout_similarity(anchor_profile, candidate, allowed_features=allowed)
        if similarity.get("similarity_score") is None:
            continue
        comps.append(
            {
                "anchor_team": anchor_profile.get("team"),
                "anchor_season": anchor_profile.get("season"),
                "comp_team": candidate.get("team"),
                "comp_season": candidate.get("season"),
                "similarity_score": similarity.get("similarity_score"),
                "features_compared": similarity.get("features_compared") or [],
                "features_missing": similarity.get("features_missing") or [],
                "confidence": similarity.get("confidence"),
                "prior_season_only": True,
                "same_season_excluded": True,
                "future_season_excluded": True,
                "no_predictive_claim": True,
            }
        )
    comps.sort(key=lambda item: (-float(item.get("similarity_score") or 0.0), str(item.get("comp_season")), str(item.get("comp_team"))))
    return comps[: max(0, int(top_k))]


def _prior_base_rate(
    *,
    anchor_profile: dict[str, Any],
    target_name: str,
    target_labels: dict[tuple[str, str], dict[str, Any]],
) -> float | None:
    anchor_season = _season_key(anchor_profile.get("season"))
    values: list[bool] = []
    for (season, _team), entry in target_labels.items():
        if _season_key(season) >= anchor_season:
            continue
        value = entry.get("target_values", {}).get(target_name)
        if value is not None:
            values.append(bool(value))
    return sum(1 for value in values if value) / len(values) if values else None


def evaluate_comps_against_targets(
    anchor_profiles: list[dict[str, Any]],
    target_labels: dict[tuple[str, str], dict[str, Any]],
    *,
    k_values: list[int] | None = None,
    allowed_features: list[str] | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    allowed = list(allowed_features or HOLDOUT_ALLOWED_SIMILARITY_FEATURES)
    selected_k = list(k_values or HOLDOUT_K_VALUES)
    max_k = max(selected_k) if selected_k else 0
    comps_by_anchor: dict[tuple[str, str], list[dict[str, Any]]] = {}
    prior_base_by_anchor_target: dict[tuple[tuple[str, str], str], float | None] = {}
    for anchor in anchor_profiles:
        key = _team_season_key_for_item(anchor)
        comps_by_anchor[key] = find_prior_season_comps(anchor, anchor_profiles, top_k=max_k, allowed_features=allowed)
        for target_name in POSTSEASON_TARGET_LABEL_FIELDS:
            prior_base_by_anchor_target[(key, target_name)] = _prior_base_rate(
                anchor_profile=anchor,
                target_name=target_name,
                target_labels=target_labels,
            )
    target_summaries = _target_label_summaries(target_labels)
    validation_by_target: dict[str, dict[str, Any]] = {}
    validation_by_k: dict[str, list[dict[str, Any]]] = {str(k): [] for k in selected_k}

    for target_name, target_summary in target_summaries.items():
        target_rows: list[dict[str, Any]] = []
        for k in selected_k:
            anchors_evaluated = 0
            anchors_skipped = 0
            skip_reasons: Counter[str] = Counter()
            comp_rates: list[float] = []
            base_rates: list[float] = []
            feature_counts: list[float] = []
            missing_counts: list[float] = []
            directional_hits = 0
            directional_total = 0
            for anchor in anchor_profiles:
                key = _team_season_key_for_item(anchor)
                anchor_target = target_labels.get(key, {}).get("target_values", {}).get(target_name)
                if anchor_target is None:
                    anchors_skipped += 1
                    skip_reasons["target_label_missing"] += 1
                    continue
                prior_base = prior_base_by_anchor_target.get((key, target_name))
                if prior_base is None:
                    anchors_skipped += 1
                    skip_reasons["no_prior_target_labels"] += 1
                    continue
                comps = comps_by_anchor.get(key, [])[:k]
                if not comps:
                    anchors_skipped += 1
                    skip_reasons["no_prior_comps"] += 1
                    continue
                comp_values: list[bool] = []
                for comp in comps:
                    comp_key = (str(comp.get("comp_season") or ""), str(comp.get("comp_team") or ""))
                    value = target_labels.get(comp_key, {}).get("target_values", {}).get(target_name)
                    if value is not None:
                        comp_values.append(bool(value))
                        feature_counts.append(float(len(comp.get("features_compared") or [])))
                        missing_counts.append(float(len(comp.get("features_missing") or [])))
                if not comp_values:
                    anchors_skipped += 1
                    skip_reasons["no_comp_target_labels"] += 1
                    continue
                comp_rate = sum(1 for value in comp_values if value) / len(comp_values)
                comp_rates.append(comp_rate)
                base_rates.append(prior_base)
                signal_positive = comp_rate >= prior_base
                if signal_positive == bool(anchor_target):
                    directional_hits += 1
                directional_total += 1
                anchors_evaluated += 1
            average_comp_rate = _mean(comp_rates)
            average_base_rate = _mean(base_rates)
            lift = average_comp_rate - average_base_rate if average_comp_rate is not None and average_base_rate is not None else None
            median_features = _median(feature_counts)
            avg_missing = _mean(missing_counts)
            minimum_sample_warning = anchors_evaluated < MINIMUM_HOLDOUT_ANCHORS
            if not target_summary["target_supported"]:
                status = "insufficient_labels"
            elif median_features is None or median_features < MIN_SIMILARITY_FEATURES:
                status = "insufficient_features"
            elif minimum_sample_warning:
                status = "insufficient_samples"
            elif lift is not None and abs(lift) >= 0.02:
                status = "historical_signal_candidate_no_predictive_claim"
            else:
                status = "holdout_backtest_ready_no_predictive_claim"
            row = {
                "target": target_name,
                "anchors_evaluated": anchors_evaluated,
                "anchors_skipped": anchors_skipped,
                "skip_reasons": dict(sorted(skip_reasons.items())),
                "average_comp_positive_rate": _compact_rate(average_comp_rate),
                "historical_base_rate": _compact_rate(average_base_rate),
                "lift_vs_base_rate": _compact_rate(lift),
                "directional_hit_rate": _compact_rate(directional_hits / directional_total if directional_total else None),
                "sample_count": anchors_evaluated,
                "top_k": k,
                "median_features_compared": _compact_rate(median_features),
                "average_features_missing": _compact_rate(avg_missing),
                "minimum_sample_warning": minimum_sample_warning,
                "confidence_tier": "high_context" if anchors_evaluated >= 300 and (median_features or 0) >= 8 else "medium_context" if anchors_evaluated >= MINIMUM_HOLDOUT_ANCHORS else "low_sample",
                "validation_status": status,
                "no_predictive_claim": True,
            }
            target_rows.append(row)
            validation_by_k[str(k)].append(row)
        validation_by_target[target_name] = {
            **target_summary,
            "by_k": target_rows,
            "validation_status": _target_status(target_rows),
            "no_predictive_claim": True,
        }
    return validation_by_target, validation_by_k


def _target_status(rows: list[dict[str, Any]]) -> str:
    statuses = [str(row.get("validation_status") or "") for row in rows]
    if any(status == "historical_signal_candidate_no_predictive_claim" for status in statuses):
        return "historical_signal_candidate_no_predictive_claim"
    if any(status == "holdout_backtest_ready_no_predictive_claim" for status in statuses):
        return "holdout_backtest_ready_no_predictive_claim"
    if any(status == "validation_scaffold_ready_no_predictive_claim" for status in statuses):
        return "validation_scaffold_ready_no_predictive_claim"
    if any(status == "insufficient_samples" for status in statuses):
        return "insufficient_samples"
    if any(status == "insufficient_features" for status in statuses):
        return "insufficient_features"
    return "insufficient_labels"


def build_holdout_leakage_guard(allowed_features: list[str] | None = None) -> dict[str, Any]:
    allowed = list(allowed_features or HOLDOUT_ALLOWED_SIMILARITY_FEATURES)
    leaked = sorted(set(allowed) & set(HOLDOUT_BLOCKED_LEAKAGE_FEATURES))
    return {
        "status": "blocked_leakage_detected" if leaked else "passed",
        "leakage_detected": bool(leaked),
        "leaked_features": leaked,
        "allowed_similarity_features": allowed,
        "blocked_leakage_features": HOLDOUT_BLOCKED_LEAKAGE_FEATURES,
        "target_label_fields": POSTSEASON_TARGET_LABEL_FIELDS,
        "future_data_excluded": True,
        "prior_seasons_only": True,
        "regular_season_snapshot_only": True,
        "postseason_labels_used_only_as_targets": True,
        "no_market_data_used": True,
        "no_roster_data_used": True,
        "no_injury_data_used": True,
    }


def _overall_holdout_status(
    *,
    leakage_guard: dict[str, Any],
    validation_by_target: dict[str, dict[str, Any]],
    anchor_profiles_evaluated: int,
) -> str:
    if leakage_guard.get("leakage_detected"):
        return "blocked_leakage_detected"
    if not validation_by_target:
        return "insufficient_labels"
    statuses = [str(row.get("validation_status") or "") for row in validation_by_target.values()]
    if anchor_profiles_evaluated < MINIMUM_HOLDOUT_ANCHORS:
        return "insufficient_samples"
    if any(status == "historical_signal_candidate_no_predictive_claim" for status in statuses):
        return "historical_signal_candidate_no_predictive_claim"
    if any(status == "holdout_backtest_ready_no_predictive_claim" for status in statuses):
        return "holdout_backtest_ready_no_predictive_claim"
    if any(status == "insufficient_features" for status in statuses):
        return "insufficient_features"
    if any(status == "insufficient_samples" for status in statuses):
        return "insufficient_samples"
    return "insufficient_labels"


def build_validation_guard_summary(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    """Classify newly available NFL feature builders before any validation use (Phase 6).

    Regular-season snapshot features (the schedule/result-derived similarity
    features) are the only validation-allowed inputs. All source-supported
    in-season feature builders (injury/roster/snap/depth/market/nextgen/pace)
    are blocked by default: by leakage when they are availability/market
    families, otherwise by cutoff sensitivity. Builders missing their source
    fields are blocked by missing provenance.
    """
    builder_report = build_nfl_feature_builder_report(base_data_dir=base_data_dir)
    builders = builder_report.get("feature_builders") or []
    allowed_features = list(HOLDOUT_ALLOWED_SIMILARITY_FEATURES)
    blocked_by_leakage: list[str] = []
    blocked_by_cutoff: list[str] = []
    blocked_by_future_data: list[str] = []
    blocked_by_missing_provenance: list[str] = []
    availability_leakage = {"availability_in_season_cutoff_required", "market_timing_cutoff_required"}
    for builder in builders:
        name = str(builder.get("feature_name"))
        if builder.get("status") != "available":
            blocked_by_missing_provenance.append(name)
            continue
        if builder.get("uses_future_data"):
            blocked_by_future_data.append(name)
            continue
        leakage_risk = str(builder.get("leakage_risk"))
        if name in HOLDOUT_BLOCKED_LEAKAGE_FEATURES or leakage_risk in availability_leakage:
            blocked_by_leakage.append(name)
        elif builder.get("cutoff_required"):
            blocked_by_cutoff.append(name)
        else:
            blocked_by_cutoff.append(name)
    candidate_feature_count = len(allowed_features) + len(builders)
    blocked_total = len(blocked_by_leakage) + len(blocked_by_cutoff) + len(blocked_by_future_data) + len(blocked_by_missing_provenance)
    return {
        "candidate_features_count": candidate_feature_count,
        "allowed_validation_features_count": len(allowed_features),
        "allowed_validation_features": allowed_features,
        "blocked_validation_features_count": blocked_total,
        "blocked_by_leakage": sorted(blocked_by_leakage),
        "blocked_by_cutoff": sorted(blocked_by_cutoff),
        "blocked_by_future_data": sorted(blocked_by_future_data),
        "blocked_by_missing_provenance": sorted(blocked_by_missing_provenance),
        "newly_available_feature_builders_blocked_by_default": True,
        "market_features_cutoff_sensitive_by_default": True,
        "postseason_labels_target_only": True,
        "no_predictive_claim": True,
    }


def build_historical_holdout_validation_scorecard(
    *,
    base_data_dir: str | Path | None = None,
    allowed_similarity_features: list[str] | None = None,
    k_values: list[int] | None = None,
) -> dict[str, Any]:
    base = resolve_base_data_dir(base_data_dir)
    rows, synthetic_ignored = load_real_nfl_rows(base_data_dir=base)
    team_games = build_team_game_profiles(rows)
    snapshots = build_regular_season_snapshot_profiles(team_games)
    target_labels = derive_postseason_target_labels(team_games)
    leakage_guard = build_holdout_leakage_guard(allowed_similarity_features)
    selected_k = list(k_values or HOLDOUT_K_VALUES)
    if leakage_guard.get("leakage_detected"):
        validation_by_target: dict[str, dict[str, Any]] = {}
        validation_by_k: dict[str, list[dict[str, Any]]] = {str(k): [] for k in selected_k}
        anchor_profiles_evaluated = 0
        anchor_profiles_skipped = len(snapshots)
    else:
        validation_by_target, validation_by_k = evaluate_comps_against_targets(
            snapshots,
            target_labels,
            k_values=selected_k,
            allowed_features=list(allowed_similarity_features or HOLDOUT_ALLOWED_SIMILARITY_FEATURES),
        )
        evaluated_keys = set()
        skipped = 0
        for target in validation_by_target.values():
            for row in target.get("by_k") or []:
                if int(row.get("top_k", 0) or 0) == selected_k[0]:
                    evaluated_keys.add(target.get("target_name"))
                    skipped = max(skipped, int(row.get("anchors_skipped", 0) or 0))
        anchor_profiles_evaluated = max((int(row.get("anchors_evaluated", 0) or 0) for rows_by_k in validation_by_k.values() for row in rows_by_k), default=0)
        anchor_profiles_skipped = skipped
    target_summaries = _target_label_summaries(target_labels)
    seasons = sorted({str(profile.get("season")) for profile in snapshots}, key=_season_key)
    validation_guard_summary = build_validation_guard_summary(base_data_dir=base)
    status = _overall_holdout_status(
        leakage_guard=leakage_guard,
        validation_by_target=validation_by_target,
        anchor_profiles_evaluated=anchor_profiles_evaluated,
    )
    return {
        **SAFETY_FIELDS,
        "ok": True,
        "status": status,
        "validation_guard_summary": validation_guard_summary,
        "schema_version": "nfl_historical_holdout_validation_v1",
        "created_at": utc_now_iso(),
        "run_id": sanitize_filename(f"nfl_pattern_validation_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
        "runtime_data_dir": str(base),
        "report_root": str(base / "data_sources" / "open_sports_history" / "nfl_pattern_validation"),
        "seasons_analyzed": seasons,
        "real_rows_consumed": len(rows),
        "synthetic_rows_ignored": synthetic_ignored,
        "team_season_profiles_used": len(snapshots),
        "anchor_profiles_evaluated": anchor_profiles_evaluated,
        "anchor_profiles_skipped": anchor_profiles_skipped,
        "targets_evaluated": POSTSEASON_TARGET_LABEL_FIELDS,
        "target_label_summary": target_summaries,
        "holdout_method": "regular_season_snapshot_prior_seasons_only",
        "similarity_k_values": selected_k,
        "leakage_guard": leakage_guard,
        "validation_by_target": validation_by_target,
        "validation_by_k": validation_by_k,
        "feature_catalog": {
            "allowed_similarity_features": list(allowed_similarity_features or HOLDOUT_ALLOWED_SIMILARITY_FEATURES),
            "blocked_leakage_features": HOLDOUT_BLOCKED_LEAKAGE_FEATURES,
            "blocked_unavailable_feature_families": [
                "market_price_or_odds",
                "injury_lineup_profile",
                "roster_continuity",
                "pace_or_advanced_efficiency",
            ],
        },
        "blockers": [] if status not in {"insufficient_labels", "insufficient_features", "insufficient_samples", "blocked_leakage_detected"} else [status],
        "no_predictive_claim": True,
        "predictive_claim_made": False,
        "betting_decision_made": False,
        "confirmed_bets_created": False,
        "no_bet_rows_modified": False,
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
        "recommended_next_step": "review holdout validation metrics as historical context only; do not use for betting or execution",
        "storage_health": get_storage_health(),
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
    label_summary = _label_coverage_summary(rows)
    seasons = sorted({str(profile.get("season")) for profile in team_seasons}, key=_season_key)
    teams = sorted({str(profile.get("team")) for profile in team_seasons})
    example_similarity = None
    example_comps: list[dict[str, Any]] = []
    if len(team_seasons) >= 2:
        example_similarity = compute_team_profile_similarity(team_seasons[0], team_seasons[1])
        example_comps = find_historical_team_comps(
            team_seasons,
            anchor_team=str(team_seasons[0].get("team")),
            anchor_season=str(team_seasons[0].get("season")),
            limit=5,
        )
    validation_scorecard = build_pattern_validation_scorecard(team_seasons, catalog)
    readiness_status = validation_scorecard["validation_status"]
    expanded_readiness = build_expanded_feature_readiness(base_data_dir=base)
    exhaustion = build_nfl_source_exhaustion_report(base_data_dir=base)
    coaching = coaching_readiness_flags(base_data_dir=base)
    cutoff_summary = cutoff_feature_availability_summary()
    return {
        **SAFETY_FIELDS,
        **expanded_readiness,
        **coaching,
        "nfl_source_exhaustion_checked": True,
        "nfl_new_safe_sources_found": exhaustion.get("nfl_new_safe_sources_found") or [],
        "nfl_redundant_sources_skipped": exhaustion.get("nfl_redundant_sources_skipped") or [],
        "nfl_blocked_sources": exhaustion.get("nfl_blocked_sources") or [],
        "nfl_coaching_data_blocked_reason": None
        if coaching["nfl_coaching_data_available"]
        else "no_coaching_rows_ingested_yet_sources_disabled_by_default",
        "nfl_cutoff_week_features_available": cutoff_summary["nfl_cutoff_week_features_available"],
        "nfl_cutoff_week_feature_groups_available": cutoff_summary["nfl_cutoff_week_feature_groups_available"],
        "nfl_cutoff_week_leakage_guard_status": cutoff_summary["nfl_cutoff_week_leakage_guard_status"],
        "nfl_cutoff_week_snapshot_count": 0,
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
        "example_historical_comps": example_comps,
        "postseason_label_status": label_summary["postseason_label_status"],
        "playoff_label_coverage_count": label_summary["playoff_label_coverage_count"],
        "playoff_label_missing_count": label_summary["playoff_label_missing_count"],
        "super_bowl_label_coverage_count": label_summary["super_bowl_label_coverage_count"],
        "super_bowl_label_missing_count": label_summary["super_bowl_label_missing_count"],
        "playoff_round_label_method": label_summary["playoff_round_label_method"],
        "super_bowl_label_method": label_summary["super_bowl_label_method"],
        "playoff_super_bowl_labels_available": label_summary["postseason_label_status"],
        "label_blockers": label_summary["label_blockers"],
        "label_coverage_by_season": label_summary["label_coverage_by_season"],
        "label_blockers_by_season": label_summary["label_blockers_by_season"],
        "validation_scorecard": validation_scorecard,
        "validation_status": validation_scorecard["validation_status"],
        "no_predictive_claim": True,
        "no_fabricated_labels": True,
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
        "recommended_next_step": "fill remaining source-supported nflverse game_type coverage before any predictive validation claims",
        "storage_health": get_storage_health(),
    }


def render_nfl_pattern_lab_markdown(report: dict[str, Any]) -> str:
    scorecard = report.get("validation_scorecard") or {}
    lines = [
        "# NFL Historical Pattern Lab v2",
        "",
        f"1. seasons_analyzed: {', '.join(report.get('seasons_analyzed') or []) if report.get('seasons_analyzed') else 'none'}",
        f"2. teams_profiled: {len(report.get('teams_profiled') or [])}",
        f"3. team_season_profiles_created: {report.get('team_season_profiles_created')}",
        f"4. team_game_profiles_created: {report.get('team_game_profiles_created')}",
        f"5. matchup_profiles_created: {report.get('matchup_profiles_created')}",
        f"6. playoff_label_method: {report.get('playoff_round_label_method')}",
        f"7. playoff_label_coverage_count: {report.get('playoff_label_coverage_count')}",
        f"8. playoff_label_missing_count: {report.get('playoff_label_missing_count')}",
        f"9. super_bowl_label_method: {report.get('super_bowl_label_method')}",
        f"10. super_bowl_label_coverage_count: {report.get('super_bowl_label_coverage_count')}",
        f"11. super_bowl_label_missing_count: {report.get('super_bowl_label_missing_count')}",
        f"12. label_blockers: {', '.join(report.get('label_blockers') or []) if report.get('label_blockers') else 'none'}",
        f"13. label_blockers_by_season: {json.dumps(report.get('label_blockers_by_season') or {}, sort_keys=True)}",
        f"14. no_fabricated_labels: {str(report.get('no_fabricated_labels')).lower()}",
        f"15. similarity_features_available: {', '.join(report.get('similarity_features_available') or []) if report.get('similarity_features_available') else 'none'}",
        f"16. similarity_features_blocked: {', '.join(report.get('similarity_features_blocked') or []) if report.get('similarity_features_blocked') else 'none'}",
        f"17. validation_status: {scorecard.get('validation_status')}",
        f"18. backtest_ready: {str(scorecard.get('backtest_ready')).lower()}",
        "19. no_predictive_claim=true",
        "20. raw_payload_included=false",
        "21. secrets_included=false",
        "22. provider_write=false",
        "23. execution_allowed=false",
        f"24. recommended_next_step: {report.get('recommended_next_step')}",
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


def _validation_root(base_data_dir: str | Path | None = None) -> Path:
    base = get_data_sources_dir() if base_data_dir is None else resolve_base_data_dir(base_data_dir) / "data_sources"
    root = base / "open_sports_history" / "nfl_pattern_validation"
    root.mkdir(parents=True, exist_ok=True)
    return root


def render_nfl_pattern_validation_markdown(report: dict[str, Any]) -> str:
    target_lines = []
    for target, details in sorted((report.get("validation_by_target") or {}).items()):
        first_k = (details.get("by_k") or [{}])[0]
        target_lines.append(
            f"- {target}: status={details.get('validation_status')}; base_rate={details.get('base_rate')}; "
            f"k{first_k.get('top_k')} comp_rate={first_k.get('average_comp_positive_rate')}; lift={first_k.get('lift_vs_base_rate')}"
        )
    lines = [
        "# NFL Historical Holdout Validation",
        "",
        f"1. status: {report.get('status')}",
        f"2. seasons_analyzed: {', '.join(report.get('seasons_analyzed') or []) if report.get('seasons_analyzed') else 'none'}",
        f"3. real_rows_consumed: {report.get('real_rows_consumed')}",
        f"4. synthetic_rows_ignored: {report.get('synthetic_rows_ignored')}",
        f"5. team_season_profiles_used: {report.get('team_season_profiles_used')}",
        f"6. anchor_profiles_evaluated: {report.get('anchor_profiles_evaluated')}",
        f"7. anchor_profiles_skipped: {report.get('anchor_profiles_skipped')}",
        f"8. holdout_method: {report.get('holdout_method')}",
        f"9. similarity_k_values: {', '.join(str(item) for item in report.get('similarity_k_values') or [])}",
        f"10. leakage_guard_status: {(report.get('leakage_guard') or {}).get('status')}",
        "11. no_predictive_claim=true",
        "12. provider_calls_attempted=0",
        "13. downloads_attempted=0",
        "14. provider_write=false",
        "15. execution_allowed=false",
        "",
        "## Targets",
        *(target_lines or ["- none"]),
        "",
        f"recommended_next_step: {report.get('recommended_next_step')}",
        "",
    ]
    return "\n".join(lines)


def write_nfl_historical_holdout_validation_report(
    report: dict[str, Any],
    *,
    base_data_dir: str | Path | None = None,
) -> dict[str, str]:
    root = _validation_root(base_data_dir)
    run_id = sanitize_filename(str(report.get("run_id") or f"nfl_pattern_validation_{uuid4().hex[:8]}"))
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
    markdown = render_nfl_pattern_validation_markdown(payload)
    _atomic_write_json(latest_json, payload)
    _atomic_write_text(latest_md, markdown)
    _atomic_write_json(item_json, payload)
    _atomic_write_text(item_md, markdown)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--persist", action="store_true")
    parser.add_argument("--validation", action="store_true")
    args = parser.parse_args(argv)
    report = build_historical_holdout_validation_scorecard() if args.validation else build_nfl_historical_pattern_lab_report()
    paths: dict[str, str] = {}
    if args.persist:
        paths = (
            write_nfl_historical_holdout_validation_report(report)
            if args.validation
            else write_nfl_historical_pattern_lab_report(report)
        )
        report.update(paths)
    if args.validation:
        print(
            json.dumps(
                {
                    "ok": report["ok"],
                    "status": report["status"],
                    "seasons_analyzed": report["seasons_analyzed"],
                    "real_rows_consumed": report["real_rows_consumed"],
                    "synthetic_rows_ignored": report["synthetic_rows_ignored"],
                    "team_season_profiles_used": report["team_season_profiles_used"],
                    "anchor_profiles_evaluated": report["anchor_profiles_evaluated"],
                    "anchor_profiles_skipped": report["anchor_profiles_skipped"],
                    "targets_evaluated": report["targets_evaluated"],
                    "holdout_method": report["holdout_method"],
                    "similarity_k_values": report["similarity_k_values"],
                    "leakage_guard": report["leakage_guard"],
                    "validation_guard_summary": report["validation_guard_summary"],
                    "validation_by_target": report["validation_by_target"],
                    "validation_by_k": report["validation_by_k"],
                    "no_predictive_claim": True,
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
                "expanded_feature_catalog_available": report.get("expanded_feature_catalog_available"),
                "expanded_feature_families_available": report.get("expanded_feature_families_available"),
                "expanded_feature_families_blocked": report.get("expanded_feature_families_blocked"),
                "source_supported_feature_count": report.get("source_supported_feature_count"),
                "source_supported_feature_builder_count": report.get("source_supported_feature_builder_count"),
                "postseason_label_status": report["postseason_label_status"],
                "playoff_round_label_method": report["playoff_round_label_method"],
                "playoff_label_coverage_count": report["playoff_label_coverage_count"],
                "playoff_label_missing_count": report["playoff_label_missing_count"],
                "super_bowl_label_method": report["super_bowl_label_method"],
                "super_bowl_label_coverage_count": report["super_bowl_label_coverage_count"],
                "super_bowl_label_missing_count": report["super_bowl_label_missing_count"],
                "label_blockers": report["label_blockers"],
                "label_coverage_by_season": report["label_coverage_by_season"],
                "label_blockers_by_season": report["label_blockers_by_season"],
                "playoff_super_bowl_labels_available": report["playoff_super_bowl_labels_available"],
                "validation_scorecard": report["validation_scorecard"],
                "no_predictive_claim": True,
                "no_fabricated_labels": report["no_fabricated_labels"],
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

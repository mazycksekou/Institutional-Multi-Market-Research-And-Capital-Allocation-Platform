from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from uuid import uuid4

from .data_availability_tiers import resolve_profile_key
from .data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from .scheduler_config import sanitize_filename, utc_now_iso


DERIVED_FEATURE_REPORT_SCHEMA_VERSION = "derived_feature_backfill_report_v1"

REPORT_MODULES = [
    "basketball_nba",
    "basketball_wnba",
    "basketball_ncaab",
    "basketball_ncaaw",
    "americanfootball_nfl",
    "americanfootball_ncaaf",
    "baseball_mlb",
    "icehockey_nhl",
    "soccer",
    "tennis",
    "ufc_mma",
    "boxing",
    "golf",
    "prediction_markets",
    "kalshi",
    "polymarket",
    "sportsbooks",
    "stocks",
    "ETFs",
    "crypto",
    "bonds",
    "rates",
    "macro",
    "major_assets",
]

DERIVED_FEATURES = [
    "final_margin",
    "total_points",
    "total_runs",
    "total_goals",
    "total_sets",
    "winner",
    "result",
    "market_implied_probability",
    "prediction_market_outcome",
    "rolling_points_for",
    "rolling_points_against",
    "rolling_margin",
    "rolling_win_rate",
    "home_away_split",
    "rest_days",
    "volatility",
    "close_game_rate",
    "simple_team_rating",
    "opponent_adjusted_margin",
]

ALLOWED_BLOCKED_REASONS = {
    "available",
    "insufficient_history",
    "missing_required_fields",
    "missing_event_dates",
    "missing_home_away_fields",
    "missing_scores_or_results",
    "missing_market_prices",
    "missing_explicit_outcomes",
    "not_applicable_for_module",
    "unsupported_module",
    "no_local_records_found",
}

NORMALIZED_SCHEDULE_RESULT_SHAPE = [
    "module",
    "event_id",
    "source_id",
    "season",
    "week_or_round",
    "event_date",
    "home_participant",
    "away_participant",
    "neutral_site",
    "home_score",
    "away_score",
    "final_result",
    "winner",
    "final_margin",
    "total_score",
    "market_price_or_odds",
    "explicit_outcome",
    "data_source_path",
    "raw_payload_included",
]

SENSITIVE_KEY_PARTS = ("key", "secret", "token", "password", "auth", "credential", "signature", "header")
RAW_PAYLOAD_KEYS = {
    "provider_payload",
    "raw_payload",
    "external_payload",
    "source_payload",
    "source_payload_redacted",
    "raw_provider_payload",
    "raw_kalshi_payload",
    "raw_sharp_payload",
}
PLACEHOLDER_VALUES = {"", "n/a", "na", "none", "null", "unknown", "tbd", "placeholder"}

SPORT_MODULES = {
    "basketball_nba",
    "basketball_wnba",
    "basketball_ncaab",
    "basketball_ncaaw",
    "americanfootball_nfl",
    "americanfootball_ncaaf",
    "baseball_mlb",
    "icehockey_nhl",
    "soccer",
    "tennis",
    "ufc_mma",
    "boxing",
    "golf",
}
TEAM_SCORE_MODULES = {
    "basketball_nba",
    "basketball_wnba",
    "basketball_ncaab",
    "basketball_ncaaw",
    "americanfootball_nfl",
    "americanfootball_ncaaf",
    "baseball_mlb",
    "icehockey_nhl",
    "soccer",
}
PARTICIPANT_RESULT_MODULES = {"tennis", "ufc_mma", "boxing", "golf"}
PREDICTION_MARKET_MODULES = {"prediction_markets", "kalshi", "polymarket"}
MARKET_PRICE_MODULES = SPORT_MODULES | PREDICTION_MARKET_MODULES | {"sportsbooks"}
ASSET_MODULES = {"stocks", "ETFs", "crypto", "bonds", "rates", "macro", "major_assets"}
SUPPORTED_MODULES = SPORT_MODULES | PREDICTION_MARKET_MODULES | {"sportsbooks"} | ASSET_MODULES

TOTAL_FEATURE_BY_MODULE = {
    "basketball_nba": "total_points",
    "basketball_wnba": "total_points",
    "basketball_ncaab": "total_points",
    "basketball_ncaaw": "total_points",
    "americanfootball_nfl": "total_points",
    "americanfootball_ncaaf": "total_points",
    "baseball_mlb": "total_runs",
    "icehockey_nhl": "total_goals",
    "soccer": "total_goals",
    "tennis": "total_sets",
}

TIER0_DERIVED_FEATURES = {
    "final_margin",
    "total_points",
    "total_runs",
    "total_goals",
    "total_sets",
    "winner",
    "result",
    "prediction_market_outcome",
}
TIER1_DERIVED_FEATURES = {
    "rolling_points_for",
    "rolling_points_against",
    "rolling_margin",
    "rolling_win_rate",
    "home_away_split",
    "rest_days",
    "volatility",
    "close_game_rate",
    "simple_team_rating",
    "opponent_adjusted_margin",
}
MISSING_FIELD_REASONS = {
    "missing_required_fields",
    "missing_event_dates",
    "missing_home_away_fields",
    "missing_scores_or_results",
    "missing_market_prices",
    "missing_explicit_outcomes",
}

MIN_HISTORY = {
    "final_margin": 1,
    "total_points": 1,
    "total_runs": 1,
    "total_goals": 1,
    "total_sets": 1,
    "winner": 1,
    "result": 1,
    "market_implied_probability": 1,
    "prediction_market_outcome": 1,
    "rolling_points_for": 3,
    "rolling_points_against": 3,
    "rolling_margin": 3,
    "rolling_win_rate": 3,
    "home_away_split": 3,
    "rest_days": 2,
    "volatility": 5,
    "close_game_rate": 5,
    "simple_team_rating": 3,
    "opponent_adjusted_margin": 3,
}

FEATURE_FIELDS_NEEDED = {
    "final_margin": ["home_score", "away_score"],
    "total_points": ["home_score", "away_score"],
    "total_runs": ["home_score", "away_score"],
    "total_goals": ["home_score", "away_score"],
    "total_sets": ["home_score", "away_score"],
    "winner": ["final_result"],
    "result": ["final_result"],
    "market_implied_probability": ["market_price_or_odds"],
    "prediction_market_outcome": ["explicit_outcome"],
    "rolling_points_for": ["home_score", "away_score"],
    "rolling_points_against": ["home_score", "away_score"],
    "rolling_margin": ["home_score", "away_score"],
    "rolling_win_rate": ["final_result"],
    "home_away_split": ["home_participant", "away_participant", "final_result"],
    "rest_days": ["event_date", "home_participant", "away_participant"],
    "volatility": ["final_margin"],
    "close_game_rate": ["final_margin"],
    "simple_team_rating": ["final_margin"],
    "opponent_adjusted_margin": ["final_margin", "home_participant", "away_participant"],
}

AVAILABILITY_ALIAS = {
    "crypto": "cryptocurrency_edge_lab",
}


def _real_value(value: Any) -> bool:
    if value in (None, [], {}):
        return False
    if isinstance(value, str) and value.strip().lower() in PLACEHOLDER_VALUES:
        return False
    return True


def _safe_number(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean_scalar(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return None


def _first_value(row: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in row and _real_value(row.get(key)):
            return _clean_scalar(row.get(key))
    return None


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _items_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return [row for row in payload["items"] if isinstance(row, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        return [row for row in payload["records"] if isinstance(row, dict)]
    return []


def _safe_record_slice(row: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in row.items():
        lower_key = str(key).lower()
        if lower_key in RAW_PAYLOAD_KEYS or any(part in lower_key for part in SENSITIVE_KEY_PARTS):
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            safe[str(key)] = value
    return safe


def _module_from_record(row: dict[str, Any], *, default: str | None = None) -> str:
    explicit = str(
        row.get("module")
        or row.get("sport_or_symbol")
        or row.get("sport")
        or row.get("league")
        or ""
    ).strip()
    normalized = explicit.lower().replace(" ", "_").replace("-", "_")
    module_aliases = {
        "nba": "basketball_nba",
        "wnba": "basketball_wnba",
        "ncaab": "basketball_ncaab",
        "ncaaw": "basketball_ncaaw",
        "nfl": "americanfootball_nfl",
        "ncaaf": "americanfootball_ncaaf",
        "mlb": "baseball_mlb",
        "nhl": "icehockey_nhl",
        "ufc": "ufc_mma",
        "mma": "ufc_mma",
        "stocks": "stocks",
        "stock": "stocks",
        "etfs": "ETFs",
        "cryptocurrency": "crypto",
    }
    if normalized in module_aliases:
        return module_aliases[normalized]
    if explicit in SUPPORTED_MODULES:
        return explicit

    provider = str(row.get("provider") or row.get("provider_id") or row.get("source") or "").lower()
    market_type = str(row.get("market_type") or row.get("source_type") or row.get("market") or "").lower()
    if "kalshi" in provider:
        return "kalshi"
    if "polymarket" in provider:
        return "polymarket"
    if "prediction" in market_type or "prediction" in provider:
        return "prediction_markets"
    if "sportsbook" in provider or "sportsbook" in market_type or "odds" in market_type:
        return "sportsbooks"
    return default or "prediction_markets"


def normalize_schedule_result_record(
    row: dict[str, Any],
    *,
    module: str | None = None,
    data_source_path: str | None = None,
) -> dict[str, Any]:
    safe = _safe_record_slice(row)
    module_name = module or _module_from_record(safe)
    home_score = _first_value(safe, ["home_score", "home_points", "home_runs", "home_goals", "points_for"])
    away_score = _first_value(safe, ["away_score", "away_points", "away_runs", "away_goals", "points_against"])
    home_n = _safe_number(home_score)
    away_n = _safe_number(away_score)
    final_margin = _first_value(safe, ["final_margin", "margin"])
    if final_margin is None and home_n is not None and away_n is not None:
        final_margin = home_n - away_n
    total_score = _first_value(safe, ["total_score", "total_points", "total_runs", "total_goals", "total_sets", "total"])
    if total_score is None and home_n is not None and away_n is not None:
        total_score = home_n + away_n
    winner = _first_value(safe, ["winner", "winning_team", "winning_participant"])
    if winner is None and home_n is not None and away_n is not None:
        if home_n > away_n:
            winner = _first_value(safe, ["home_participant", "home_team", "team", "fighter"])
        elif away_n > home_n:
            winner = _first_value(safe, ["away_participant", "away_team", "opponent"])
        else:
            winner = "draw"
    final_result = _first_value(safe, ["final_result", "result", "paper_result", "outcome_status"])
    explicit_outcome = _first_value(safe, ["explicit_outcome", "settlement_result", "final_outcome", "outcome"])
    return {
        "module": module_name,
        "event_id": _first_value(safe, ["event_id", "game_id", "match_id", "fight_id", "tournament_id", "market_id", "ticker", "contract_id"]),
        "source_id": _first_value(safe, ["source_id", "provider", "provider_id", "source"]),
        "season": _first_value(safe, ["season", "year"]),
        "week_or_round": _first_value(safe, ["week", "round", "matchday"]),
        "event_date": _first_value(safe, ["event_date", "date", "timestamp", "close_time", "settled_at", "created_at"]),
        "home_participant": _first_value(safe, ["home_participant", "home_team", "home", "team", "fighter"]),
        "away_participant": _first_value(safe, ["away_participant", "away_team", "away", "opponent"]),
        "neutral_site": _first_value(safe, ["neutral_site", "neutral"]),
        "home_score": home_score,
        "away_score": away_score,
        "final_result": final_result,
        "winner": winner,
        "final_margin": final_margin,
        "total_score": total_score,
        "market_price_or_odds": _first_value(
            safe,
            [
                "market_price_or_odds",
                "implied_probability",
                "observed_price",
                "yes_price",
                "odds_or_price",
                "best_odds",
                "best_line",
                "moneyline",
                "odds",
            ],
        ),
        "explicit_outcome": explicit_outcome,
        "data_source_path": data_source_path,
        "raw_payload_included": False,
    }


def _local_source_files(base: Path) -> list[tuple[str, Path]]:
    pairs: list[tuple[str, Path]] = []
    for relative in (
        "paper_ledger/latest.json",
        "paper_ledger/paper_decisions.json",
        "outcomes/latest.json",
        "outcomes/outcomes.json",
        "review_queue/latest.json",
        "review_queue/review_queue.json",
        "prediction_market_outcome_candidates/latest.json",
    ):
        pairs.append((relative, base / relative))
    for directory in ("paper_ledger/items", "outcomes/items", "review_queue/items"):
        item_dir = base / directory
        if item_dir.exists():
            for path in sorted(item_dir.glob("*.json")):
                pairs.append((str(path.relative_to(base)).replace("\\", "/"), path))
    return pairs


def _open_sports_history_latest_path(base: Path) -> tuple[str, Path]:
    relative = "data_sources/open_sports_history/validated/latest.json"
    return relative, base / relative


def _open_sports_history_payload_paths(base: Path) -> list[tuple[str, Path]]:
    pairs: list[tuple[str, Path]] = []
    latest = _open_sports_history_latest_path(base)
    if latest[1].exists():
        pairs.append(latest)
    by_module = base / "data_sources" / "open_sports_history" / "validated" / "by_module"
    if by_module.exists():
        for path in sorted(by_module.glob("*.json")):
            pairs.append((str(path.relative_to(base)).replace("\\", "/"), path))
    by_season = base / "data_sources" / "open_sports_history" / "validated" / "by_season"
    if by_season.exists():
        for path in sorted(by_season.glob("*/*.json")):
            pairs.append((str(path.relative_to(base)).replace("\\", "/"), path))
    return pairs


def _nfl_open_data_coverage_path(base: Path) -> tuple[str, Path]:
    relative = "data_sources/nfl_open_data/coverage_matrix/latest.json"
    return relative, base / relative


def _nfl_open_data_feature_availability(base: Path) -> dict[str, bool]:
    _, path = _nfl_open_data_coverage_path(base)
    payload = _read_json(path)
    if not isinstance(payload, dict) or not isinstance(payload.get("feature_availability"), dict):
        return {
            "play_by_play_available": False,
            "team_stats_available": False,
            "weekly_player_stats_available": False,
            "roster_data_available": False,
            "weekly_rosters_available": False,
            "snap_counts_available": False,
            "participation_available": False,
            "depth_charts_available": False,
            "injury_data_available": False,
            "pace_play_volume_available": False,
            "roster_continuity_available": False,
            "nextgen_stats_available": False,
            "player_stats_available": False,
            "draft_combine_available": False,
            "market_data_available": False,
        }
    return {
        str(key): bool(value)
        for key, value in payload["feature_availability"].items()
        if isinstance(key, str)
    }


def _item_is_real_open_data(item: dict[str, Any]) -> bool:
    synthetic_flag = item.get("is_synthetic")
    synthetic_text = str(synthetic_flag).strip().lower()
    return item.get("data_kind") == "real_open_data" and synthetic_flag is not True and synthetic_text not in {"true", "1", "yes"}


def _open_sports_history_records(base: Path) -> tuple[dict[str, list[dict[str, Any]]], str | None, int, int, int]:
    relative, path = _open_sports_history_latest_path(base)
    payload_paths = _open_sports_history_payload_paths(base)
    if not payload_paths:
        return {}, relative if path.exists() else None, 0, 0, 0
    records_by_module: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen: set[tuple[str, str, str]] = set()
    real_consumed = 0
    synthetic_ignored = 0
    total_seen = 0
    primary_relative = payload_paths[0][0]
    for payload_relative, payload_path in payload_paths:
        payload = _read_json(payload_path)
        if not isinstance(payload, dict):
            continue
        candidates = payload.get("validated_preview_rows")
        if not isinstance(candidates, list):
            candidates = payload.get("preview_rows")
        for item in candidates or []:
            if not isinstance(item, dict):
                continue
            if item.get("raw_payload_included") is True:
                continue
            if str(item.get("validation_status") or item.get("blocked_reason") or "").lower() not in {"available"}:
                continue
            module = str(item.get("module") or "")
            if not module:
                continue
            event_id = str(item.get("event_id") or "")
            source_id = str(item.get("source_id") or "open_sports_history")
            dedupe_key = (module, source_id, event_id)
            if event_id and dedupe_key in seen:
                continue
            if event_id:
                seen.add(dedupe_key)
            total_seen += 1
            if not _item_is_real_open_data(item):
                synthetic_ignored += 1
                continue
            row = {
                "module": module,
                "event_id": item.get("event_id"),
                "source_id": item.get("source_id"),
                "season": item.get("season"),
                "week_or_round": item.get("week_or_round"),
                "event_date": item.get("event_date"),
                "home_participant": item.get("home_participant"),
                "away_participant": item.get("away_participant"),
                "neutral_site": item.get("neutral_site"),
                "home_score": item.get("home_score"),
                "away_score": item.get("away_score"),
                "final_result": item.get("final_result"),
                "winner": item.get("winner"),
                "final_margin": item.get("final_margin"),
                "total_score": item.get("total_score"),
                "market_price_or_odds": None,
                "explicit_outcome": None,
                "data_source_path": item.get("source_file_or_ref") or payload_relative,
                "raw_payload_included": False,
                "data_kind": item.get("data_kind"),
                "is_synthetic": item.get("is_synthetic"),
                "source_url_kind": item.get("source_url_kind"),
                "source_verified_at": item.get("source_verified_at"),
            }
            records_by_module[module].append(row)
            real_consumed += 1
    return dict(records_by_module), primary_relative, real_consumed, synthetic_ignored, total_seen


def load_local_normalized_records(*, base_data_dir: str | Path | None = None) -> dict[str, list[dict[str, Any]]]:
    base = resolve_base_data_dir(base_data_dir)
    records_by_module: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen: set[tuple[str, str, str]] = set()
    for relative, path in _local_source_files(base):
        payload = _read_json(path)
        if payload is None:
            continue
        for item in _items_from_payload(payload):
            module = _module_from_record(item)
            normalized = normalize_schedule_result_record(item, module=module, data_source_path=relative)
            event_key = str(normalized.get("event_id") or "")
            source_key = str(normalized.get("source_id") or relative)
            dedupe_key = (module, event_key, source_key)
            if event_key and dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            records_by_module[module].append(normalized)
    open_records, _, _, _, _ = _open_sports_history_records(base)
    for module, rows in open_records.items():
        for row in rows:
            event_key = str(row.get("event_id") or "")
            source_key = str(row.get("source_id") or "open_sports_history")
            dedupe_key = (module, event_key, source_key)
            if event_key and dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            records_by_module[module].append(row)
    return dict(records_by_module)


def _availability_rows(base: Path) -> dict[str, dict[str, Any]]:
    payload = _read_json(base / "data_sources" / "data_availability" / "latest.json")
    rows: dict[str, dict[str, Any]] = {}
    if isinstance(payload, dict):
        for row in payload.get("modules") or []:
            if isinstance(row, dict) and row.get("module"):
                rows[str(row["module"])] = row
    return rows


def _availability_for(module: str, rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if module in rows:
        return rows[module]
    alias = AVAILABILITY_ALIAS.get(module)
    if alias and alias in rows:
        return rows[alias]
    resolved = resolve_profile_key(module)
    for row_module, row in rows.items():
        if resolve_profile_key(row_module) == resolved:
            return row
    return {}


def _fields_from_records(records: list[dict[str, Any]]) -> set[str]:
    fields: set[str] = set()
    for row in records:
        for key, value in row.items():
            if key == "raw_payload_included":
                continue
            if _real_value(value):
                fields.add(key)
        if _safe_number(row.get("home_score")) is not None and _safe_number(row.get("away_score")) is not None:
            fields.update({"home_score", "away_score", "final_score", "points_for", "points_against", "final_margin", "total_score"})
        if _real_value(row.get("final_result")) or _real_value(row.get("winner")):
            fields.update({"final_result", "result", "winner"})
        if _real_value(row.get("market_price_or_odds")):
            fields.update({"market_price", "odds", "implied_probability", "market_price_or_odds"})
        if _real_value(row.get("explicit_outcome")):
            fields.update({"settlement_result", "explicit_outcome", "final_outcome"})
    return fields


def _has_scores(row: dict[str, Any]) -> bool:
    return _safe_number(row.get("home_score")) is not None and _safe_number(row.get("away_score")) is not None


def _has_margin(row: dict[str, Any]) -> bool:
    return _safe_number(row.get("final_margin")) is not None or _has_scores(row)


def _has_result(row: dict[str, Any]) -> bool:
    return _real_value(row.get("final_result")) or _real_value(row.get("winner")) or _real_value(row.get("explicit_outcome")) or _has_scores(row)


def _has_home_away(row: dict[str, Any]) -> bool:
    return _real_value(row.get("home_participant")) and _real_value(row.get("away_participant"))


def _feature_applicable(module: str, feature: str) -> bool:
    if module not in SUPPORTED_MODULES:
        return False
    if feature.startswith("total_"):
        return TOTAL_FEATURE_BY_MODULE.get(module) == feature
    if feature in {"final_margin", "rolling_points_for", "rolling_points_against", "rolling_margin", "home_away_split", "close_game_rate", "opponent_adjusted_margin"}:
        return module in TEAM_SCORE_MODULES
    if feature == "rolling_win_rate":
        return module in SPORT_MODULES
    if feature == "rest_days":
        return module in SPORT_MODULES
    if feature == "simple_team_rating":
        return module in TEAM_SCORE_MODULES
    if feature in {"winner", "result"}:
        return module in SPORT_MODULES
    if feature == "market_implied_probability":
        return module in MARKET_PRICE_MODULES
    if feature == "prediction_market_outcome":
        return module in PREDICTION_MARKET_MODULES
    if feature == "volatility":
        return module in TEAM_SCORE_MODULES or module in PREDICTION_MARKET_MODULES or module in ASSET_MODULES
    return True


def _history_count(records: list[dict[str, Any]], feature: str) -> int:
    if feature in {"final_margin", "total_points", "total_runs", "total_goals", "total_sets", "rolling_points_for", "rolling_points_against", "rolling_margin"}:
        return sum(1 for row in records if _has_scores(row))
    if feature in {"winner", "result", "rolling_win_rate"}:
        return sum(1 for row in records if _has_result(row))
    if feature == "market_implied_probability":
        return sum(1 for row in records if _real_value(row.get("market_price_or_odds")))
    if feature == "prediction_market_outcome":
        return sum(1 for row in records if str(row.get("explicit_outcome") or "").strip().lower() in {"yes", "no"})
    if feature == "home_away_split":
        return sum(1 for row in records if _has_home_away(row) and _has_result(row))
    if feature == "rest_days":
        return sum(1 for row in records if _real_value(row.get("event_date")) and _has_home_away(row))
    if feature in {"volatility", "close_game_rate", "simple_team_rating"}:
        return sum(1 for row in records if _has_margin(row))
    if feature == "opponent_adjusted_margin":
        return sum(1 for row in records if _has_margin(row) and _has_home_away(row))
    return len(records)


def _missing_fields_for_feature(records: list[dict[str, Any]], feature: str, fields_available: set[str]) -> tuple[list[str], str | None]:
    needed = list(FEATURE_FIELDS_NEEDED.get(feature, []))
    missing: list[str] = []
    reason: str | None = None
    if not records:
        return needed, "no_local_records_found"
    if feature in {"final_margin", "total_points", "total_runs", "total_goals", "total_sets", "rolling_points_for", "rolling_points_against", "rolling_margin"}:
        if not any(_has_scores(row) for row in records):
            missing = [field for field in ("home_score", "away_score") if field not in fields_available]
            return missing or ["home_score", "away_score"], "missing_scores_or_results"
    if feature in {"winner", "result", "rolling_win_rate"}:
        if not any(_has_result(row) for row in records):
            return ["final_result"], "missing_scores_or_results"
    if feature == "market_implied_probability" and not any(_real_value(row.get("market_price_or_odds")) for row in records):
        return ["market_price_or_odds"], "missing_market_prices"
    if feature == "prediction_market_outcome" and not any(str(row.get("explicit_outcome") or "").strip().lower() in {"yes", "no"} for row in records):
        return ["explicit_outcome"], "missing_explicit_outcomes"
    if feature == "home_away_split":
        if not any(_has_home_away(row) for row in records):
            return ["home_participant", "away_participant"], "missing_home_away_fields"
        if not any(_has_result(row) for row in records):
            return ["final_result"], "missing_scores_or_results"
    if feature == "rest_days":
        if not any(_real_value(row.get("event_date")) for row in records):
            return ["event_date"], "missing_event_dates"
        if not any(_has_home_away(row) for row in records):
            return ["home_participant", "away_participant"], "missing_home_away_fields"
    if feature in {"volatility", "close_game_rate", "simple_team_rating"} and not any(_has_margin(row) for row in records):
        return ["final_margin"], "missing_scores_or_results"
    if feature == "opponent_adjusted_margin":
        if not any(_has_margin(row) for row in records):
            return ["final_margin"], "missing_scores_or_results"
        if not any(_has_home_away(row) for row in records):
            return ["home_participant", "away_participant"], "missing_home_away_fields"
    for field in needed:
        if field not in fields_available:
            missing.append(field)
    return missing, reason


def _evaluate_feature(module: str, feature: str, records: list[dict[str, Any]], fields_available: set[str]) -> dict[str, Any]:
    needed = list(FEATURE_FIELDS_NEEDED.get(feature, []))
    minimum = int(MIN_HISTORY.get(feature, 1))
    if module not in SUPPORTED_MODULES:
        blocked_reason = "unsupported_module"
        history = 0
        missing = needed
    elif not _feature_applicable(module, feature):
        blocked_reason = "not_applicable_for_module"
        history = 0
        missing = []
    else:
        history = _history_count(records, feature)
        missing, specific_reason = _missing_fields_for_feature(records, feature, fields_available)
        if specific_reason is not None:
            blocked_reason = specific_reason
        elif history < minimum:
            blocked_reason = "insufficient_history"
        elif missing:
            blocked_reason = "missing_required_fields"
        else:
            blocked_reason = "available"
    if blocked_reason not in ALLOWED_BLOCKED_REASONS:
        blocked_reason = "missing_required_fields"
    can_derive = blocked_reason == "available"
    return {
        "feature_name": feature,
        "module": module,
        "derivation_status": "available" if can_derive else "blocked",
        "can_derive_now": can_derive,
        "fields_needed": needed,
        "fields_available": sorted(set(needed) & fields_available),
        "fields_missing": sorted(set(missing)),
        "minimum_history_required": minimum,
        "history_available": history,
        "blocked_reason": blocked_reason,
        "no_fabrication_confirmed": True,
    }


def _recommended_action(module: str, supported: list[str], blocked: list[dict[str, Any]]) -> str:
    if supported:
        if any(name.startswith("rolling_") or name in {"volatility", "close_game_rate", "simple_team_rating"} for name in supported):
            return "backfill Tier 1 derived features from existing local history"
        return "derive available Tier 0 fields from existing local records"
    reasons = Counter(str(row.get("blocked_reason")) for row in blocked)
    if reasons.get("no_local_records_found"):
        return "no-call audit of existing source reports for schedule/result rows"
    if reasons.get("insufficient_history"):
        return "append local historical result files or rerun existing no-call backfill"
    if module in PREDICTION_MARKET_MODULES and reasons.get("missing_explicit_outcomes"):
        return "continue compact explicit-settlement candidate checks without persistence"
    if reasons.get("missing_market_prices"):
        return "no-call audit of existing odds or market-price reports"
    return "mocked adapter test coverage for normalized schedule/result shape"


def _module_report(module: str, availability: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    availability_fields = set(str(field) for field in availability.get("fields_available") or [])
    record_fields = _fields_from_records(records)
    fields_available = availability_fields | record_fields
    features = [_evaluate_feature(module, feature, records, fields_available) for feature in DERIVED_FEATURES]
    supported = [row["feature_name"] for row in features if row["can_derive_now"]]
    blocked = [row for row in features if not row["can_derive_now"]]
    tier = str(availability.get("current_best_tier") or "UNKNOWN")
    return {
        "module": module,
        "current_best_tier": tier,
        "supported_derived_features": supported,
        "blocked_derived_features": [
            {
                "feature_name": row["feature_name"],
                "blocked_reason": row["blocked_reason"],
                "minimum_history_required": row["minimum_history_required"],
                "history_available": row["history_available"],
                "fields_missing": row["fields_missing"],
            }
            for row in blocked
        ],
        "feature_rows": features,
        "calibration_bucket": availability.get("calibration_bucket") or f"{resolve_profile_key(module)}.derived_feature_backfill",
        "confidence_cap_reason": availability.get("confidence_cap_reason") or "derived_feature_report_no_score_change",
        "recommended_next_no_spend_action": _recommended_action(module, supported, blocked),
        "local_records_seen": len(records),
        "fields_available": sorted(fields_available),
        "raw_payload_included": False,
    }


def build_derived_feature_backfill_report(
    *,
    base_data_dir: str | Path | None = None,
    module: str | None = None,
    records_by_module: dict[str, list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    base = resolve_base_data_dir(base_data_dir)
    availability = _availability_rows(base)
    (
        open_records,
        open_history_report,
        open_history_real_consumed,
        open_history_synthetic_ignored,
        open_history_seen,
    ) = _open_sports_history_records(base)
    local_records = records_by_module if records_by_module is not None else load_local_normalized_records(base_data_dir=base)
    module_names = [module] if module else REPORT_MODULES
    normalized_records: dict[str, list[dict[str, Any]]] = {}
    for name, rows in local_records.items():
        normalized_records[name] = [
            row if set(NORMALIZED_SCHEDULE_RESULT_SHAPE).issubset(row.keys()) else normalize_schedule_result_record(row, module=name)
            for row in rows
            if isinstance(row, dict)
        ]
    modules = [
        _module_report(name, _availability_for(name, availability), normalized_records.get(name, []))
        for name in module_names
    ]
    feature_rows = [feature for row in modules for feature in row["feature_rows"]]
    blocked_reason_counts = Counter(str(row["blocked_reason"]) for row in feature_rows if not row["can_derive_now"])
    tier_counts = Counter(str(row["current_best_tier"]) for row in modules)
    supported_total = sum(len(row["supported_derived_features"]) for row in modules)
    blocked_total = sum(len(row["blocked_derived_features"]) for row in modules)
    modules_ready_tier0 = [
        row["module"]
        for row in modules
        if any(feature in TIER0_DERIVED_FEATURES for feature in row["supported_derived_features"])
    ]
    modules_ready_tier1 = [
        row["module"]
        for row in modules
        if any(feature in TIER1_DERIVED_FEATURES for feature in row["supported_derived_features"])
    ]
    real_open_modules = set(open_records) if records_by_module is None else set()
    modules_ready_real_tier0 = [name for name in modules_ready_tier0 if name in real_open_modules]
    modules_ready_real_tier1 = [name for name in modules_ready_tier1 if name in real_open_modules]
    derivable_features = sorted({row["feature_name"] for row in feature_rows if row["can_derive_now"]})
    insufficient_history_features = sorted(
        {row["feature_name"] for row in feature_rows if row["blocked_reason"] == "insufficient_history"}
    )
    missing_field_features = sorted(
        {row["feature_name"] for row in feature_rows if row["blocked_reason"] in MISSING_FIELD_REASONS}
    )
    reports_consumed = [
        path
        for path in (
            "data_sources/data_availability/latest.json",
            "paper_ledger/latest.json",
            "paper_ledger/paper_decisions.json",
            "outcomes/latest.json",
            "outcomes/outcomes.json",
            "review_queue/latest.json",
            "review_queue/review_queue.json",
            "prediction_market_outcome_candidates/latest.json",
        )
        if (base / path).exists()
    ]
    if records_by_module is None and open_history_report and (base / open_history_report).exists():
        reports_consumed.append(open_history_report)
    nfl_open_data_report, nfl_open_data_report_path = _nfl_open_data_coverage_path(base)
    nfl_feature_availability = _nfl_open_data_feature_availability(base)
    if records_by_module is None and nfl_open_data_report_path.exists():
        reports_consumed.append(nfl_open_data_report)
    return {
        "ok": True,
        "status": "ok",
        "schema_version": DERIVED_FEATURE_REPORT_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "module_filter": module,
        "runtime_data_dir": str(base),
        "report_root": str(base / "data_sources" / "derived_features"),
        "root_runtime_path_confusion_resolved": True,
        "root_data_sources_path_used": False,
        "reports_consumed": reports_consumed,
        "open_sports_history_preview_rows_seen": open_history_seen if records_by_module is None else 0,
        "open_sports_history_preview_rows_consumed": open_history_real_consumed if records_by_module is None else 0,
        "open_sports_history_real_rows_consumed": open_history_real_consumed if records_by_module is None else 0,
        "open_sports_history_synthetic_rows_ignored": open_history_synthetic_ignored if records_by_module is None else 0,
        "synthetic_rows_ignored_for_real_coverage": True,
        "open_sports_history_modules_consumed": sorted(open_records) if records_by_module is None else [],
        "nfl_open_data_feature_availability": nfl_feature_availability if records_by_module is None else {},
        "normalized_schedule_result_shape": NORMALIZED_SCHEDULE_RESULT_SHAPE,
        "total_modules": len(modules),
        "total_feature_rows": len(feature_rows),
        "supported_feature_count": supported_total,
        "blocked_feature_count": blocked_total,
        "blocked_reason_counts": dict(sorted(blocked_reason_counts.items())),
        "current_best_tier_counts": dict(sorted(tier_counts.items())),
        "modules_ready_for_tier0_backfill": modules_ready_tier0,
        "modules_ready_for_tier1_derived_backfill": modules_ready_tier1,
        "modules_ready_for_real_tier0_backfill": modules_ready_real_tier0,
        "modules_ready_for_real_tier1_derived_backfill": modules_ready_real_tier1,
        "features_derivable_now": derivable_features,
        "features_blocked_by_insufficient_history": insufficient_history_features,
        "features_blocked_by_missing_fields": missing_field_features,
        "modules": modules,
        "provider_calls_attempted": 0,
        "provider_calls_succeeded": 0,
        "provider_calls_failed": 0,
        "enabled_source_count": 0,
        "paid_source_enabled_count": 0,
        "paid_action_blocked": True,
        "recommended_no_spend_next_step": "derive available fields from existing local compact reports and schedule/result history",
        "outcome_persistence_attempted": False,
        "import_or_persist_endpoint_called": False,
        "persisted_outcomes": False,
        "provider_write": False,
        "execution_allowed": False,
        "execution_allowed_count": 0,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "crypto_trade_execution_enabled": False,
        "stock_trade_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "actual_crypto_swaps_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
        "storage_health": get_storage_health(),
    }


def _root(base_data_dir: str | Path | None = None) -> Path:
    base = get_data_sources_dir() if base_data_dir is None else resolve_base_data_dir(base_data_dir) / "data_sources"
    path = base / "derived_features"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _rel(path: Path, base_data_dir: str | Path | None = None) -> str:
    root = resolve_base_data_dir(base_data_dir)
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return path.name


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


def render_derived_feature_markdown(report: dict[str, Any]) -> str:
    ready_tier0 = list(report.get("modules_ready_for_tier0_backfill") or [])
    ready_tier1 = list(report.get("modules_ready_for_tier1_derived_backfill") or [])
    ready_real_tier0 = list(report.get("modules_ready_for_real_tier0_backfill") or [])
    ready_real_tier1 = list(report.get("modules_ready_for_real_tier1_derived_backfill") or [])
    derivable = list(report.get("features_derivable_now") or [])
    insufficient = list(report.get("features_blocked_by_insufficient_history") or [])
    missing_fields = list(report.get("features_blocked_by_missing_fields") or [])
    nfl_open_data = dict(report.get("nfl_open_data_feature_availability") or {})
    lines = [
        "# Derived Feature Backfill Report",
        "",
        f"1. total_modules_scanned: {report.get('total_modules')}; feature_rows: {report.get('total_feature_rows')}",
        f"2. open_sports_history_real_rows_consumed: {report.get('open_sports_history_real_rows_consumed')}",
        f"3. open_sports_history_synthetic_rows_ignored: {report.get('open_sports_history_synthetic_rows_ignored')}",
        f"4. modules_ready_for_tier0: {', '.join(ready_tier0[:12]) if ready_tier0 else 'none'}",
        f"5. modules_ready_for_tier1: {', '.join(ready_tier1[:12]) if ready_tier1 else 'none'}",
        f"6. modules_ready_for_real_tier0: {', '.join(ready_real_tier0[:12]) if ready_real_tier0 else 'none'}",
        f"7. modules_ready_for_real_tier1: {', '.join(ready_real_tier1[:12]) if ready_real_tier1 else 'none'}",
        f"8. features_derivable_now: {', '.join(derivable) if derivable else 'none'}",
        f"9. features_blocked_by_insufficient_history: {', '.join(insufficient) if insufficient else 'none'}",
        f"10. features_blocked_by_missing_fields: {', '.join(missing_fields) if missing_fields else 'none'}",
        f"11. highest_value_next_no_spend_actions: {report.get('recommended_no_spend_next_step')}",
        "12. safety_status: provider_calls_attempted=0; enabled_source_count=0; paid_source_enabled_count=0; provider_write=false; execution_allowed=false; raw_payload_included=false; secrets_included=false",
        f"13. nfl_open_data_feature_availability: {json.dumps(nfl_open_data, sort_keys=True)}",
        "",
    ]
    return "\n".join(lines)


def write_derived_feature_backfill_report(
    report: dict[str, Any],
    *,
    base_data_dir: str | Path | None = None,
) -> dict[str, Any]:
    root = _root(base_data_dir)
    created = str(report.get("created_at") or utc_now_iso())
    day = created[:10]
    run_id = sanitize_filename(f"derived_features_{created.replace(':', '-')}_{uuid4().hex[:8]}")
    latest_json = root / "latest.json"
    latest_md = root / "latest.md"
    item_json = root / "items" / f"{run_id}.json"
    item_md = root / "items" / f"{run_id}.md"
    daily_json = root / "daily" / f"{day}.json"
    daily_md = root / "daily" / f"{day}.md"
    paths = {
        "latest_json_path": _rel(latest_json, base_data_dir),
        "latest_markdown_path": _rel(latest_md, base_data_dir),
        "item_json_path": _rel(item_json, base_data_dir),
        "item_markdown_path": _rel(item_md, base_data_dir),
        "daily_json_path": _rel(daily_json, base_data_dir),
        "daily_markdown_path": _rel(daily_md, base_data_dir),
    }
    payload = {**report, **paths, "raw_payload_included": False, "secrets_included": False}
    markdown = render_derived_feature_markdown(payload)
    _atomic_write_json(latest_json, payload)
    _atomic_write_text(latest_md, markdown)
    _atomic_write_json(item_json, payload)
    _atomic_write_text(item_md, markdown)
    _atomic_write_json(daily_json, payload)
    _atomic_write_text(daily_md, markdown)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default=None)
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    report = build_derived_feature_backfill_report(module=args.module)
    paths: dict[str, Any] = {}
    if args.persist:
        paths = write_derived_feature_backfill_report(report)
        report.update(paths)
    print(
        json.dumps(
            {
                "ok": report["ok"],
                "status": report["status"],
                "total_modules": report["total_modules"],
                "supported_feature_count": report["supported_feature_count"],
                "blocked_feature_count": report["blocked_feature_count"],
                "open_sports_history_real_rows_consumed": report.get("open_sports_history_real_rows_consumed"),
                "open_sports_history_synthetic_rows_ignored": report.get("open_sports_history_synthetic_rows_ignored"),
                "latest_json_path": paths.get("latest_json_path"),
                "latest_markdown_path": paths.get("latest_markdown_path"),
                "provider_calls_attempted": 0,
                "enabled_source_count": 0,
                "paid_source_enabled_count": 0,
                "provider_write": False,
                "execution_allowed": False,
                "raw_payload_included": False,
                "secrets_included": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

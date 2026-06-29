from __future__ import annotations

import argparse
import csv
import hashlib
import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any
from uuid import uuid4

from .data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from .open_sports_history_sources import SAFETY_FIELDS, source_by_id
from .scheduler_config import sanitize_filename, utc_now_iso


OPEN_SPORTS_HISTORY_IMPORT_SCHEMA_VERSION = "open_sports_history_import_v1"
DEFAULT_MAX_RECORDS = 25
HARD_MAX_RECORDS = 500

ALLOWED_BLOCKED_REASONS = {
    "available",
    "unsupported_source",
    "source_not_current_phase_allowed",
    "source_disabled",
    "paid_source_not_approved",
    "terms_review_required",
    "sports_reference_scraping_blocked",
    "missing_event_id",
    "missing_event_date",
    "missing_participants",
    "missing_scores_or_results",
    "nonnumeric_score",
    "raw_payload_risk",
    "secret_risk",
    "duplicate_record",
    "malformed_csv",
    "malformed_json",
    "unsupported_file_type",
    "no_records_found",
    "download_not_allowed",
    "unsupported_mode",
    "source_url_unverified",
    "source_timeout",
    "unsupported_file_shape",
    "provider_error",
    "source_error",
    "insufficient_fields",
    "source_not_available",
    "package_not_installed",
    "research_required",
}

RAW_PAYLOAD_KEYS = {
    "provider_payload",
    "raw_payload",
    "external_payload",
    "source_payload",
    "source_payload_redacted",
    "raw_provider_payload",
    "raw_kalshi_payload",
    "raw_sharp_payload",
    "response_payload",
    "raw_response",
}
SECRET_FIELD_MARKERS = (
    "api_key",
    "api_secret",
    "secret",
    "token",
    "password",
    "auth_header",
    "authorization",
    "credential",
    "signature",
    "private_key",
)
PLACEHOLDER_VALUES = {"", "n/a", "na", "none", "null", "unknown", "tbd", "placeholder"}
RECORD_LIST_KEYS = ("items", "records", "rows", "games", "events", "schedule", "results", "data")
POSTSEASON_GAME_TYPES = {"WC", "DIV", "CON", "SB"}
LABEL_ENRICHMENT_FIELDS = (
    "game_type",
    "season_type",
    "postseason_flag",
    "playoff_round",
    "source_label_fields_present",
)
LABEL_VALUE_FIELDS = (
    "game_type",
    "season_type",
    "postseason_flag",
    "playoff_round",
)

COMMON_ALIASES = {
    "event_id": ("event_id", "game_id", "GAME_ID", "gameid", "old_game_id", "gsis_id", "id"),
    "event_date": ("event_date", "date", "game_date", "Date", "GAME_DT", "gameday"),
    "home_participant": ("home_participant", "home_team", "home", "Home", "home_team_id", "HOME_TEAM_ID"),
    "away_participant": ("away_participant", "away_team", "away", "Away", "away_team_id", "AWAY_TEAM_ID"),
    "home_score": ("home_score", "home_points", "home_runs", "home_team_runs", "home_score_ct", "HOME_SCORE_CT", "home_score_final", "total_home_score"),
    "away_score": ("away_score", "away_points", "away_runs", "away_team_runs", "away_score_ct", "AWAY_SCORE_CT", "away_score_final", "total_away_score"),
    "week_or_round": ("week_or_round", "week", "round"),
    "season": ("season", "year"),
    "game_type": ("game_type", "season_type"),
    "winner": ("winner", "winning_team", "winning_participant"),
    "final_result": ("final_result", "result", "game_result", "outcome"),
    "neutral_site": ("neutral_site", "neutral"),
}

RETROSHEET_ALIASES = {
    **COMMON_ALIASES,
    "event_id": ("event_id", "game_id", "GAME_ID", "gameid", "id"),
    "event_date": ("event_date", "date", "game_date", "Date", "GAME_DT"),
    "home_participant": ("home_participant", "home_team", "home", "Home", "home_team_id", "HOME_TEAM_ID"),
    "away_participant": ("away_participant", "away_team", "away", "Away", "away_team_id", "AWAY_TEAM_ID"),
    "home_score": ("home_score", "home_runs", "home_team_runs", "home_score_ct", "HOME_SCORE_CT"),
    "away_score": ("away_score", "away_runs", "away_team_runs", "away_score_ct", "AWAY_SCORE_CT"),
}

NFLVERSE_ALIASES = {
    **COMMON_ALIASES,
    "event_id": ("event_id", "game_id", "old_game_id", "gsis_id"),
    "event_date": ("event_date", "game_date", "gameday", "date"),
    "home_participant": ("home_participant", "home_team", "home"),
    "away_participant": ("away_participant", "away_team", "away"),
    "home_score": ("home_score", "home_points", "home_score_final", "total_home_score"),
    "away_score": ("away_score", "away_points", "away_score_final", "total_away_score"),
    "week_or_round": ("week", "week_or_round"),
    "season": ("season",),
    "game_type": ("game_type", "season_type"),
}

SOURCE_ALIASES = {
    "retrosheet_mlb": RETROSHEET_ALIASES,
    "nflverse_nfl": NFLVERSE_ALIASES,
}

HTTP_TIMEOUT_SECONDS = 20
HTTP_USER_AGENT = "betting-stock-api-open-data-check"
NFLVERSE_RELEASE_TAG = "schedules"
NFLVERSE_RELEASE_API_URL = "https://api.github.com/repos/nflverse/nflverse-data/releases/tags/schedules"
NFLVERSE_RAW_GAMES_CSV_FALLBACK_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"


def _real_value(value: Any) -> bool:
    if value in (None, [], {}):
        return False
    if isinstance(value, str) and value.strip().lower() in PLACEHOLDER_VALUES:
        return False
    return True


def _safe_scalar(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return None


def _first_value(row: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in row and _real_value(row.get(key)):
            return _safe_scalar(row.get(key))
    return None


def _safe_number(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _compact_number(value: float | None) -> int | float | None:
    if value is None:
        return None
    return int(value) if float(value).is_integer() else value


def _record_hash(source_id: str, row: dict[str, Any]) -> str:
    safe = {
        str(key): value
        for key, value in row.items()
        if isinstance(value, (str, int, float, bool)) or value is None
    }
    text = json.dumps({"source_id": source_id, "row": safe}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def classify_open_data_source_url(url: str | None) -> dict[str, Any]:
    parsed = urllib.parse.urlparse(str(url or ""))
    host = parsed.netloc.lower()
    path = parsed.path
    if host == "github.com" and path.startswith(f"/nflverse/nflverse-data/releases/download/{NFLVERSE_RELEASE_TAG}/"):
        suffix = Path(path).suffix.lower().lstrip(".") or "unknown"
        return {
            "source_url_verified": True,
            "selected_source_url_kind": "nflverse_data_release_asset",
            "selected_source_host": host,
            "selected_release_tag": NFLVERSE_RELEASE_TAG,
            "selected_asset_format": suffix,
            "fallback_used": False,
            "url_resolution_blocker": None,
        }
    if host == "raw.githubusercontent.com" and path == "/nflverse/nfldata/master/data/games.csv":
        return {
            "source_url_verified": True,
            "selected_source_url_kind": "nflverse_nfldata_games_csv_fallback",
            "selected_source_host": host,
            "selected_release_tag": None,
            "selected_asset_format": "csv",
            "fallback_used": True,
            "url_resolution_blocker": None,
        }
    return {
        "source_url_verified": False,
        "selected_source_url_kind": "unverified_open_data_url",
        "selected_source_host": host or None,
        "selected_release_tag": None,
        "selected_asset_format": None,
        "fallback_used": False,
        "url_resolution_blocker": "source_url_unverified",
    }


def _urlopen_json(url: str, *, timeout: int = HTTP_TIMEOUT_SECONDS) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": HTTP_USER_AGENT,
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read(2_000_000).decode("utf-8", errors="replace")
    payload = json.loads(body)
    return payload if isinstance(payload, dict) else {}


def _timeout_error(exc: BaseException) -> bool:
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return True
    if isinstance(exc, urllib.error.URLError) and isinstance(getattr(exc, "reason", None), (TimeoutError, socket.timeout)):
        return True
    return "timed out" in str(exc).lower() or "timeout" in str(exc).lower()


def _compact_asset(asset: dict[str, Any]) -> dict[str, Any]:
    download_url = str(asset.get("browser_download_url") or "")
    classified = classify_open_data_source_url(download_url)
    return {
        **classified,
        "selected_asset_name": asset.get("name"),
        "selected_asset_format": classified.get("selected_asset_format") or Path(str(asset.get("name") or "")).suffix.lower().lstrip("."),
        "selected_asset_size": int(asset.get("size", 0) or 0),
    }


def _select_nflverse_schedule_asset(assets: list[Any]) -> dict[str, Any] | None:
    candidates = [asset for asset in assets if isinstance(asset, dict)]
    exact = [asset for asset in candidates if str(asset.get("name") or "").lower() == "games.csv"]
    if exact:
        return exact[0]
    csv_assets = [
        asset
        for asset in candidates
        if str(asset.get("name") or "").lower().endswith(".csv")
        and any(token in str(asset.get("name") or "").lower() for token in ("game", "schedule"))
    ]
    return csv_assets[0] if csv_assets else None


def _fallback_nflverse_resolution(
    blocker: str | None = None,
    *,
    provider_calls_attempted: int = 0,
    provider_calls_succeeded: int = 0,
) -> dict[str, Any]:
    classified = classify_open_data_source_url(NFLVERSE_RAW_GAMES_CSV_FALLBACK_URL)
    return {
        **classified,
        "selected_asset_name": "games.csv",
        "selected_asset_format": "csv",
        "source_file_or_ref": "nflverse_nfldata_games_csv_fallback:games.csv",
        "selected_release_tag": None,
        "provider_calls_attempted": provider_calls_attempted,
        "provider_calls_succeeded": provider_calls_succeeded,
        "provider_calls_failed": max(0, provider_calls_attempted - provider_calls_succeeded),
        "downloads_attempted": 0,
        "downloads_succeeded": 0,
        "raw_payload_included": False,
        "secrets_included": False,
        "url_resolution_blocker": blocker,
        "_download_url": NFLVERSE_RAW_GAMES_CSV_FALLBACK_URL,
    }


def resolve_nflverse_schedules_source(*, allow_fallback: bool = True, timeout: int = HTTP_TIMEOUT_SECONDS) -> dict[str, Any]:
    provider_calls_attempted = 1
    try:
        release = _urlopen_json(NFLVERSE_RELEASE_API_URL, timeout=timeout)
        asset = _select_nflverse_schedule_asset(list(release.get("assets") or []))
        if not asset:
            if allow_fallback:
                return _fallback_nflverse_resolution(
                    "source_not_available",
                    provider_calls_attempted=provider_calls_attempted,
                    provider_calls_succeeded=1,
                )
            return {
                "source_url_verified": False,
                "selected_source_url_kind": None,
                "selected_source_host": "api.github.com",
                "selected_release_tag": NFLVERSE_RELEASE_TAG,
                "selected_asset_name": None,
                "selected_asset_format": None,
                "fallback_used": False,
                "url_resolution_blocker": "source_not_available",
                "provider_calls_attempted": provider_calls_attempted,
                "provider_calls_succeeded": 1,
                "provider_calls_failed": 0,
                "downloads_attempted": 0,
                "downloads_succeeded": 0,
                "raw_payload_included": False,
                "secrets_included": False,
                "_download_url": None,
            }
        download_url = str(asset.get("browser_download_url") or "")
        compact = _compact_asset(asset)
        if not compact.get("source_url_verified"):
            if allow_fallback:
                return _fallback_nflverse_resolution(
                    "source_url_unverified",
                    provider_calls_attempted=provider_calls_attempted,
                    provider_calls_succeeded=1,
                )
            return {**compact, "provider_calls_attempted": provider_calls_attempted, "provider_calls_succeeded": 1, "provider_calls_failed": 0, "downloads_attempted": 0, "downloads_succeeded": 0, "raw_payload_included": False, "secrets_included": False, "_download_url": None}
        return {
            **compact,
            "source_file_or_ref": f"nflverse_data_release_asset:{asset.get('name')}",
            "provider_calls_attempted": provider_calls_attempted,
            "provider_calls_succeeded": 1,
            "provider_calls_failed": 0,
            "downloads_attempted": 0,
            "downloads_succeeded": 0,
            "raw_payload_included": False,
            "secrets_included": False,
            "_download_url": download_url,
        }
    except (json.JSONDecodeError, urllib.error.URLError, TimeoutError, socket.timeout, OSError) as exc:
        blocker = "source_timeout" if _timeout_error(exc) else "provider_error"
        if allow_fallback:
            return _fallback_nflverse_resolution(
                blocker,
                provider_calls_attempted=provider_calls_attempted,
                provider_calls_succeeded=0,
            )
        return {
            "source_url_verified": False,
            "selected_source_url_kind": None,
            "selected_source_host": "api.github.com",
            "selected_release_tag": NFLVERSE_RELEASE_TAG,
            "selected_asset_name": None,
            "selected_asset_format": None,
            "fallback_used": False,
            "url_resolution_blocker": blocker,
            "provider_calls_attempted": provider_calls_attempted,
            "provider_calls_succeeded": 0,
            "provider_calls_failed": provider_calls_attempted,
            "downloads_attempted": 0,
            "downloads_succeeded": 0,
            "raw_payload_included": False,
            "secrets_included": False,
            "_download_url": None,
        }


def _compact_resolution_for_report(resolution: dict[str, Any] | None) -> dict[str, Any]:
    safe = dict(resolution or {})
    safe.pop("_download_url", None)
    safe["raw_payload_included"] = False
    safe["secrets_included"] = False
    return safe


def _parse_event_date(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in PLACEHOLDER_VALUES:
        return None
    candidates = [
        "%Y-%m-%d",
        "%Y%m%d",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%m-%d-%Y",
    ]
    for fmt in candidates:
        try:
            return datetime.strptime(text[:10] if fmt == "%Y-%m-%d" else text, fmt).date().isoformat()
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return None


def _has_raw_payload_risk(value: Any, *, depth: int = 0) -> bool:
    if depth > 6:
        return False
    if isinstance(value, dict):
        for key, item in value.items():
            lower_key = str(key).lower()
            if lower_key in RAW_PAYLOAD_KEYS:
                return True
            if _has_raw_payload_risk(item, depth=depth + 1):
                return True
    if isinstance(value, list):
        return any(_has_raw_payload_risk(item, depth=depth + 1) for item in value[:100])
    return False


def _has_secret_risk(value: Any, *, depth: int = 0) -> bool:
    if depth > 6:
        return False
    if isinstance(value, dict):
        for key, item in value.items():
            lower_key = str(key).lower()
            if any(marker in lower_key for marker in SECRET_FIELD_MARKERS) and _real_value(item):
                return True
            if _has_secret_risk(item, depth=depth + 1):
                return True
    if isinstance(value, list):
        return any(_has_secret_risk(item, depth=depth + 1) for item in value[:100])
    return False


def _source_aliases(source_id: str) -> dict[str, tuple[str, ...]]:
    return SOURCE_ALIASES.get(source_id, COMMON_ALIASES)


def _derive_winner_and_result(
    *,
    home: Any,
    away: Any,
    home_score: float | None,
    away_score: float | None,
    explicit_winner: Any,
    explicit_result: Any,
) -> tuple[Any, Any, float | None, float | None]:
    final_margin = None
    total_score = None
    winner = explicit_winner
    result = explicit_result
    if home_score is None or away_score is None:
        return winner, result, final_margin, total_score
    final_margin = home_score - away_score
    total_score = home_score + away_score
    if not _real_value(winner):
        if home_score > away_score:
            winner = home
        elif away_score > home_score:
            winner = away
        else:
            winner = "draw"
    if not _real_value(result):
        if home_score > away_score:
            result = "home_win"
        elif away_score > home_score:
            result = "away_win"
        else:
            result = "draw"
    return winner, result, final_margin, total_score


def _clean_game_type(value: Any) -> str | None:
    text = str(value or "").strip().upper()
    return text if text else None


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


def _explicit_label_fields(safe: dict[str, Any], game_type: Any) -> dict[str, Any]:
    season_type = _first_value(safe, ("season_type",))
    postseason_flag = _first_value(safe, ("postseason_flag", "playoff_flag", "is_postseason", "is_playoff"))
    explicit_playoff_round = _first_value(safe, ("playoff_round", "postseason_round", "round_label"))
    cleaned_game_type = _clean_game_type(game_type)
    playoff_round = explicit_playoff_round
    if not _real_value(playoff_round) and cleaned_game_type in POSTSEASON_GAME_TYPES:
        playoff_round = cleaned_game_type
    source_label_fields_present = any(
        _real_value(value)
        for value in (
            game_type,
            season_type,
            postseason_flag,
            explicit_playoff_round,
        )
    )
    return {
        "season_type": season_type,
        "postseason_flag": _explicit_bool(postseason_flag),
        "playoff_round": playoff_round,
        "source_label_fields_present": bool(source_label_fields_present),
    }


def _empty_preview_row(
    *,
    module: str | None,
    source_id: str,
    season: int | str | None,
    source_file_or_ref: str | None,
    blocked_reason: str,
    data_kind: str = "synthetic_fixture",
    source_url_kind: str | None = None,
    source_verified_at: str | None = None,
) -> dict[str, Any]:
    if blocked_reason not in ALLOWED_BLOCKED_REASONS:
        blocked_reason = "insufficient_fields"
    return {
        "module": module,
        "source_id": source_id,
        "event_id": None,
        "event_date": None,
        "season": season,
        "week_or_round": None,
        "game_type": None,
        "home_participant": None,
        "away_participant": None,
        "neutral_site": None,
        "home_score": None,
        "away_score": None,
        "final_result": None,
        "winner": None,
        "final_margin": None,
        "total_score": None,
        "validation_status": "blocked",
        "blocked_reason": blocked_reason,
        "source_file_or_ref": source_file_or_ref,
        "source_record_hash": None,
        "data_kind": data_kind,
        "is_synthetic": data_kind != "real_open_data",
        "source_url_kind": source_url_kind,
        "source_verified_at": source_verified_at,
        "raw_payload_included": False,
    }


def _infer_data_kind(source_file_or_ref: str | None, allow_download: bool, downloads_succeeded: bool = False) -> str:
    """Infer whether data is synthetic_fixture or real_open_data.
    
    Synthetic: local test file in /imports/ directory
    Real: downloaded from URL or explicitly provided non-test file
    """
    if not source_file_or_ref:
        return "synthetic_fixture"
    source_path = str(source_file_or_ref).lower().replace("\\", "/")
    # Mark as synthetic if it's from test imports directory
    if "/imports/" in source_path:
        return "synthetic_fixture"
    # Mark as real if it was downloaded
    if allow_download and downloads_succeeded:
        return "real_open_data"
    # Mark as real if explicitly provided by user (not from downloads, not from test directory)
    if not allow_download and "/imports/" not in source_path:
        return "real_open_data"
    return "synthetic_fixture"


def normalize_open_sports_history_row(
    row: dict[str, Any],
    *,
    source_id: str,
    module: str,
    season: int | str | None = None,
    source_file_or_ref: str | None = None,
    data_kind: str = "synthetic_fixture",
    source_url_kind: str | None = None,
    source_verified_at: str | None = None,
) -> dict[str, Any]:
    aliases = _source_aliases(source_id)
    if _has_raw_payload_risk(row):
        return _empty_preview_row(
            module=module,
            source_id=source_id,
            season=season,
            source_file_or_ref=source_file_or_ref,
            blocked_reason="raw_payload_risk",
            data_kind=data_kind,
            source_url_kind=source_url_kind,
            source_verified_at=source_verified_at,
        )
    if _has_secret_risk(row):
        return _empty_preview_row(
            module=module,
            source_id=source_id,
            season=season,
            source_file_or_ref=source_file_or_ref,
            blocked_reason="secret_risk",
            data_kind=data_kind,
            source_url_kind=source_url_kind,
            source_verified_at=source_verified_at,
        )

    safe = {str(key): _safe_scalar(value) for key, value in row.items() if _safe_scalar(value) is not None}
    event_id = _first_value(safe, aliases["event_id"])
    raw_date = _first_value(safe, aliases["event_date"])
    event_date = _parse_event_date(raw_date)
    home = _first_value(safe, aliases["home_participant"])
    away = _first_value(safe, aliases["away_participant"])
    home_score_raw = _first_value(safe, aliases["home_score"])
    away_score_raw = _first_value(safe, aliases["away_score"])
    home_score = _safe_number(home_score_raw)
    away_score = _safe_number(away_score_raw)
    explicit_winner = _first_value(safe, aliases["winner"])
    explicit_result = _first_value(safe, aliases["final_result"])
    week = _first_value(safe, aliases["week_or_round"])
    game_type = _first_value(safe, aliases.get("game_type", ("game_type", "season_type")))
    label_fields = _explicit_label_fields(safe, game_type)
    row_season = _first_value(safe, aliases["season"]) or season
    if row_season is None and event_date:
        row_season = int(event_date[:4])

    if not _real_value(event_id):
        blocked_reason = "missing_event_id"
    elif event_date is None:
        blocked_reason = "missing_event_date"
    elif not (_real_value(home) and _real_value(away)):
        blocked_reason = "missing_participants"
    elif (_real_value(home_score_raw) and home_score is None) or (_real_value(away_score_raw) and away_score is None):
        blocked_reason = "nonnumeric_score"
    elif not ((home_score is not None and away_score is not None) or _real_value(explicit_result) or _real_value(explicit_winner)):
        blocked_reason = "missing_scores_or_results"
    else:
        blocked_reason = "available"

    winner, final_result, final_margin, total_score = _derive_winner_and_result(
        home=home,
        away=away,
        home_score=home_score,
        away_score=away_score,
        explicit_winner=explicit_winner,
        explicit_result=explicit_result,
    )
    validation_status = "available" if blocked_reason == "available" else "blocked"
    return {
        "module": module,
        "source_id": source_id,
        "event_id": event_id,
        "event_date": event_date,
        "season": row_season,
        "week_or_round": week,
        "game_type": game_type,
        "season_type": label_fields["season_type"],
        "postseason_flag": label_fields["postseason_flag"],
        "playoff_round": label_fields["playoff_round"],
        "source_label_fields_present": label_fields["source_label_fields_present"],
        "home_participant": home,
        "away_participant": away,
        "neutral_site": _first_value(safe, aliases["neutral_site"]),
        "home_score": _compact_number(home_score),
        "away_score": _compact_number(away_score),
        "final_result": final_result,
        "winner": winner,
        "final_margin": _compact_number(final_margin),
        "total_score": _compact_number(total_score),
        "validation_status": validation_status,
        "blocked_reason": blocked_reason,
        "source_file_or_ref": source_file_or_ref,
        "source_record_hash": _record_hash(source_id, safe),
        "raw_payload_included": False,
        "data_kind": data_kind,
        "is_synthetic": data_kind != "real_open_data",
        "source_url_kind": source_url_kind,
        "source_verified_at": source_verified_at,
    }


def _read_csv_rows(path: Path, max_records: int) -> tuple[list[dict[str, Any]], str | None]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                return [], "malformed_csv"
            return [dict(row) for _, row in zip(range(max_records), reader)], None
    except (OSError, UnicodeDecodeError, csv.Error):
        return [], "malformed_csv"


def _extract_json_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in RECORD_LIST_KEYS:
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
        return [payload]
    return []


def _read_json_rows(path: Path, max_records: int) -> tuple[list[dict[str, Any]], str | None]:
    try:
        if path.suffix.lower() in {".jsonl", ".ndjson"}:
            rows: list[dict[str, Any]] = []
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    parsed = json.loads(line)
                    if isinstance(parsed, dict):
                        rows.append(parsed)
                    if len(rows) >= max_records:
                        break
            return rows, None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return _extract_json_records(payload)[:max_records], None
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return [], "malformed_json"


def _read_parquet_rows(path: Path, max_records: int) -> tuple[list[dict[str, Any]], str | None]:
    try:
        import pandas as pd  # type: ignore
    except Exception:
        return [], "unsupported_file_type"
    try:
        frame = pd.read_parquet(path)
        return frame.head(max_records).to_dict(orient="records"), None
    except Exception:
        return [], "unsupported_file_type"


def _read_local_rows(pathish: str | Path, max_records: int) -> tuple[list[dict[str, Any]], str | None]:
    path = Path(pathish).expanduser()
    if not path.exists() or not path.is_file():
        return [], "no_records_found"
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _read_csv_rows(path, max_records)
    if suffix in {".json", ".jsonl", ".ndjson"}:
        return _read_json_rows(path, max_records)
    if suffix == ".parquet":
        return _read_parquet_rows(path, max_records)
    return [], "unsupported_file_type"


def validate_nflverse_schedule_columns(fieldnames: list[str] | tuple[str, ...] | None) -> tuple[bool, list[str]]:
    fields = {str(field) for field in (fieldnames or [])}
    aliases = NFLVERSE_ALIASES
    required_groups = {
        "event_id": aliases["event_id"],
        "event_date": aliases["event_date"],
        "season": aliases["season"],
        "home_participant": aliases["home_participant"],
        "away_participant": aliases["away_participant"],
        "home_score": aliases["home_score"],
        "away_score": aliases["away_score"],
    }
    missing = [canonical for canonical, candidates in required_groups.items() if not any(candidate in fields for candidate in candidates)]
    return not missing, missing


def _row_has_final_scores(row: dict[str, Any], *, source_id: str = "nflverse_nfl") -> bool:
    aliases = _source_aliases(source_id)
    home_score = _safe_number(_first_value(row, aliases.get("home_score", ("home_score",))))
    away_score = _safe_number(_first_value(row, aliases.get("away_score", ("away_score",))))
    return home_score is not None and away_score is not None


def build_nflverse_schedule_availability(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_season: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "rows": 0,
            "final_score_rows": 0,
            "missing_score_rows": 0,
            "game_types": Counter(),
            "min_event_date": None,
            "max_event_date": None,
        }
    )
    for row in rows:
        season = str(_season_value_for_row(row, "nflverse_nfl") or "").strip()
        if not season:
            continue
        item = by_season[season]
        item["rows"] += 1
        if _row_has_final_scores(row, source_id="nflverse_nfl"):
            item["final_score_rows"] += 1
        else:
            item["missing_score_rows"] += 1
        game_type = str(_first_value(row, NFLVERSE_ALIASES.get("game_type", ("game_type", "season_type"))) or "unknown")
        item["game_types"][game_type] += 1
        event_date = _parse_event_date(_first_value(row, NFLVERSE_ALIASES["event_date"]))
        if event_date:
            item["min_event_date"] = event_date if item["min_event_date"] is None or event_date < item["min_event_date"] else item["min_event_date"]
            item["max_event_date"] = event_date if item["max_event_date"] is None or event_date > item["max_event_date"] else item["max_event_date"]

    ordered_seasons = sorted(by_season, key=lambda value: int(value) if value.isdigit() else -1)
    completed = [
        season
        for season in ordered_seasons
        if int(by_season[season]["rows"] or 0) > 0 and int(by_season[season]["missing_score_rows"] or 0) == 0
    ]
    incomplete = [
        season
        for season in ordered_seasons
        if int(by_season[season]["missing_score_rows"] or 0) > 0
    ]
    seasons_with_final_scores = [
        season
        for season in ordered_seasons
        if int(by_season[season]["final_score_rows"] or 0) > 0
    ]
    season_status = {}
    for season in ordered_seasons:
        item = by_season[season]
        missing_score_rows = int(item["missing_score_rows"] or 0)
        rows_count = int(item["rows"] or 0)
        status = "complete_final_scores" if rows_count > 0 and missing_score_rows == 0 else "incomplete_or_future"
        season_status[season] = {
            "status": status,
            "rows": rows_count,
            "final_score_rows": int(item["final_score_rows"] or 0),
            "missing_score_rows": missing_score_rows,
            "game_types": dict(sorted(item["game_types"].items())),
            "min_event_date": item["min_event_date"],
            "max_event_date": item["max_event_date"],
        }
    return {
        "target_coverage_strategy": "all_available_completed_seasons",
        "earliest_available_season": completed[0] if completed else (ordered_seasons[0] if ordered_seasons else None),
        "latest_available_completed_season": completed[-1] if completed else None,
        "all_available_completed_seasons": completed,
        "seasons_available": completed,
        "seasons_with_final_scores": seasons_with_final_scores,
        "incomplete_or_future_seasons": incomplete,
        "source_completion_status": season_status,
        "source_completion_status_blocker": None if completed else "season_completion_status_unknown",
        "raw_payload_included": False,
        "secrets_included": False,
    }


def _season_value_for_row(row: dict[str, Any], source_id: str) -> Any:
    aliases = _source_aliases(source_id)
    return _first_value(row, aliases.get("season", ("season",)))


def _filter_rows_by_season(rows: list[dict[str, Any]], *, source_id: str, season: int | str | None, max_records: int) -> list[dict[str, Any]]:
    if season is None:
        return rows[:max_records]
    target = str(season)
    filtered = [row for row in rows if str(_season_value_for_row(row, source_id) or "") == target]
    return filtered[:max_records]


def download_official_open_data_file(
    *,
    source_id: str,
    season: int | str | None,
    max_records: int,
    timeout: int = HTTP_TIMEOUT_SECONDS,
) -> tuple[list[dict[str, Any]], str | None, dict[str, Any]]:
    if source_id != "nflverse_nfl":
        return [], "source_not_available", {
            "source_url_verified": False,
            "selected_source_url_kind": None,
            "selected_source_host": None,
            "selected_release_tag": None,
            "selected_asset_name": None,
            "selected_asset_format": None,
            "fallback_used": False,
            "url_resolution_blocker": "source_not_available",
            "provider_calls_attempted": 0,
            "downloads_attempted": 0,
            "downloads_succeeded": 0,
            "raw_payload_included": False,
            "secrets_included": False,
        }
    resolution = resolve_nflverse_schedules_source(allow_fallback=True, timeout=timeout)
    download_url = resolution.get("_download_url")
    if not resolution.get("source_url_verified") or not download_url:
        return [], str(resolution.get("url_resolution_blocker") or "source_url_unverified"), resolution
    try:
        request = urllib.request.Request(str(download_url), headers={"User-Agent": HTTP_USER_AGENT})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(8_000_000).decode("utf-8", errors="replace")
        reader = csv.DictReader(StringIO(body))
        if not reader.fieldnames:
            return [], "malformed_csv", {**resolution, "downloads_attempted": 1, "downloads_succeeded": 0}
        valid_shape, missing = validate_nflverse_schedule_columns(reader.fieldnames)
        if not valid_shape:
            return [], "unsupported_file_shape", {
                **resolution,
                "downloads_attempted": 1,
                "downloads_succeeded": 0,
                "missing_required_columns": missing,
            }
        all_rows = [dict(row) for row in reader]
        source_availability = build_nflverse_schedule_availability(all_rows)
        rows = _filter_rows_by_season(all_rows, source_id=source_id, season=season, max_records=max_records)
        if not rows:
            return [], "no_records_found", {
                **resolution,
                "downloads_attempted": 1,
                "downloads_succeeded": 1,
                "source_availability": source_availability,
            }
        return rows, None, {
            **resolution,
            "downloads_attempted": 1,
            "downloads_succeeded": 1,
            "source_availability": source_availability,
        }
    except (urllib.error.URLError, TimeoutError, socket.timeout, OSError, UnicodeDecodeError, csv.Error) as exc:
        blocker = "source_timeout" if _timeout_error(exc) else "provider_error"
        return [], blocker, {**resolution, "downloads_attempted": 1, "downloads_succeeded": 0}


def _download_rows(source_id: str, season: int | str | None, max_records: int) -> tuple[list[dict[str, Any]], str | None, dict[str, Any]]:
    return download_official_open_data_file(source_id=source_id, season=season, max_records=max_records)


def _effective_max_records(max_records: int | None) -> int:
    requested = DEFAULT_MAX_RECORDS if max_records is None else int(max_records)
    return max(1, min(requested, HARD_MAX_RECORDS))


def _source_gate(
    source: dict[str, Any] | None,
    *,
    source_id: str,
    allow_download: bool,
) -> str | None:
    if source is None:
        return "unsupported_source"
    if source_id == "sports_reference_manual_export" and allow_download:
        return "sports_reference_scraping_blocked"
    if source.get("future_paid_candidate") or source.get("requires_budget_approval"):
        return "paid_source_not_approved"
    if source.get("approval_status") == "research_required":
        return "research_required"
    if not source.get("current_phase_allowed") and source_id != "sports_reference_manual_export":
        return "source_not_current_phase_allowed"
    if source_id == "sports_reference_manual_export":
        return "terms_review_required"
    return None


def _dedupe_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    seen: set[tuple[str, str, str]] = set()
    out: list[dict[str, Any]] = []
    duplicates = 0
    for row in rows:
        if row.get("blocked_reason") != "available":
            out.append(row)
            continue
        key = (str(row.get("module") or ""), str(row.get("source_id") or ""), str(row.get("event_id") or ""))
        if key in seen:
            duplicates += 1
            out.append({**row, "validation_status": "blocked", "blocked_reason": "duplicate_record"})
            continue
        seen.add(key)
        out.append(row)
    return out, duplicates


def _count_reasons(rows: list[dict[str, Any]], fallback: str | None = None) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        reason = str(row.get("blocked_reason") or fallback or "available")
        counts[reason] = counts.get(reason, 0) + 1
    if not rows and fallback:
        counts[fallback] = 1
    return dict(sorted(counts.items()))


def build_open_sports_history_import_report(
    *,
    source_id: str,
    season: int | str | None = None,
    input_path: str | Path | None = None,
    max_records: int | None = None,
    dry_run: bool = True,
    allow_download: bool = False,
    persist_preview: bool = False,
    base_data_dir: str | Path | None = None,
) -> dict[str, Any]:
    source = source_by_id(source_id)
    effective_max = _effective_max_records(max_records)
    source_ref = str(input_path) if input_path else None
    gate_reason = _source_gate(source, source_id=source_id, allow_download=allow_download)
    rows_received: list[dict[str, Any]] = []
    read_error: str | None = None
    downloads_attempted = 0
    downloads_succeeded = 0
    provider_calls_attempted = 0
    source_resolution: dict[str, Any] = {
        "source_url_verified": False,
        "selected_source_url_kind": "local_file_import" if input_path else None,
        "selected_source_host": None,
        "selected_release_tag": None,
        "selected_asset_name": Path(str(input_path)).name if input_path else None,
        "selected_asset_format": Path(str(input_path)).suffix.lower().lstrip(".") if input_path else None,
        "fallback_used": False,
        "url_resolution_blocker": None,
        "provider_calls_attempted": 0,
        "downloads_attempted": 0,
        "downloads_succeeded": 0,
        "raw_payload_included": False,
        "secrets_included": False,
    }

    if gate_reason is None:
        if input_path:
            rows_received, read_error = _read_local_rows(input_path, effective_max)
        elif allow_download:
            if not source.get("supports_direct_download"):
                read_error = "download_not_allowed"
            else:
                rows_received, read_error, source_resolution = _download_rows(source_id, season, effective_max)
                downloads_attempted = int(source_resolution.get("downloads_attempted", 0) or 0)
                downloads_succeeded = int(source_resolution.get("downloads_succeeded", 0) or 0)
                provider_calls_attempted = int(source_resolution.get("provider_calls_attempted", 0) or 0)
                provider_calls_succeeded = int(source_resolution.get("provider_calls_succeeded", 0) or 0)
                provider_calls_failed = int(source_resolution.get("provider_calls_failed", 0) or 0)
                source_ref = str(source_resolution.get("source_file_or_ref") or source_resolution.get("selected_source_url_kind") or source_id)
        elif source_id.startswith("sportsdataverse_"):
            read_error = "package_not_installed"
        else:
            read_error = "download_not_allowed"
    else:
        read_error = gate_reason
    provider_calls_succeeded = int(source_resolution.get("provider_calls_succeeded", 0) or 0)
    provider_calls_failed = int(source_resolution.get("provider_calls_failed", 0) or 0)

    module = str((source or {}).get("module") or "")
    download_completed = downloads_attempted > 0 and downloads_succeeded > 0 and read_error is None
    data_kind = _infer_data_kind(source_ref, allow_download, download_completed)
    source_url_kind = str(source_resolution.get("selected_source_url_kind") or ("local_file_import" if input_path else "download_not_allowed"))
    source_verified_at = utc_now_iso() if (input_path or source_resolution.get("source_url_verified")) else None
    preview_rows: list[dict[str, Any]] = []
    if rows_received and read_error is None:
        preview_rows = [
            normalize_open_sports_history_row(
                row,
                source_id=source_id,
                module=module,
                season=season,
                source_file_or_ref=source_ref,
                data_kind=data_kind,
                source_url_kind=source_url_kind,
                source_verified_at=source_verified_at,
            )
            for row in rows_received[:effective_max]
        ]
        preview_rows, duplicate_count = _dedupe_rows(preview_rows)
    else:
        duplicate_count = 0

    if not rows_received and read_error is None:
        read_error = "no_records_found"
    if read_error and read_error not in ALLOWED_BLOCKED_REASONS:
        read_error = "insufficient_fields"

    valid_rows = [row for row in preview_rows if row.get("blocked_reason") == "available"]
    rejected_rows = [row for row in preview_rows if row.get("blocked_reason") != "available"]
    ok = gate_reason is None and read_error is None
    status = "preview_ready" if valid_rows else "blocked"
    if read_error in {"malformed_csv", "malformed_json", "unsupported_file_type"}:
        status = read_error
    elif read_error == "download_not_allowed":
        status = "download_blocked"
    elif read_error == "package_not_installed":
        status = "metadata_ready_no_source_configured"
    elif read_error == "source_not_available":
        status = "source_download_not_implemented"
    elif read_error in {"source_url_unverified", "source_timeout", "provider_error", "unsupported_file_shape"}:
        status = read_error

    return {
        **SAFETY_FIELDS,
        "ok": bool(ok or valid_rows),
        "status": status,
        "schema_version": OPEN_SPORTS_HISTORY_IMPORT_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "run_id": sanitize_filename(f"open_sports_history_validated_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
        "runtime_data_dir": str(resolve_base_data_dir(base_data_dir)),
        "source_id": source_id,
        "source_name": (source or {}).get("source_name"),
        "module": module or None,
        "source_access_type": (source or {}).get("source_access_type"),
        "approval_status": (source or {}).get("approval_status"),
        "source_enabled": bool((source or {}).get("enabled", False)),
        "season": season,
        "input_path": str(input_path) if input_path else None,
        "source_file_or_ref": source_ref,
        "source_url_resolution": _compact_resolution_for_report(source_resolution),
        **_compact_resolution_for_report(source_resolution),
        "source_verified_at": source_verified_at,
        "dry_run": bool(dry_run),
        "allow_download": bool(allow_download),
        "persist_preview": bool(persist_preview),
        "data_kind": data_kind,
        "is_synthetic": data_kind != "real_open_data",
        "max_records_requested": DEFAULT_MAX_RECORDS if max_records is None else int(max_records),
        "max_records_effective": effective_max,
        "records_received": len(rows_received),
        "preview_rows_created": len(valid_rows),
        "records_valid": len(valid_rows),
        "records_rejected": len(rejected_rows) + (1 if read_error and not preview_rows else 0),
        "duplicate_record_count": duplicate_count,
        "blocked_reason": read_error,
        "download_blocker": "source_download_not_implemented" if read_error == "source_not_available" and allow_download else None,
        "blocked_reason_counts": _count_reasons(preview_rows, read_error),
        "validated_preview_rows": valid_rows,
        "preview_rows": preview_rows,
        "rejected_preview_rows": rejected_rows[:50],
        "download_required": bool(not input_path and not allow_download),
        "downloads_attempted": downloads_attempted,
        "downloads_succeeded": downloads_succeeded,
        "provider_calls_attempted": provider_calls_attempted,
        "provider_calls_succeeded": provider_calls_succeeded,
        "provider_calls_failed": provider_calls_failed,
        "outcome_persistence_attempted": False,
        "import_or_persist_endpoint_called": False,
        "persisted_outcomes": False,
        "recommended_next_action": "persist compact preview rows with -PersistPreview after verifying the local fixture" if valid_rows and not persist_preview else "provide a local approved CSV fixture or explicitly pass -AllowDownload",
        "storage_health": get_storage_health(),
    }


def _report_root(base_data_dir: str | Path | None = None) -> Path:
    base = get_data_sources_dir() if base_data_dir is None else resolve_base_data_dir(base_data_dir) / "data_sources"
    root = base / "open_sports_history" / "validated"
    root.mkdir(parents=True, exist_ok=True)
    return root


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


def render_open_sports_history_import_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Open Sports History Import Preview",
        "",
        f"1. source_id: {report.get('source_id')}",
        f"2. module: {report.get('module')}",
        f"3. dry_run: {str(report.get('dry_run')).lower()}",
        f"4. allow_download: {str(report.get('allow_download')).lower()}",
        f"5. downloads_attempted: {report.get('downloads_attempted')}",
        f"6. records_received: {report.get('records_received')}",
        f"7. preview_rows_created: {report.get('preview_rows_created')}",
        f"8. blocked_reason_counts: {json.dumps(report.get('blocked_reason_counts') or {}, sort_keys=True)}",
        f"9. data_kind: {report.get('data_kind')}",
        f"10. source_url_kind: {report.get('selected_source_url_kind')}",
        f"11. safety: provider_calls_attempted={report.get('provider_calls_attempted', 0)}; provider_write=false; execution_allowed=false; raw_payload_included=false; secrets_included=false",
        "",
    ]
    return "\n".join(lines)


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _valid_preview_rows(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    candidates = payload.get("validated_preview_rows")
    if not isinstance(candidates, list):
        candidates = payload.get("preview_rows")
    rows: list[dict[str, Any]] = []
    for row in candidates or []:
        if not isinstance(row, dict):
            continue
        if row.get("raw_payload_included") is True:
            continue
        if row.get("blocked_reason") != "available" and row.get("validation_status") != "available":
            continue
        safe = {key: row.get(key) for key in COMPACT_ROW_FIELDS if key in row}
        safe["raw_payload_included"] = False
        rows.append(safe)
    return rows


COMPACT_ROW_FIELDS = (
    "module",
    "source_id",
    "event_id",
    "event_date",
    "season",
    "week_or_round",
    "game_type",
    "season_type",
    "postseason_flag",
    "playoff_round",
    "source_label_fields_present",
    "home_participant",
    "away_participant",
    "neutral_site",
    "home_score",
    "away_score",
    "final_result",
    "winner",
    "final_margin",
    "total_score",
    "validation_status",
    "blocked_reason",
    "source_file_or_ref",
    "source_record_hash",
    "raw_payload_included",
    "data_kind",
    "is_synthetic",
    "source_url_kind",
    "source_verified_at",
)


def _has_label_value(row: dict[str, Any]) -> bool:
    return any(_real_value(row.get(field)) for field in LABEL_VALUE_FIELDS)


def _merge_duplicate_validated_row(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = {field: existing.get(field) for field in COMPACT_ROW_FIELDS if field in existing}
    for field in LABEL_ENRICHMENT_FIELDS:
        if not _real_value(merged.get(field)) and _real_value(incoming.get(field)):
            merged[field] = incoming.get(field)
    if not _real_value(merged.get("source_url_kind")) and _real_value(incoming.get("source_url_kind")):
        merged["source_url_kind"] = incoming.get("source_url_kind")
    if not _real_value(merged.get("source_verified_at")) and _real_value(incoming.get("source_verified_at")):
        merged["source_verified_at"] = incoming.get("source_verified_at")
    if not _real_value(merged.get("source_record_hash")) and _real_value(incoming.get("source_record_hash")):
        merged["source_record_hash"] = incoming.get("source_record_hash")
    merged["source_label_fields_present"] = bool(_has_label_value(merged))
    merged["raw_payload_included"] = False
    return merged


def _dedupe_validated_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    out: list[dict[str, Any]] = []
    index_by_key: dict[tuple[str, str, str], int] = {}
    for row in rows:
        key = (str(row.get("module") or ""), str(row.get("source_id") or ""), str(row.get("event_id") or ""))
        if not key[2] or key in seen:
            if key in index_by_key:
                out[index_by_key[key]] = _merge_duplicate_validated_row(out[index_by_key[key]], row)
            continue
        seen.add(key)
        index_by_key[key] = len(out)
        compact = {field: row.get(field) for field in COMPACT_ROW_FIELDS if field in row}
        compact["source_label_fields_present"] = bool(_has_label_value(compact))
        compact["raw_payload_included"] = False
        out.append(compact)
    return out


def _validated_collection_payload(
    *,
    rows: list[dict[str, Any]],
    created: str,
    scope: str,
    scope_value: str,
    base_data_dir: str | Path | None,
) -> dict[str, Any]:
    modules = sorted({str(row.get("module")) for row in rows if row.get("module")})
    sources = sorted({str(row.get("source_id")) for row in rows if row.get("source_id")})
    seasons = sorted({str(row.get("season")) for row in rows if row.get("season") is not None})
    return {
        **SAFETY_FIELDS,
        "ok": True,
        "status": "ok",
        "schema_version": OPEN_SPORTS_HISTORY_IMPORT_SCHEMA_VERSION,
        "created_at": created,
        "runtime_data_dir": str(resolve_base_data_dir(base_data_dir)),
        "scope": scope,
        "scope_value": scope_value,
        "records_valid": len(rows),
        "preview_rows_created": len(rows),
        "validated_preview_rows": rows,
        "preview_rows": rows,
        "modules": modules,
        "sources": sources,
        "seasons": seasons,
        "provider_calls_attempted": 0,
        "downloads_attempted": 0,
        "outcome_persistence_attempted": False,
        "import_or_persist_endpoint_called": False,
        "persisted_outcomes": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def _merge_write_validated_collection(
    path: Path,
    *,
    incoming_rows: list[dict[str, Any]],
    created: str,
    scope: str,
    scope_value: str,
    base_data_dir: str | Path | None,
) -> dict[str, Any]:
    existing = _valid_preview_rows(_read_json(path))
    rows = _dedupe_validated_rows(existing + incoming_rows)
    payload = _validated_collection_payload(
        rows=rows,
        created=created,
        scope=scope,
        scope_value=scope_value,
        base_data_dir=base_data_dir,
    )
    _atomic_write_json(path, payload)
    return payload


def _write_grouped_validated_rows(
    *,
    root: Path,
    rows: list[dict[str, Any]],
    created: str,
    base_data_dir: str | Path | None,
) -> dict[str, Any]:
    paths: dict[str, Any] = {"by_source_paths": [], "by_module_paths": [], "by_season_paths": []}
    for source_id in sorted({str(row.get("source_id")) for row in rows if row.get("source_id")}):
        group = [row for row in rows if str(row.get("source_id")) == source_id]
        path = root / "by_source" / f"{sanitize_filename(source_id)}.json"
        _merge_write_validated_collection(path, incoming_rows=group, created=created, scope="source", scope_value=source_id, base_data_dir=base_data_dir)
        paths["by_source_paths"].append(_rel(path, base_data_dir))
    for module in sorted({str(row.get("module")) for row in rows if row.get("module")}):
        group = [row for row in rows if str(row.get("module")) == module]
        path = root / "by_module" / f"{sanitize_filename(module)}.json"
        _merge_write_validated_collection(path, incoming_rows=group, created=created, scope="module", scope_value=module, base_data_dir=base_data_dir)
        paths["by_module_paths"].append(_rel(path, base_data_dir))
        for season in sorted({str(row.get("season")) for row in group if row.get("season") is not None}):
            season_group = [row for row in group if str(row.get("season")) == season]
            season_path = root / "by_season" / sanitize_filename(module) / f"{sanitize_filename(season)}.json"
            _merge_write_validated_collection(
                season_path,
                incoming_rows=season_group,
                created=created,
                scope="module_season",
                scope_value=f"{module}:{season}",
                base_data_dir=base_data_dir,
            )
            paths["by_season_paths"].append(_rel(season_path, base_data_dir))
    return paths


def write_open_sports_history_import_report(
    report: dict[str, Any],
    *,
    base_data_dir: str | Path | None = None,
) -> dict[str, str]:
    root = _report_root(base_data_dir)
    created = str(report.get("created_at") or utc_now_iso())
    day = created[:10]
    run_id = sanitize_filename(str(report.get("run_id") or f"open_sports_history_validated_{created}_{uuid4().hex[:8]}"))
    latest_json = root / "latest.json"
    latest_md = root / "latest.md"
    item_json = root / "items" / f"{run_id}.json"
    item_md = root / "items" / f"{run_id}.md"
    daily_json = root / "daily" / f"{day}.json"
    daily_md = root / "daily" / f"{day}.md"
    paths: dict[str, Any] = {
        "latest_json_path": _rel(latest_json, base_data_dir),
        "latest_markdown_path": _rel(latest_md, base_data_dir),
        "item_json_path": _rel(item_json, base_data_dir),
        "item_markdown_path": _rel(item_md, base_data_dir),
        "daily_json_path": _rel(daily_json, base_data_dir),
        "daily_markdown_path": _rel(daily_md, base_data_dir),
    }
    payload = {**SAFETY_FIELDS, **report, **paths, "raw_payload_included": False, "secrets_included": False}
    markdown = render_open_sports_history_import_markdown(payload)
    _atomic_write_json(latest_json, payload)
    _atomic_write_text(latest_md, markdown)
    _atomic_write_json(item_json, payload)
    _atomic_write_text(item_md, markdown)
    _atomic_write_json(daily_json, payload)
    _atomic_write_text(daily_md, markdown)
    valid_rows = _valid_preview_rows(payload)
    if valid_rows:
        paths.update(_write_grouped_validated_rows(root=root, rows=valid_rows, created=created, base_data_dir=base_data_dir))
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--season", default=None)
    parser.add_argument("--input-path", default=None)
    parser.add_argument("--max-records", type=int, default=None)
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    parser.add_argument("--no-dry-run", dest="dry_run", action="store_false")
    parser.add_argument("--allow-download", action="store_true")
    parser.add_argument("--persist-preview", action="store_true")
    args = parser.parse_args(argv)

    report = build_open_sports_history_import_report(
        source_id=args.source_id,
        season=args.season,
        input_path=args.input_path,
        max_records=args.max_records,
        dry_run=args.dry_run,
        allow_download=args.allow_download,
        persist_preview=args.persist_preview,
    )
    paths: dict[str, str] = {}
    if args.persist_preview:
        paths = write_open_sports_history_import_report(report)
        report.update(paths)

    print(
        json.dumps(
            {
                "ok": report["ok"],
                "status": report["status"],
                "run_id": report["run_id"],
                "source_id": report["source_id"],
                "module": report["module"],
                "dry_run": report["dry_run"],
                "allow_download": report["allow_download"],
                "persist_preview": report["persist_preview"],
                "max_records_effective": report["max_records_effective"],
                "records_received": report["records_received"],
                "preview_rows_created": report["preview_rows_created"],
                "records_rejected": report["records_rejected"],
                "blocked_reason": report["blocked_reason"],
                "blocked_reason_counts": report["blocked_reason_counts"],
                "downloads_attempted": report["downloads_attempted"],
                "downloads_succeeded": report.get("downloads_succeeded", 0),
                "provider_calls_attempted": report.get("provider_calls_attempted", 0),
                "source_url_verified": report.get("source_url_verified"),
                "selected_source_url_kind": report.get("selected_source_url_kind"),
                "selected_source_host": report.get("selected_source_host"),
                "selected_release_tag": report.get("selected_release_tag"),
                "selected_asset_name": report.get("selected_asset_name"),
                "selected_asset_format": report.get("selected_asset_format"),
                "fallback_used": report.get("fallback_used"),
                "url_resolution_blocker": report.get("url_resolution_blocker"),
                "data_kind": report.get("data_kind"),
                "is_synthetic": report.get("is_synthetic"),
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

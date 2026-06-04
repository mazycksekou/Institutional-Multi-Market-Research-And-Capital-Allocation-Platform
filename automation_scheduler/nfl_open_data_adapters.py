from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from .data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from .nfl_open_data_sources import NFL_MODULE, nfl_open_data_sources, source_by_id
from .open_sports_history_sources import SAFETY_FIELDS
from .scheduler_config import sanitize_filename, utc_now_iso


NFL_OPEN_DATA_ADAPTER_SCHEMA_VERSION = "nfl_open_data_adapter_v1"
GITHUB_RELEASE_API_ROOT = "https://api.github.com/repos/nflverse/nflverse-data/releases/tags"
HTTP_TIMEOUT_SECONDS = 30
HTTP_USER_AGENT = "betting-stock-api-nfl-open-data-check"
DEFAULT_TINY_SAMPLE_RECORDS = 25
DEFAULT_ONE_SEASON = 2024
MAX_SAMPLE_ROWS_TO_PERSIST = 25

BLOCKED_REASONS = {
    "available",
    "download_not_allowed",
    "metadata_not_available",
    "terms_review_required",
    "source_not_current_phase_allowed",
    "source_not_available",
    "source_url_unverified",
    "source_timeout",
    "provider_error",
    "unsupported_source",
    "unsafe_source",
    "tiny_sample_required",
    "one_season_required",
    "unsupported_file_shape",
    "no_records_found",
    "field_shape_unverified",
    "sports_reference_scraping_blocked",
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
SECRET_MARKERS = ("api_key", "secret", "token", "password", "authorization", "auth_header", "cookie")


def _short_run_id(prefix: str, source_id: str) -> str:
    return sanitize_filename(f"nflod_{prefix}_{source_id}_{uuid4().hex[:8]}")

FIELD_HINTS: dict[str, list[str]] = {
    "schedules_results": [
        "game_id",
        "season",
        "week",
        "game_type",
        "gameday",
        "home_team",
        "away_team",
        "home_score",
        "away_score",
        "result",
        "total",
        "spread_line",
        "total_line",
        "roof",
        "surface",
        "temp",
        "wind",
        "stadium",
    ],
    "play_by_play": ["game_id", "play_id", "season", "week", "posteam", "defteam", "epa", "success", "yards_gained", "down", "ydstogo"],
    "team_stats": ["season", "week", "team", "opponent", "pass_att", "rush_att", "points", "yards"],
    "player_stats": ["season", "week", "player_id", "player_name", "recent_team", "position", "passing_yards", "rushing_yards", "receiving_yards"],
    "rosters": ["season", "team", "player_id", "gsis_id", "player_name", "position", "depth_team"],
    "weekly_rosters": ["season", "week", "team", "player_id", "gsis_id", "player_name", "position"],
    "snap_counts": ["season", "week", "team", "player", "player_id", "offense_snaps", "defense_snaps", "st_snaps"],
    "participation": ["season", "game_id", "play_id", "team", "players_on_field"],
    "depth_charts": ["season", "week", "team", "depth_team", "formation", "depth_position", "player_name", "gsis_id"],
    "injuries": ["season", "week", "team", "player_id", "gsis_id", "full_name", "report_status", "practice_status"],
    "transactions": ["season", "team", "player_id", "player_name", "trade_date"],
    "draft": ["season", "round", "pick", "team", "player_id", "pfr_id", "player_name", "position"],
    "combine": ["season", "player_name", "pfr_id", "position", "forty", "bench", "vertical", "broad_jump"],
    "officials": ["game_id", "official_name", "official_id", "position"],
    "stadiums": ["game_id", "season", "stadium", "roof", "surface", "home_team"],
    "weather": ["game_id", "season", "weather", "temp", "wind", "roof", "surface"],
    "betting_lines_or_market_odds": ["game_id", "season", "spread_line", "total_line", "div_game", "home_moneyline", "away_moneyline"],
    "advanced_efficiency": ["season", "player_id", "team_abbr", "player_display_name", "avg_speed", "avg_separation"],
    "pace_or_play_volume": ["season", "game_id", "posteam", "defteam", "play_id", "half_seconds_remaining", "game_seconds_remaining"],
    "roster_continuity": ["season", "week", "team", "player_id", "gsis_id", "position", "status"],
    "coaching": ["season", "team", "coach_id", "coach_name", "role"],
}


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


def _rel(path: Path, base_data_dir: str | Path | None = None) -> str:
    root = resolve_base_data_dir(base_data_dir)
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return path.name


def _url_request(url: str, *, accept_json: bool = False) -> urllib.request.Request:
    headers = {"User-Agent": HTTP_USER_AGENT}
    if accept_json:
        headers["Accept"] = "application/vnd.github+json"
    return urllib.request.Request(url, headers=headers)


def _urlopen_json(url: str, *, timeout: int = HTTP_TIMEOUT_SECONDS) -> dict[str, Any]:
    with urllib.request.urlopen(_url_request(url, accept_json=True), timeout=timeout) as response:
        body = response.read(4_000_000).decode("utf-8", errors="replace")
    payload = json.loads(body)
    return payload if isinstance(payload, dict) else {}


def _timeout_error(exc: BaseException) -> bool:
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return True
    if isinstance(exc, urllib.error.URLError) and isinstance(getattr(exc, "reason", None), (TimeoutError, socket.timeout)):
        return True
    return "timed out" in str(exc).lower() or "timeout" in str(exc).lower()


def _classify_release_asset_url(url: str | None, *, release_tag: str | None) -> dict[str, Any]:
    parsed = urllib.parse.urlparse(str(url or ""))
    host = parsed.netloc.lower()
    path = parsed.path
    expected_prefix = f"/nflverse/nflverse-data/releases/download/{release_tag}/" if release_tag else ""
    if host == "github.com" and release_tag and path.startswith(expected_prefix):
        suffixes = Path(path).suffixes
        fmt = "csv.gz" if suffixes[-2:] == [".csv", ".gz"] else (suffixes[-1].lstrip(".") if suffixes else "unknown")
        return {
            "source_url_verified": True,
            "source_url_kind": "nflverse_data_release_asset",
            "host": host,
            "release_tag_or_ref": release_tag,
            "file_format": fmt,
            "url_blocker": None,
        }
    return {
        "source_url_verified": False,
        "source_url_kind": "unverified_open_data_url",
        "host": host or None,
        "release_tag_or_ref": release_tag,
        "file_format": None,
        "url_blocker": "source_url_unverified",
    }


def _compact_asset(asset: dict[str, Any], *, release_tag: str | None) -> dict[str, Any]:
    name = str(asset.get("name") or "")
    download_url = str(asset.get("browser_download_url") or "")
    classified = _classify_release_asset_url(download_url, release_tag=release_tag)
    season = _season_from_asset_name(name)
    return {
        **classified,
        "asset_name_or_dataset_ref": name,
        "asset_size": int(asset.get("size", 0) or 0),
        "season": season,
        "_download_url": download_url if classified["source_url_verified"] else None,
    }


def _public_asset(asset: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in asset.items() if not key.startswith("_")}


def _season_from_asset_name(name: str) -> str | None:
    match = re.search(r"(?:^|_)(19\d{2}|20\d{2})(?:_|\.|$)", name)
    return match.group(1) if match else None


def _format_rank(name: str, *, prefer_csv_gz: bool = True) -> int:
    lower = name.lower()
    if prefer_csv_gz:
        if lower.endswith(".csv.gz"):
            return 0
        if lower.endswith(".csv"):
            return 1
    else:
        if lower.endswith(".csv"):
            return 0
        if lower.endswith(".csv.gz"):
            return 1
    if lower.endswith(".parquet"):
        return 2
    if lower.endswith(".rds"):
        return 3
    if lower.endswith(".qs"):
        return 4
    return 9


def _is_csv_asset(name: str) -> bool:
    lower = name.lower()
    return lower.endswith(".csv") or lower.endswith(".csv.gz")


def _safe_scalar(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return None


def _has_raw_or_secret_risk(row: dict[str, Any]) -> bool:
    for key, value in row.items():
        lower = str(key).lower()
        if lower in RAW_PAYLOAD_KEYS:
            return True
        if any(marker in lower for marker in SECRET_MARKERS) and str(value or "").strip():
            return True
    return False


def _record_hash(source_id: str, row: dict[str, Any], index: int) -> str:
    safe = {
        str(key): _safe_scalar(value)
        for key, value in row.items()
        if isinstance(value, (str, int, float, bool)) or value is None
    }
    text = json.dumps({"source_id": source_id, "index": index, "row": safe}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _first_value(row: dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return _safe_scalar(value)
    return None


def _compact_record(
    row: dict[str, Any],
    *,
    source: dict[str, Any],
    asset_name: str | None,
    row_index: int,
) -> dict[str, Any]:
    source_id = str(source["source_id"])
    data_category = str(source["data_category"])
    safe = {str(key): _safe_scalar(value) for key, value in row.items() if isinstance(value, (str, int, float, bool)) or value is None}
    season = _first_value(safe, ("season", "year", "draft_year")) or _season_from_asset_name(str(asset_name or ""))
    week = _first_value(safe, ("week", "game_week"))
    team = _first_value(safe, ("team", "recent_team", "team_abbr", "club_code", "posteam", "defteam", "home_team"))
    player_id = _first_value(safe, ("player_id", "gsis_id", "player_gsis_id", "pfr_id", "esb_id", "smart_id"))
    game_id = _first_value(safe, ("game_id", "old_game_id", "gsis_id"))
    record_id = _first_value(safe, ("play_id", "record_id", "official_id")) or _record_hash(source_id, safe, row_index)[:16]
    keep_keys = [
        "game_id",
        "play_id",
        "season",
        "week",
        "team",
        "recent_team",
        "home_team",
        "away_team",
        "posteam",
        "defteam",
        "player_id",
        "gsis_id",
        "pfr_id",
        "player_name",
        "player_display_name",
        "position",
        "depth_position",
        "report_status",
        "practice_status",
        "injury_report_status",
        "offense_snaps",
        "defense_snaps",
        "st_snaps",
        "epa",
        "success",
        "yards_gained",
        "spread_line",
        "total_line",
        "home_moneyline",
        "away_moneyline",
        "stadium",
        "roof",
        "surface",
        "temp",
        "wind",
        "weather",
    ]
    compact = {
        "module": NFL_MODULE,
        "source_id": source_id,
        "source_family": source.get("source_family"),
        "data_category": data_category,
        "asset_name_or_dataset_ref": asset_name,
        "record_id": str(record_id),
        "season": str(season) if season is not None else None,
        "week": str(week) if week is not None else None,
        "team": str(team) if team is not None else None,
        "player_id": str(player_id) if player_id is not None else None,
        "game_id": str(game_id) if game_id is not None else None,
        "validation_status": "available",
        "blocked_reason": "available",
        "data_kind": "real_open_data",
        "is_synthetic": False,
        "raw_payload_included": False,
    }
    for key in keep_keys:
        if key in safe and safe[key] not in (None, ""):
            compact[key] = safe[key]
    return compact


def _open_csv_response(url: str, *, timeout: int = HTTP_TIMEOUT_SECONDS):
    response = urllib.request.urlopen(_url_request(url), timeout=timeout)
    if url.lower().endswith(".gz"):
        binary = gzip.GzipFile(fileobj=response)
    else:
        binary = response
    text = io.TextIOWrapper(binary, encoding="utf-8", errors="replace", newline="")
    return response, text


def _iter_csv_rows_from_url(url: str, *, max_records: int | None = None) -> tuple[list[str], list[dict[str, Any]], int]:
    response, text = _open_csv_response(url)
    try:
        reader = csv.DictReader(text)
        fields = list(reader.fieldnames or [])
        sample: list[dict[str, Any]] = []
        total = 0
        for row in reader:
            total += 1
            if max_records is None or len(sample) < max_records:
                sample.append(dict(row))
        return fields, sample, total
    finally:
        try:
            text.close()
        except Exception:
            pass
        try:
            response.close()
        except Exception:
            pass


def _field_type(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if value in (None, ""):
        return "unknown"
    text = str(value)
    try:
        int(text)
        return "integer"
    except ValueError:
        pass
    try:
        float(text)
        return "number"
    except ValueError:
        return "string"


@dataclass
class NflOpenDataAdapter:
    source: dict[str, Any]

    def describe_source(self) -> dict[str, Any]:
        return {**self.source, "provider_write": False, "execution_allowed": False}

    def list_expected_fields(self) -> list[str]:
        return list(FIELD_HINTS.get(str(self.source.get("data_category")), []))

    def resolve_source_metadata(self) -> dict[str, Any]:
        if not self.source.get("release_tag"):
            return self._blocked_metadata("metadata_not_available", provider_calls_attempted=0)
        provider_calls_attempted = 1
        try:
            release = _urlopen_json(f"{GITHUB_RELEASE_API_ROOT}/{self.source['release_tag']}")
            assets = [
                _compact_asset(asset, release_tag=str(self.source["release_tag"]))
                for asset in list(release.get("assets") or [])
                if isinstance(asset, dict)
            ]
            selected = self._select_assets(assets)
            seasons = sorted({str(asset["season"]) for asset in selected if asset.get("season")})
            formats = sorted({str(asset.get("file_format")) for asset in selected if asset.get("file_format")})
            status = "metadata_ready" if selected else "metadata_ready_no_matching_csv_asset"
            blocker = None if selected else "source_not_available"
            return {
                **SAFETY_FIELDS,
                "ok": bool(selected),
                "status": status,
                "blocked_reason": blocker,
                "source_id": self.source["source_id"],
                "source_name": self.source.get("source_name"),
                "source_family": self.source.get("source_family"),
                "data_category": self.source.get("data_category"),
                "module": NFL_MODULE,
                "source_url_kind": "github_release_metadata",
                "host": "api.github.com",
                "release_tag_or_ref": self.source.get("release_tag"),
                "asset_count": len(assets),
                "matching_asset_count": len(selected),
                "assets": [_public_asset(asset) for asset in selected[:200]],
                "_assets_private": selected,
                "file_formats": formats,
                "seasons_available": seasons,
                "row_granularity": self.source.get("expected_granularity"),
                "join_keys": self.source.get("expected_join_keys") or [],
                "field_count": None,
                "sample_allowed": bool(self.source.get("current_phase_allowed") and self.source.get("live_download_supported")),
                "full_backfill_allowed": bool(self.source.get("current_phase_allowed") and self.source.get("live_download_supported")),
                "provider_calls_attempted": provider_calls_attempted,
                "provider_calls_succeeded": 1,
                "provider_calls_failed": 0,
                "downloads_attempted": 0,
                "downloads_succeeded": 0,
                "raw_payload_included": False,
                "secrets_included": False,
            }
        except (json.JSONDecodeError, urllib.error.URLError, TimeoutError, socket.timeout, OSError) as exc:
            blocker = "source_timeout" if _timeout_error(exc) else "provider_error"
            return self._blocked_metadata(blocker, provider_calls_attempted=provider_calls_attempted)

    def run_tiny_sample(self, *, allow_download: bool = False, max_records: int = DEFAULT_TINY_SAMPLE_RECORDS) -> dict[str, Any]:
        if not allow_download:
            return self._blocked_report("tiny_sample", "download_not_allowed")
        gate = self._source_gate()
        if gate:
            return self._blocked_report("tiny_sample", gate)
        metadata = self.resolve_source_metadata()
        if not metadata.get("ok"):
            return self._blocked_report("tiny_sample", str(metadata.get("blocked_reason") or "metadata_not_available"), metadata=metadata)
        assets = self._select_assets_with_private(metadata)
        target = assets[-1:]
        return self._download_assets(
            "tiny_sample",
            target,
            max_records=max(1, min(int(max_records or DEFAULT_TINY_SAMPLE_RECORDS), DEFAULT_TINY_SAMPLE_RECORDS)),
            metadata=metadata,
        )

    def run_one_season_import(
        self,
        *,
        season: int | str = DEFAULT_ONE_SEASON,
        allow_download: bool = False,
        tiny_sample_passed: bool = False,
        safe_override: bool = False,
    ) -> dict[str, Any]:
        if not allow_download:
            return self._blocked_report("one_season_import", "download_not_allowed", season=season)
        if not tiny_sample_passed and not safe_override:
            return self._blocked_report("one_season_import", "tiny_sample_required", season=season)
        gate = self._source_gate()
        if gate:
            return self._blocked_report("one_season_import", gate, season=season)
        metadata = self.resolve_source_metadata()
        if not metadata.get("ok"):
            return self._blocked_report("one_season_import", str(metadata.get("blocked_reason") or "metadata_not_available"), season=season, metadata=metadata)
        selected = self._assets_for_season(self._select_assets_with_private(metadata), str(season))
        if not selected:
            return self._blocked_report("one_season_import", "source_not_available", season=season, metadata=metadata)
        return self._download_assets("one_season_import", selected, max_records=None, metadata=metadata, season=season)

    def run_full_available_backfill(
        self,
        *,
        allow_download: bool = False,
        one_season_passed: bool = False,
        max_full_assets: int | None = None,
    ) -> dict[str, Any]:
        if not allow_download:
            return self._blocked_report("full_available_backfill", "download_not_allowed")
        if not one_season_passed:
            return self._blocked_report("full_available_backfill", "one_season_required")
        gate = self._source_gate()
        if gate:
            return self._blocked_report("full_available_backfill", gate)
        metadata = self.resolve_source_metadata()
        if not metadata.get("ok"):
            return self._blocked_report("full_available_backfill", str(metadata.get("blocked_reason") or "metadata_not_available"), metadata=metadata)
        assets = self._select_assets_with_private(metadata)
        bounded = False
        if self.source.get("large_source") and max_full_assets is None:
            max_full_assets = 2
        if max_full_assets is not None and max_full_assets > 0 and len(assets) > max_full_assets:
            bounded = True
            assets = assets[-max_full_assets:]
        report = self._download_assets("full_available_backfill", assets, max_records=None, metadata=metadata)
        if bounded:
            report["status"] = "partial_backfill_session_complete" if report.get("ok") else report.get("status")
            report["full_backfill_status"] = "partial_bounded_session"
            report["next_recommended_session"] = "resume full_available_backfill with a larger max_full_assets value after reviewing runtime"
        return report

    def validate_sample_shape(self, rows: list[dict[str, Any]], fields: list[str]) -> dict[str, Any]:
        hints = set(self.list_expected_fields())
        available = set(fields)
        join_keys = set(str(key) for key in self.source.get("expected_join_keys") or [])
        known_overlap = sorted(hints & available)
        join_overlap = sorted(join_keys & available)
        ok = bool(rows) and (bool(known_overlap) or bool(join_overlap) or not hints)
        return {
            "ok": ok,
            "status": "shape_validated" if ok else "field_shape_unverified",
            "field_count": len(fields),
            "fields_available": sorted(available),
            "known_field_overlap": known_overlap,
            "join_keys_available": join_overlap,
            "blocked_reason": None if ok else "field_shape_unverified",
        }

    def normalize_records(self, rows: list[dict[str, Any]], *, asset_name: str | None = None) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for index, row in enumerate(rows):
            if _has_raw_or_secret_risk(row):
                continue
            out.append(_compact_record(row, source=self.source, asset_name=asset_name, row_index=index))
        return out

    def write_compact_validated_rows(
        self,
        report: dict[str, Any],
        *,
        base_data_dir: str | Path | None = None,
    ) -> dict[str, Any]:
        root = _validated_root(self.source["source_id"], base_data_dir)
        created = str(report.get("created_at") or utc_now_iso())
        run_id = sanitize_filename(str(report.get("run_id") or f"nfl_open_data_validated_{created}_{uuid4().hex[:8]}"))
        latest_json = root / "latest.json"
        latest_md = root / "latest.md"
        item_json = root / "items" / f"{run_id}.json"
        by_season_paths: list[str] = []
        by_team_paths: list[str] = []
        by_player_paths: list[str] = []
        payload = {**SAFETY_FIELDS, **report, "raw_payload_included": False, "secrets_included": False}
        _atomic_write_json(latest_json, payload)
        _atomic_write_text(latest_md, render_adapter_markdown(payload))
        _atomic_write_json(item_json, payload)
        by_season: dict[str, list[dict[str, Any]]] = defaultdict(list)
        by_team: dict[str, list[dict[str, Any]]] = defaultdict(list)
        by_player: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in list(report.get("sample_rows") or [])[:MAX_SAMPLE_ROWS_TO_PERSIST]:
            if not isinstance(row, dict):
                continue
            season = str(row.get("season") or "unknown")
            by_season[season].append(row)
            if row.get("team"):
                by_team[str(row["team"])].append(row)
            if row.get("player_id"):
                by_player[str(row["player_id"])].append(row)
        for season, rows in sorted(by_season.items()):
            path = root / "by_season" / f"{sanitize_filename(season)}.json"
            _atomic_write_json(path, _collection_payload(report, rows, scope="season", scope_value=season))
            by_season_paths.append(_rel(path, base_data_dir))
        for team, rows in sorted(by_team.items()):
            path = root / "by_team" / f"{sanitize_filename(team)}.json"
            _atomic_write_json(path, _collection_payload(report, rows, scope="team", scope_value=team))
            by_team_paths.append(_rel(path, base_data_dir))
        for player_id, rows in sorted(by_player.items()):
            path = root / "by_player" / f"{sanitize_filename(player_id)}.json"
            _atomic_write_json(path, _collection_payload(report, rows, scope="player", scope_value=player_id))
            by_player_paths.append(_rel(path, base_data_dir))
        paths = {
            "latest_json_path": _rel(latest_json, base_data_dir),
            "latest_markdown_path": _rel(latest_md, base_data_dir),
            "item_json_path": _rel(item_json, base_data_dir),
            "by_season_paths": by_season_paths,
            "by_team_paths": by_team_paths,
            "by_player_paths": by_player_paths,
        }
        report.update(paths)
        _atomic_write_json(latest_json, {**payload, **paths})
        return paths

    def build_compact_report(self) -> dict[str, Any]:
        metadata = self.resolve_source_metadata()
        return {
            **SAFETY_FIELDS,
            "ok": bool(metadata.get("ok")),
            "status": metadata.get("status"),
            "schema_version": NFL_OPEN_DATA_ADAPTER_SCHEMA_VERSION,
            "created_at": utc_now_iso(),
            "run_id": _short_run_id("adapter", str(self.source["source_id"])),
            "source": self.describe_source(),
            "metadata": {key: value for key, value in metadata.items() if key != "assets"},
            "expected_fields": self.list_expected_fields(),
            "provider_calls_attempted": int(metadata.get("provider_calls_attempted", 0) or 0),
            "provider_calls_succeeded": int(metadata.get("provider_calls_succeeded", 0) or 0),
            "provider_calls_failed": int(metadata.get("provider_calls_failed", 0) or 0),
            "downloads_attempted": 0,
            "downloads_succeeded": 0,
            "provider_write": False,
            "execution_allowed": False,
            "raw_payload_included": False,
            "secrets_included": False,
        }

    def _source_gate(self) -> str | None:
        if self.source.get("requires_auth") or self.source.get("requires_api_key"):
            return "unsafe_source"
        if self.source.get("future_paid_candidate") or self.source.get("requires_budget_approval"):
            return "unsafe_source"
        if self.source.get("approval_status") == "terms_review_required" or str(self.source.get("terms_review_status") or "").endswith("required"):
            return "terms_review_required"
        if self.source["source_id"].lower().find("pfr") >= 0:
            return "sports_reference_scraping_blocked"
        if not self.source.get("current_phase_allowed") or not self.source.get("live_download_supported"):
            return "source_not_current_phase_allowed"
        return None

    def _blocked_metadata(self, blocker: str, *, provider_calls_attempted: int) -> dict[str, Any]:
        return {
            **SAFETY_FIELDS,
            "ok": False,
            "status": "blocked",
            "blocked_reason": blocker if blocker in BLOCKED_REASONS else "metadata_not_available",
            "source_id": self.source["source_id"],
            "source_name": self.source.get("source_name"),
            "source_family": self.source.get("source_family"),
            "data_category": self.source.get("data_category"),
            "module": NFL_MODULE,
            "host": "api.github.com" if provider_calls_attempted else None,
            "release_tag_or_ref": self.source.get("release_tag"),
            "asset_count": 0,
            "matching_asset_count": 0,
            "assets": [],
            "seasons_available": [],
            "row_granularity": self.source.get("expected_granularity"),
            "join_keys": self.source.get("expected_join_keys") or [],
            "field_count": None,
            "sample_allowed": False,
            "full_backfill_allowed": False,
            "provider_calls_attempted": provider_calls_attempted,
            "provider_calls_succeeded": 0,
            "provider_calls_failed": provider_calls_attempted,
            "downloads_attempted": 0,
            "downloads_succeeded": 0,
            "raw_payload_included": False,
            "secrets_included": False,
        }

    def _blocked_report(
        self,
        gate: str,
        blocker: str,
        *,
        season: int | str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            **SAFETY_FIELDS,
            "ok": False,
            "status": "blocked",
            "schema_version": NFL_OPEN_DATA_ADAPTER_SCHEMA_VERSION,
            "created_at": utc_now_iso(),
            "run_id": _short_run_id(gate, str(self.source["source_id"])),
            "source_id": self.source["source_id"],
            "source_name": self.source.get("source_name"),
            "source_family": self.source.get("source_family"),
            "data_category": self.source.get("data_category"),
            "module": NFL_MODULE,
            "gate": gate,
            "season": str(season) if season is not None else None,
            "blocked_reason": blocker if blocker in BLOCKED_REASONS else "unsupported_source",
            "metadata": _safe_metadata(metadata),
            "records_validated": 0,
            "records_rejected": 0,
            "sample_rows": [],
            "fields_available": [],
            "field_count": 0,
            "seasons_available": list((metadata or {}).get("seasons_available") or []),
            "seasons_backfilled": [],
            "downloads_attempted": int((metadata or {}).get("downloads_attempted", 0) or 0),
            "downloads_succeeded": int((metadata or {}).get("downloads_succeeded", 0) or 0),
            "provider_calls_attempted": int((metadata or {}).get("provider_calls_attempted", 0) or 0),
            "provider_calls_succeeded": int((metadata or {}).get("provider_calls_succeeded", 0) or 0),
            "provider_calls_failed": int((metadata or {}).get("provider_calls_failed", 0) or 0),
            "provider_write": False,
            "execution_allowed": False,
            "raw_payload_included": False,
            "secrets_included": False,
            "next_safe_action": "resolve blocker before attempting downloads",
            "storage_health": get_storage_health(),
        }

    def _select_assets(self, assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not assets:
            return []
        exact = str(self.source.get("asset_name") or "")
        prefix = str(self.source.get("asset_prefix") or "")
        regex = self.source.get("asset_regex")
        prefer_csv_gz = bool(self.source.get("prefer_csv_gz", True))
        candidates = [asset for asset in assets if _is_csv_asset(str(asset.get("asset_name_or_dataset_ref") or ""))]
        if exact:
            candidates = [asset for asset in candidates if str(asset.get("asset_name_or_dataset_ref") or "").lower() == exact.lower()]
        elif regex:
            pattern = re.compile(str(regex))
            candidates = [asset for asset in candidates if pattern.search(str(asset.get("asset_name_or_dataset_ref") or ""))]
        elif prefix:
            candidates = [
                asset
                for asset in candidates
                if str(asset.get("asset_name_or_dataset_ref") or "").startswith(prefix)
                and (_season_from_asset_name(str(asset.get("asset_name_or_dataset_ref") or "")) is not None)
            ]
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for asset in candidates:
            key = str(asset.get("season") or asset.get("asset_name_or_dataset_ref"))
            grouped[key].append(asset)
        selected = [
            sorted(group, key=lambda item: _format_rank(str(item.get("asset_name_or_dataset_ref") or ""), prefer_csv_gz=prefer_csv_gz))[0]
            for _, group in sorted(grouped.items())
        ]
        return sorted(selected, key=lambda item: (str(item.get("season") or "9999"), str(item.get("asset_name_or_dataset_ref") or "")))

    def _select_assets_with_private(self, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        private = [asset for asset in list(metadata.get("_assets_private") or []) if isinstance(asset, dict)]
        if private:
            return private
        release_tag = str(self.source.get("release_tag") or "")
        public = list(metadata.get("assets") or [])
        assets: list[dict[str, Any]] = []
        for asset in public:
            if not isinstance(asset, dict):
                continue
            name = str(asset.get("asset_name_or_dataset_ref") or "")
            url = f"https://github.com/nflverse/nflverse-data/releases/download/{release_tag}/{name}"
            assets.append({**asset, "_download_url": url})
        return assets

    def _assets_for_season(self, assets: list[dict[str, Any]], season: str) -> list[dict[str, Any]]:
        season_matches = [asset for asset in assets if str(asset.get("season") or "") == season]
        if season_matches:
            return season_matches
        return [asset for asset in assets if not asset.get("season")]

    def _download_assets(
        self,
        gate: str,
        assets: list[dict[str, Any]],
        *,
        max_records: int | None,
        metadata: dict[str, Any],
        season: int | str | None = None,
    ) -> dict[str, Any]:
        records_validated = 0
        records_rejected = 0
        downloads_attempted = 0
        downloads_succeeded = 0
        fields_seen: set[str] = set()
        field_type_counts: dict[str, Counter[str]] = defaultdict(Counter)
        seasons_backfilled: set[str] = set()
        sample_rows: list[dict[str, Any]] = []
        asset_reports: list[dict[str, Any]] = []
        status = "ok"
        blocked_reason = None
        for asset in assets:
            url = str(asset.get("_download_url") or "")
            asset_name = str(asset.get("asset_name_or_dataset_ref") or "")
            if not url:
                records_rejected += 1
                asset_reports.append({"asset_name_or_dataset_ref": asset_name, "status": "blocked", "blocked_reason": "source_url_unverified"})
                continue
            downloads_attempted += 1
            try:
                fields, rows, total_rows = _iter_csv_rows_from_url(url, max_records=max_records)
                downloads_succeeded += 1
                normalized = self.normalize_records(rows, asset_name=asset_name)
                shape = self.validate_sample_shape(normalized, fields)
                if not shape["ok"]:
                    blocked_reason = "field_shape_unverified"
                    status = "field_shape_unverified"
                fields_seen.update(fields)
                for row in rows[:MAX_SAMPLE_ROWS_TO_PERSIST]:
                    for key, value in row.items():
                        field_type_counts[str(key)][_field_type(value)] += 1
                records_validated += int(total_rows)
                if len(normalized) < len(rows):
                    records_rejected += len(rows) - len(normalized)
                for row in normalized:
                    if len(sample_rows) < MAX_SAMPLE_ROWS_TO_PERSIST:
                        sample_rows.append(row)
                asset_season = str(asset.get("season") or season or "all")
                seasons_backfilled.add(asset_season)
                asset_reports.append(
                    {
                        "asset_name_or_dataset_ref": asset_name,
                        "status": "ok",
                        "blocked_reason": None,
                        "season": asset.get("season"),
                        "file_format": asset.get("file_format"),
                        "records_validated": int(total_rows),
                        "records_rejected": max(0, len(rows) - len(normalized)),
                        "field_count": len(fields),
                        "fields_available": fields[:200],
                    }
                )
            except (csv.Error, EOFError, UnicodeDecodeError, OSError, urllib.error.URLError, TimeoutError, socket.timeout) as exc:
                records_rejected += 1
                blocker = "source_timeout" if _timeout_error(exc) else "provider_error"
                status = blocker
                blocked_reason = blocker
                asset_reports.append(
                    {
                        "asset_name_or_dataset_ref": asset_name,
                        "status": "blocked",
                        "blocked_reason": blocker,
                        "season": asset.get("season"),
                        "records_validated": 0,
                        "records_rejected": 1,
                    }
                )
        ok = downloads_succeeded > 0 and (blocked_reason is None or records_validated > 0)
        if records_validated <= 0 and blocked_reason is None:
            blocked_reason = "no_records_found"
            status = "blocked"
            ok = False
        field_types = {
            field: counts.most_common(1)[0][0]
            for field, counts in field_type_counts.items()
            if counts
        }
        report = {
            **SAFETY_FIELDS,
            "ok": bool(ok),
            "status": "sample_ready" if gate == "tiny_sample" and ok else "one_season_import_complete" if gate == "one_season_import" and ok else "full_backfill_complete" if gate == "full_available_backfill" and ok else status,
            "schema_version": NFL_OPEN_DATA_ADAPTER_SCHEMA_VERSION,
            "created_at": utc_now_iso(),
            "run_id": _short_run_id(gate, str(self.source["source_id"])),
            "source_id": self.source["source_id"],
            "source_name": self.source.get("source_name"),
            "source_family": self.source.get("source_family"),
            "data_category": self.source.get("data_category"),
            "module": NFL_MODULE,
            "gate": gate,
            "season": str(season) if season is not None else None,
            "blocked_reason": blocked_reason,
            "metadata": _safe_metadata(metadata),
            "asset_reports": asset_reports,
            "records_validated": int(records_validated),
            "records_rejected": int(records_rejected),
            "sample_rows": sample_rows,
            "fields_available": sorted(fields_seen),
            "field_types": field_types,
            "field_count": len(fields_seen),
            "seasons_available": list(metadata.get("seasons_available") or []),
            "seasons_backfilled": sorted(seasons_backfilled),
            "downloads_attempted": downloads_attempted,
            "downloads_succeeded": downloads_succeeded,
            "provider_calls_attempted": int(metadata.get("provider_calls_attempted", 0) or 0),
            "provider_calls_succeeded": int(metadata.get("provider_calls_succeeded", 0) or 0),
            "provider_calls_failed": int(metadata.get("provider_calls_failed", 0) or 0),
            "enabled_source_count": 0,
            "paid_source_enabled_count": 0,
            "provider_write": False,
            "execution_allowed": False,
            "raw_payload_included": False,
            "secrets_included": False,
            "next_safe_action": "continue next gate" if ok else "review source blocker",
            "storage_health": get_storage_health(),
        }
        if blocked_reason and blocked_reason not in BLOCKED_REASONS:
            report["blocked_reason"] = "unsupported_file_shape"
        return report


def _safe_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        return {}
    safe = {
        key: value
        for key, value in metadata.items()
        if key not in {"assets"} and not str(key).startswith("_")
    }
    safe["raw_payload_included"] = False
    safe["secrets_included"] = False
    return safe


def _collection_payload(report: dict[str, Any], rows: list[dict[str, Any]], *, scope: str, scope_value: str) -> dict[str, Any]:
    return {
        **SAFETY_FIELDS,
        "ok": True,
        "status": "ok",
        "schema_version": NFL_OPEN_DATA_ADAPTER_SCHEMA_VERSION,
        "created_at": report.get("created_at"),
        "source_id": report.get("source_id"),
        "source_family": report.get("source_family"),
        "data_category": report.get("data_category"),
        "module": NFL_MODULE,
        "scope": scope,
        "scope_value": scope_value,
        "records_validated": len(rows),
        "sample_rows": rows,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def _validated_root(source_id: str, base_data_dir: str | Path | None = None) -> Path:
    base = get_data_sources_dir() if base_data_dir is None else resolve_base_data_dir(base_data_dir) / "data_sources"
    root = base / "nfl_open_data" / "validated" / sanitize_filename(source_id)
    root.mkdir(parents=True, exist_ok=True)
    return root


def render_adapter_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# NFL Open Data Validated Source",
            "",
            f"1. source_id: {report.get('source_id')}",
            f"2. gate: {report.get('gate')}",
            f"3. status: {report.get('status')}",
            f"4. records_validated: {report.get('records_validated')}",
            f"5. records_rejected: {report.get('records_rejected')}",
            f"6. seasons_backfilled: {', '.join(report.get('seasons_backfilled') or []) if report.get('seasons_backfilled') else 'none'}",
            f"7. field_count: {report.get('field_count')}",
            f"8. downloads_attempted: {report.get('downloads_attempted')}; downloads_succeeded: {report.get('downloads_succeeded')}; provider_calls_attempted: {report.get('provider_calls_attempted')}",
            "9. safety: provider_write=false; execution_allowed=false; raw_payload_included=false; secrets_included=false",
            "",
        ]
    )


def build_adapters() -> list[NflOpenDataAdapter]:
    return [NflOpenDataAdapter(source) for source in nfl_open_data_sources()]


def adapter_by_id(source_id: str) -> NflOpenDataAdapter | None:
    source = source_by_id(source_id)
    return NflOpenDataAdapter(source) if source else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--gate", default="metadata_check")
    parser.add_argument("--season", default=str(DEFAULT_ONE_SEASON))
    parser.add_argument("--max-records", type=int, default=DEFAULT_TINY_SAMPLE_RECORDS)
    parser.add_argument("--allow-download", action="store_true")
    parser.add_argument("--tiny-sample-passed", action="store_true")
    parser.add_argument("--one-season-passed", action="store_true")
    parser.add_argument("--safe-override", action="store_true")
    parser.add_argument("--max-full-assets", type=int, default=None)
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    adapter = adapter_by_id(args.source_id)
    if adapter is None:
        print(json.dumps({**SAFETY_FIELDS, "ok": False, "status": "blocked", "blocked_reason": "unsupported_source"}, indent=2, sort_keys=True))
        return 1
    if args.gate == "metadata_check":
        report = adapter.build_compact_report()
    elif args.gate == "tiny_sample":
        report = adapter.run_tiny_sample(allow_download=args.allow_download, max_records=args.max_records)
    elif args.gate == "one_season_import":
        report = adapter.run_one_season_import(
            season=args.season,
            allow_download=args.allow_download,
            tiny_sample_passed=args.tiny_sample_passed,
            safe_override=args.safe_override,
        )
    elif args.gate == "full_available_backfill":
        report = adapter.run_full_available_backfill(
            allow_download=args.allow_download,
            one_season_passed=args.one_season_passed,
            max_full_assets=args.max_full_assets,
        )
    else:
        report = adapter._blocked_report(str(args.gate), "unsupported_source")
    paths: dict[str, Any] = {}
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
                "seasons_backfilled": report.get("seasons_backfilled") or [],
                "field_count": int(report.get("field_count", 0) or 0),
                "downloads_attempted": int(report.get("downloads_attempted", 0) or 0),
                "downloads_succeeded": int(report.get("downloads_succeeded", 0) or 0),
                "provider_calls_attempted": int(report.get("provider_calls_attempted", 0) or 0),
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
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

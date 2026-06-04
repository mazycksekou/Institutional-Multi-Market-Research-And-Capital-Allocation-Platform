from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from .open_sports_history_import import (
    build_open_sports_history_import_report,
    write_open_sports_history_import_report,
)
from .open_sports_history_sources import SAFETY_FIELDS, source_by_id
from .scheduler_config import sanitize_filename, utc_now_iso


OPEN_SPORTS_HISTORY_BACKFILL_SCHEMA_VERSION = "open_sports_history_backfill_v1"
OPEN_SPORTS_HISTORY_COVERAGE_SCHEMA_VERSION = "open_sports_history_coverage_v1"

SUPPORTED_MODES = {
    "smoke_test",
    "season_backfill",
    "bulk_backfill",
    "scheduled_backfill",
    "coverage_report",
}
PARSER_SOURCE_IDS = {"retrosheet_mlb", "nflverse_nfl"}
DEFAULT_TARGET_YEARS = 10
NFLVERSE_NFL_TARGET_SOURCE_ID = "nflverse_nfl"
NFLVERSE_NFL_TARGET_MODULE = "americanfootball_nfl"
NFLVERSE_NFL_FALLBACK_TARGET_SEASONS = tuple(range(2024, 2014, -1))


def _data_sources_root(base_data_dir: str | Path | None = None) -> Path:
    base = get_data_sources_dir() if base_data_dir is None else resolve_base_data_dir(base_data_dir) / "data_sources"
    root = base / "open_sports_history"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _sessions_root(base_data_dir: str | Path | None = None) -> Path:
    root = _data_sources_root(base_data_dir) / "backfill_sessions"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _coverage_root(base_data_dir: str | Path | None = None) -> Path:
    root = _data_sources_root(base_data_dir) / "coverage"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _validated_root(base_data_dir: str | Path | None = None) -> Path:
    root = _data_sources_root(base_data_dir) / "validated"
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


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _season_sort_key(value: Any) -> tuple[int, str]:
    text = str(value)
    try:
        return int(text), text
    except ValueError:
        return -1, text


def _valid_rows(payload: Any) -> list[dict[str, Any]]:
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
        if str(row.get("blocked_reason") or row.get("validation_status") or "").lower() not in {"available"}:
            continue
        rows.append({**row, "raw_payload_included": False})
    return rows


def _dedupe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        key = (str(row.get("module") or ""), str(row.get("source_id") or ""), str(row.get("event_id") or ""))
        if not key[2] or key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def _row_is_real_open_data(row: dict[str, Any]) -> bool:
    synthetic_flag = row.get("is_synthetic")
    synthetic_text = str(synthetic_flag).strip().lower()
    return row.get("data_kind") == "real_open_data" and synthetic_flag is not True and synthetic_text not in {"true", "1", "yes"}


def _real_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if _row_is_real_open_data(row)]


def _count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts = Counter(str(row.get(key) or "unknown") for row in rows)
    return dict(sorted(counts.items()))


def _valid_row_kind_counts(import_report: dict[str, Any]) -> tuple[int, int]:
    rows = list(import_report.get("validated_preview_rows") or [])
    real_count = len(_real_rows(rows))
    return real_count, max(0, len(rows) - real_count)


def _load_validated_preview_rows(*, base_data_dir: str | Path | None = None) -> list[dict[str, Any]]:
    root = _validated_root(base_data_dir)
    payloads: list[Any] = [_read_json(root / "latest.json")]
    by_module = root / "by_module"
    if by_module.exists():
        for path in sorted(by_module.glob("*.json")):
            payloads.append(_read_json(path))
    by_season = root / "by_season"
    if by_season.exists():
        for path in sorted(by_season.glob("*/*.json")):
            payloads.append(_read_json(path))
    rows: list[dict[str, Any]] = []
    for payload in payloads:
        rows.extend(_valid_rows(payload))
    return _dedupe_rows(rows)


def _latest_validated_payload(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    payload = _read_json(_validated_root(base_data_dir) / "latest.json")
    return payload if isinstance(payload, dict) else {}


def _latest_source_availability(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    payload = _latest_validated_payload(base_data_dir=base_data_dir)
    direct = payload.get("source_availability")
    if isinstance(direct, dict):
        return direct
    nested = payload.get("source_url_resolution")
    if isinstance(nested, dict) and isinstance(nested.get("source_availability"), dict):
        return nested["source_availability"]
    return {}


def _rejected_rows_by_session_season(
    *,
    base_data_dir: str | Path | None = None,
    source_id: str,
) -> dict[str, int]:
    root = _sessions_root(base_data_dir)
    paths: list[Path] = []
    item_dir = root / "items"
    if item_dir.exists():
        paths.extend(sorted(item_dir.glob("*.json")))
    latest_by_season: dict[str, tuple[str, int]] = {}
    for path in paths:
        payload = _read_json(path)
        if not isinstance(payload, dict) or payload.get("source_id") != source_id:
            continue
        created = str(payload.get("created_at") or "")
        for result in payload.get("season_results") or []:
            if not isinstance(result, dict):
                continue
            season = result.get("season")
            if season is None:
                continue
            key = str(season)
            count = int(result.get("records_rejected", 0) or 0)
            prior = latest_by_season.get(key)
            if prior is None or created >= prior[0]:
                latest_by_season[key] = (created, count)
    return {season: count for season, (_, count) in sorted(latest_by_season.items())}


def _target_seasons(*, seasons: list[int | str] | None = None, target_years: int = DEFAULT_TARGET_YEARS) -> list[int | str]:
    if seasons:
        return list(seasons)
    current_year = datetime.now(timezone.utc).year
    years = max(1, min(int(target_years or DEFAULT_TARGET_YEARS), 50))
    return list(range(current_year - years, current_year))


def _session_id(mode: str, source_id: str | None, explicit: str | None = None) -> str:
    if explicit:
        return sanitize_filename(explicit)
    return sanitize_filename(f"open_sports_history_{mode}_{source_id or 'all'}_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}")


def _import_max_records(
    source: dict[str, Any],
    *,
    source_id: str,
    max_records: int | None,
    allow_download: bool,
    smoke_test: bool = False,
) -> int | None:
    if max_records is not None:
        return max_records
    if smoke_test:
        return min(int(source.get("max_records_default") or 25), 25)
    if allow_download and source_id == "nflverse_nfl":
        return int(source.get("max_records_hard_cap") or 500)
    return None


def _smoke_test_passed(source_id: str, *, base_data_dir: str | Path | None = None) -> bool:
    root = _sessions_root(base_data_dir)
    candidates = [root / "latest.json"]
    item_dir = root / "items"
    if item_dir.exists():
        candidates.extend(sorted(item_dir.glob("*.json"), reverse=True))
    for path in candidates:
        payload = _read_json(path)
        if not isinstance(payload, dict):
            continue
        if payload.get("source_id") == source_id and payload.get("mode") == "smoke_test" and payload.get("smoke_test_passed") is True:
            return True
    return False


def _error_report(
    *,
    mode: str,
    source_id: str | None,
    blocked_reason: str,
    message: str,
    base_data_dir: str | Path | None,
    session_id: str | None = None,
) -> dict[str, Any]:
    return {
        **SAFETY_FIELDS,
        "ok": False,
        "status": "blocked",
        "schema_version": OPEN_SPORTS_HISTORY_BACKFILL_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "mode": mode,
        "source_id": source_id,
        "session_id": session_id or _session_id(mode, source_id),
        "blocked_reason": blocked_reason,
        "message": message,
        "runtime_data_dir": str(resolve_base_data_dir(base_data_dir)),
        "records_valid": 0,
        "real_rows_count": 0,
        "synthetic_rows_count": 0,
        "records_rejected": 0,
        "downloads_attempted": 0,
        "downloads_succeeded": 0,
        "provider_calls_attempted": 0,
        "provider_calls_succeeded": 0,
        "provider_calls_failed": 0,
        "outcome_persistence_attempted": False,
        "import_or_persist_endpoint_called": False,
        "persisted_outcomes": False,
        "storage_health": get_storage_health(),
    }


def _source_gate(source: dict[str, Any] | None, *, source_id: str | None, mode: str, allow_download: bool) -> str | None:
    if mode == "coverage_report":
        return None
    if not source_id or source is None:
        return "unsupported_source"
    if source_id == "sports_reference_manual_export" and allow_download:
        return "sports_reference_scraping_blocked"
    if source.get("future_paid_candidate") or source.get("requires_budget_approval"):
        return "paid_source_not_approved"
    if source.get("approval_status") == "research_required":
        return "research_required"
    if source_id == "sports_reference_manual_export":
        return "terms_review_required"
    if not source.get("current_phase_allowed"):
        return "source_not_current_phase_allowed"
    if mode == "scheduled_backfill" and not source.get("supports_scheduled_backfill"):
        return "unsupported_mode"
    if mode in {"smoke_test", "season_backfill", "bulk_backfill", "scheduled_backfill"} and source_id not in PARSER_SOURCE_IDS:
        return "unsupported_source"
    return None


def _run_import(
    *,
    source_id: str,
    season: int | str | None,
    input_path: str | Path | None,
    max_records: int | None,
    dry_run: bool,
    allow_download: bool,
    persist_preview: bool,
    base_data_dir: str | Path | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    report = build_open_sports_history_import_report(
        source_id=source_id,
        season=season,
        input_path=input_path,
        max_records=max_records,
        dry_run=dry_run,
        allow_download=allow_download,
        persist_preview=persist_preview,
        base_data_dir=base_data_dir,
    )
    paths: dict[str, Any] = {}
    if persist_preview:
        paths = write_open_sports_history_import_report(report, base_data_dir=base_data_dir)
        report.update(paths)
    return report, paths


def _season_result(import_report: dict[str, Any], *, season: int | str | None) -> dict[str, Any]:
    real_count, synthetic_count = _valid_row_kind_counts(import_report)
    return {
        "season": season,
        "status": import_report.get("status"),
        "blocked_reason": import_report.get("blocked_reason"),
        "data_kind": import_report.get("data_kind"),
        "is_synthetic": import_report.get("is_synthetic"),
        "source_url_verified": import_report.get("source_url_verified"),
        "selected_source_url_kind": import_report.get("selected_source_url_kind"),
        "selected_source_host": import_report.get("selected_source_host"),
        "selected_release_tag": import_report.get("selected_release_tag"),
        "selected_asset_name": import_report.get("selected_asset_name"),
        "selected_asset_format": import_report.get("selected_asset_format"),
        "fallback_used": import_report.get("fallback_used"),
        "url_resolution_blocker": import_report.get("url_resolution_blocker"),
        "source_verified_at": import_report.get("source_verified_at"),
        "records_received": int(import_report.get("records_received", 0) or 0),
        "records_valid": int(import_report.get("records_valid", 0) or 0),
        "real_rows_count": real_count,
        "synthetic_rows_count": synthetic_count,
        "valid_real_preview_rows": real_count,
        "records_rejected": int(import_report.get("records_rejected", 0) or 0),
        "downloads_attempted": int(import_report.get("downloads_attempted", 0) or 0),
        "downloads_succeeded": int(import_report.get("downloads_succeeded", 0) or 0),
        "provider_calls_attempted": int(import_report.get("provider_calls_attempted", 0) or 0),
        "provider_calls_succeeded": int(import_report.get("provider_calls_succeeded", 0) or 0),
        "provider_calls_failed": int(import_report.get("provider_calls_failed", 0) or 0),
        "validated_paths": {
            "latest_json_path": import_report.get("latest_json_path"),
            "by_source_paths": import_report.get("by_source_paths") or [],
            "by_module_paths": import_report.get("by_module_paths") or [],
            "by_season_paths": import_report.get("by_season_paths") or [],
        },
    }


def _base_report(
    *,
    mode: str,
    source_id: str | None,
    session_id: str,
    base_data_dir: str | Path | None,
    target_years: int,
    seasons: list[int | str],
    dry_run: bool,
    allow_download: bool,
    persist_preview: bool,
    resume: bool,
) -> dict[str, Any]:
    return {
        **SAFETY_FIELDS,
        "ok": True,
        "status": "ok",
        "schema_version": OPEN_SPORTS_HISTORY_BACKFILL_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "run_id": session_id,
        "session_id": session_id,
        "mode": mode,
        "source_id": source_id,
        "target_years": int(target_years),
        "seasons": seasons,
        "dry_run": bool(dry_run),
        "allow_download": bool(allow_download),
        "persist_preview": bool(persist_preview),
        "resume": bool(resume),
        "runtime_data_dir": str(resolve_base_data_dir(base_data_dir)),
        "records_valid": 0,
        "real_rows_count": 0,
        "synthetic_rows_count": 0,
        "records_rejected": 0,
        "downloads_attempted": 0,
        "downloads_succeeded": 0,
        "provider_calls_attempted": 0,
        "provider_calls_succeeded": 0,
        "provider_calls_failed": 0,
        "outcome_persistence_attempted": False,
        "import_or_persist_endpoint_called": False,
        "persisted_outcomes": False,
        "season_results": [],
        "completed_seasons": [],
        "pending_seasons": seasons,
        "next_recommended_session": None,
        "storage_health": get_storage_health(),
    }


def build_open_sports_history_backfill_report(
    *,
    source_id: str | None = None,
    mode: str = "coverage_report",
    seasons: list[int | str] | None = None,
    target_years: int = DEFAULT_TARGET_YEARS,
    input_path: str | Path | None = None,
    max_records: int | None = None,
    dry_run: bool = True,
    allow_download: bool = False,
    persist_preview: bool = False,
    resume: bool = True,
    session_id: str | None = None,
    base_data_dir: str | Path | None = None,
) -> dict[str, Any]:
    mode = str(mode or "").strip()
    sid = _session_id(mode or "unsupported_mode", source_id, session_id)
    if mode not in SUPPORTED_MODES:
        return _error_report(mode=mode, source_id=source_id, blocked_reason="unsupported_mode", message="unsupported open sports history mode", base_data_dir=base_data_dir, session_id=sid)
    if mode == "coverage_report":
        return build_open_sports_history_coverage_report(base_data_dir=base_data_dir)

    source = source_by_id(str(source_id or ""))
    gate = _source_gate(source, source_id=source_id, mode=mode, allow_download=allow_download)
    if gate:
        return _error_report(mode=mode, source_id=source_id, blocked_reason=gate, message="source is not available for this backfill mode", base_data_dir=base_data_dir, session_id=sid)

    planned_seasons = _target_seasons(seasons=seasons, target_years=target_years)
    report = _base_report(
        mode=mode,
        source_id=source_id,
        session_id=sid,
        base_data_dir=base_data_dir,
        target_years=target_years,
        seasons=planned_seasons,
        dry_run=dry_run,
        allow_download=allow_download,
        persist_preview=persist_preview,
        resume=resume,
    )
    assert source_id is not None

    if mode == "smoke_test":
        smoke_max = _import_max_records(source, source_id=source_id, max_records=max_records, allow_download=allow_download, smoke_test=True)
        import_report, paths = _run_import(
            source_id=source_id,
            season=planned_seasons[0] if seasons else None,
            input_path=input_path,
            max_records=smoke_max,
            dry_run=dry_run,
            allow_download=allow_download,
            persist_preview=persist_preview,
            base_data_dir=base_data_dir,
        )
        real_count, synthetic_count = _valid_row_kind_counts(import_report)
        report.update(
            {
                "status": "smoke_test_passed" if import_report.get("records_valid", 0) else "blocked",
                "ok": bool(import_report.get("records_valid", 0)),
                "blocked_reason": import_report.get("blocked_reason"),
                "smoke_test_passed": bool(import_report.get("records_valid", 0)),
                "records_valid": int(import_report.get("records_valid", 0) or 0),
                "real_rows_count": real_count,
                "synthetic_rows_count": synthetic_count,
                "records_rejected": int(import_report.get("records_rejected", 0) or 0),
                "downloads_attempted": int(import_report.get("downloads_attempted", 0) or 0),
                "downloads_succeeded": int(import_report.get("downloads_succeeded", 0) or 0),
                "provider_calls_attempted": int(import_report.get("provider_calls_attempted", 0) or 0),
                "provider_calls_succeeded": int(import_report.get("provider_calls_succeeded", 0) or 0),
                "provider_calls_failed": int(import_report.get("provider_calls_failed", 0) or 0),
                "season_results": [_season_result(import_report, season=import_report.get("season"))],
                "completed_seasons": [import_report.get("season")] if import_report.get("records_valid") and import_report.get("season") else [],
                "pending_seasons": [],
                "validated_paths": paths,
                "next_recommended_session": "run season_backfill for one season after smoke_test_passed=true",
            }
        )
        return report

    if mode == "season_backfill":
        if not seasons:
            return _error_report(mode=mode, source_id=source_id, blocked_reason="insufficient_fields", message="season_backfill requires one season", base_data_dir=base_data_dir, session_id=sid)
        season = planned_seasons[0]
        season_max = _import_max_records(source, source_id=source_id, max_records=max_records, allow_download=allow_download)
        import_report, paths = _run_import(
            source_id=source_id,
            season=season,
            input_path=input_path,
            max_records=season_max,
            dry_run=dry_run,
            allow_download=allow_download,
            persist_preview=persist_preview,
            base_data_dir=base_data_dir,
        )
        valid = int(import_report.get("records_valid", 0) or 0)
        real_count, synthetic_count = _valid_row_kind_counts(import_report)
        report.update(
            {
                "status": "season_backfill_complete" if valid else "blocked",
                "ok": bool(valid),
                "blocked_reason": import_report.get("blocked_reason"),
                "records_valid": valid,
                "real_rows_count": real_count,
                "synthetic_rows_count": synthetic_count,
                "records_rejected": int(import_report.get("records_rejected", 0) or 0),
                "downloads_attempted": int(import_report.get("downloads_attempted", 0) or 0),
                "downloads_succeeded": int(import_report.get("downloads_succeeded", 0) or 0),
                "provider_calls_attempted": int(import_report.get("provider_calls_attempted", 0) or 0),
                "provider_calls_succeeded": int(import_report.get("provider_calls_succeeded", 0) or 0),
                "provider_calls_failed": int(import_report.get("provider_calls_failed", 0) or 0),
                "season_results": [_season_result(import_report, season=season)],
                "completed_seasons": [season] if valid else [],
                "pending_seasons": [] if valid else [season],
                "validated_paths": paths,
                "next_recommended_session": "run bulk_backfill for last 10 seasons after one-season validation passes" if valid else "fix the blocked season input before bulk_backfill",
            }
        )
        return report

    if mode == "bulk_backfill":
        local_parser_pass = False
        if input_path:
            parser_report, _ = _run_import(
                source_id=source_id,
                season=None,
                input_path=input_path,
                max_records=max_records,
                dry_run=True,
                allow_download=False,
                persist_preview=False,
                base_data_dir=base_data_dir,
            )
            local_parser_pass = bool(parser_report.get("records_valid", 0))
        if not (local_parser_pass or _smoke_test_passed(source_id, base_data_dir=base_data_dir)):
            return _error_report(mode=mode, source_id=source_id, blocked_reason="smoke_test_required", message="bulk_backfill requires a passing smoke_test or a valid local parser input", base_data_dir=base_data_dir, session_id=sid)
        if not source.get("bulk_backfill_allowed_after_smoke"):
            return _error_report(mode=mode, source_id=source_id, blocked_reason="unsupported_mode", message="source does not allow bulk backfill after smoke", base_data_dir=base_data_dir, session_id=sid)

        season_results: list[dict[str, Any]] = []
        completed: list[int | str] = []
        pending: list[int | str] = []
        total_valid = total_real = total_synthetic = total_rejected = total_downloads = total_downloads_succeeded = 0
        total_provider_calls = total_provider_calls_succeeded = total_provider_calls_failed = 0
        if input_path:
            import_report, paths = _run_import(
                source_id=source_id,
                season=None,
                input_path=input_path,
                max_records=max_records,
                dry_run=dry_run,
                allow_download=False,
                persist_preview=persist_preview,
                base_data_dir=base_data_dir,
            )
            rows = _valid_rows(import_report)
            seasons_with_rows = {str(row.get("season")) for row in rows if row.get("season") is not None}
            for season in planned_seasons:
                if str(season) in seasons_with_rows:
                    completed.append(season)
                else:
                    pending.append(season)
                season_results.append(_season_result(import_report, season=season))
            total_valid = int(import_report.get("records_valid", 0) or 0)
            total_real, total_synthetic = _valid_row_kind_counts(import_report)
            total_rejected = int(import_report.get("records_rejected", 0) or 0)
            total_downloads = int(import_report.get("downloads_attempted", 0) or 0)
            total_downloads_succeeded = int(import_report.get("downloads_succeeded", 0) or 0)
            total_provider_calls = int(import_report.get("provider_calls_attempted", 0) or 0)
            total_provider_calls_succeeded = int(import_report.get("provider_calls_succeeded", 0) or 0)
            total_provider_calls_failed = int(import_report.get("provider_calls_failed", 0) or 0)
            report["validated_paths"] = paths
        else:
            for season in planned_seasons:
                season_max = _import_max_records(source, source_id=source_id, max_records=max_records, allow_download=allow_download)
                import_report, paths = _run_import(
                    source_id=source_id,
                    season=season,
                    input_path=None,
                    max_records=season_max,
                    dry_run=dry_run,
                    allow_download=allow_download,
                    persist_preview=persist_preview,
                    base_data_dir=base_data_dir,
                )
                valid = int(import_report.get("records_valid", 0) or 0)
                real_count, synthetic_count = _valid_row_kind_counts(import_report)
                total_valid += valid
                total_real += real_count
                total_synthetic += synthetic_count
                total_rejected += int(import_report.get("records_rejected", 0) or 0)
                total_downloads += int(import_report.get("downloads_attempted", 0) or 0)
                total_downloads_succeeded += int(import_report.get("downloads_succeeded", 0) or 0)
                total_provider_calls += int(import_report.get("provider_calls_attempted", 0) or 0)
                total_provider_calls_succeeded += int(import_report.get("provider_calls_succeeded", 0) or 0)
                total_provider_calls_failed += int(import_report.get("provider_calls_failed", 0) or 0)
                season_results.append(_season_result(import_report, season=season))
                if valid:
                    completed.append(season)
                else:
                    pending.append(season)
                    if import_report.get("blocked_reason") in {"provider_error", "source_error", "download_not_allowed", "source_not_available"}:
                        break
        report.update(
            {
                "status": "bulk_backfill_complete" if total_valid and not pending else ("bulk_backfill_partial" if total_valid else "blocked"),
                "ok": bool(total_valid),
                "blocked_reason": None if total_valid else (season_results[-1].get("blocked_reason") if season_results else "no_records_found"),
                "records_valid": total_valid,
                "real_rows_count": total_real,
                "synthetic_rows_count": total_synthetic,
                "records_rejected": total_rejected,
                "downloads_attempted": total_downloads,
                "downloads_succeeded": total_downloads_succeeded,
                "provider_calls_attempted": total_provider_calls,
                "provider_calls_succeeded": total_provider_calls_succeeded,
                "provider_calls_failed": total_provider_calls_failed,
                "season_results": season_results,
                "completed_seasons": completed,
                "pending_seasons": pending,
                "next_recommended_session": "resume bulk_backfill for pending seasons" if pending else "run coverage_report and derived_feature_backfill_report",
            }
        )
        return report

    if mode == "scheduled_backfill":
        next_season = planned_seasons[0] if planned_seasons else None
        report.update(
            {
                "status": "scheduled_session_ready",
                "ok": True,
                "blocked_reason": None,
                "scheduled_chunk_size": 1,
                "completed_seasons": [],
                "pending_seasons": planned_seasons,
                "next_recommended_session": f"resume scheduled_backfill with season {next_season}" if next_season else "run coverage_report",
            }
        )
        if input_path or allow_download:
            scheduled_max = _import_max_records(source, source_id=source_id, max_records=max_records, allow_download=allow_download)
            import_report, paths = _run_import(
                source_id=source_id,
                season=next_season,
                input_path=input_path,
                max_records=scheduled_max,
                dry_run=dry_run,
                allow_download=allow_download,
                persist_preview=persist_preview,
                base_data_dir=base_data_dir,
            )
            valid = int(import_report.get("records_valid", 0) or 0)
            real_count, synthetic_count = _valid_row_kind_counts(import_report)
            report.update(
                {
                    "status": "scheduled_session_chunk_complete" if valid else "blocked",
                    "ok": bool(valid),
                    "blocked_reason": import_report.get("blocked_reason"),
                    "records_valid": valid,
                    "real_rows_count": real_count,
                    "synthetic_rows_count": synthetic_count,
                    "records_rejected": int(import_report.get("records_rejected", 0) or 0),
                    "downloads_attempted": int(import_report.get("downloads_attempted", 0) or 0),
                    "downloads_succeeded": int(import_report.get("downloads_succeeded", 0) or 0),
                    "provider_calls_attempted": int(import_report.get("provider_calls_attempted", 0) or 0),
                    "provider_calls_succeeded": int(import_report.get("provider_calls_succeeded", 0) or 0),
                    "provider_calls_failed": int(import_report.get("provider_calls_failed", 0) or 0),
                    "season_results": [_season_result(import_report, season=next_season)],
                    "completed_seasons": [next_season] if valid and next_season is not None else [],
                    "pending_seasons": planned_seasons[1:] if valid else planned_seasons,
                    "validated_paths": paths,
                    "next_recommended_session": "resume scheduled_backfill for next pending season",
                }
            )
        return report

    return _error_report(mode=mode, source_id=source_id, blocked_reason="unsupported_mode", message="unsupported open sports history mode", base_data_dir=base_data_dir, session_id=sid)


def build_open_sports_history_coverage_report(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    rows = _load_validated_preview_rows(base_data_dir=base_data_dir)
    by_module: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_module[str(row.get("module") or "unknown")].append(row)
        by_source[str(row.get("source_id") or "unknown")].append(row)

    real_rows = _real_rows(rows)
    synthetic_rows = [row for row in rows if not _row_is_real_open_data(row)]
    source_availability = _latest_source_availability(base_data_dir=base_data_dir)
    target_real_rows = [
        row
        for row in real_rows
        if row.get("source_id") == NFLVERSE_NFL_TARGET_SOURCE_ID and row.get("module") == NFLVERSE_NFL_TARGET_MODULE
    ]
    target_real_counts_all = Counter(str(row.get("season") or "unknown") for row in target_real_rows)
    available_completed = [
        str(season)
        for season in source_availability.get("all_available_completed_seasons") or source_availability.get("seasons_available") or []
    ]
    if not available_completed:
        available_completed = sorted(
            {str(row.get("season")) for row in target_real_rows if row.get("season") is not None},
            key=_season_sort_key,
        )
    if not available_completed:
        available_completed = [str(season) for season in sorted(NFLVERSE_NFL_FALLBACK_TARGET_SEASONS)]
    target_seasons = sorted(dict.fromkeys(available_completed), key=_season_sort_key)
    incomplete_or_future_seasons = [
        str(season)
        for season in source_availability.get("incomplete_or_future_seasons") or []
    ]
    source_completion_status = source_availability.get("source_completion_status") if isinstance(source_availability.get("source_completion_status"), dict) else {}
    if not source_completion_status:
        source_completion_status = {
            season: {
                "status": "complete_final_scores" if target_real_counts_all.get(season, 0) > 0 else "season_completion_status_unknown",
                "rows": int(target_real_counts_all.get(season, 0)),
                "final_score_rows": int(target_real_counts_all.get(season, 0)),
                "missing_score_rows": 0,
            }
            for season in target_seasons
        }
    source_completion_status_blocker = source_availability.get("source_completion_status_blocker")
    earliest_available_season = source_availability.get("earliest_available_season") or (target_seasons[0] if target_seasons else None)
    latest_available_completed_season = source_availability.get("latest_available_completed_season") or (target_seasons[-1] if target_seasons else None)

    module_rows: list[dict[str, Any]] = []
    real_coverage_percentage_by_module: dict[str, float] = {}
    seasons_missing: dict[str, list[str]] = {}
    for module, module_records in sorted(by_module.items()):
        real_module_records = _real_rows(module_records)
        synthetic_module_records = [r for r in module_records if not _row_is_real_open_data(r)]
        seasons = sorted({str(row.get("season")) for row in module_records if row.get("season") is not None})
        real_seasons = sorted({str(row.get("season")) for row in real_module_records if row.get("season") is not None})
        synthetic_seasons = sorted({str(row.get("season")) for row in synthetic_module_records if row.get("season") is not None})
        sources = sorted({str(row.get("source_id")) for row in module_records if row.get("source_id")})
        missing = [season for season in target_seasons if season not in set(real_seasons)]
        seasons_missing[module] = missing
        real_coverage_percentage_by_module[module] = round(
            (len(set(real_seasons) & set(target_seasons)) / max(1, len(target_seasons))) * 100,
            2,
        )
        module_rows.append(
            {
                "module": module,
                "total_rows": len(module_records),
                "records_valid": len(module_records),
                "real_records": len(real_module_records),
                "real_rows_count": len(real_module_records),
                "synthetic_records": len(synthetic_module_records),
                "synthetic_rows_count": len(synthetic_module_records),
                "sources": sources,
                "seasons": seasons,
                "real_seasons": real_seasons,
                "synthetic_seasons": synthetic_seasons,
                "target_seasons_missing": missing,
                "season_count": len(seasons),
                "real_season_count": len(real_seasons),
                "tier0_ready": bool(real_module_records),
                "tier0_with_real_data": bool(real_module_records),
                "tier1_candidate": len(real_module_records) >= 3,
                "tier1_with_real_data": len(real_module_records) >= 3,
                "synthetic_rows_ignored_for_real_coverage": True,
            }
        )
    source_rows = [
        {
            "source_id": source,
            "total_rows": len(source_records),
            "records_valid": len(source_records),
            "real_records": len(_real_rows(source_records)),
            "real_rows_count": len(_real_rows(source_records)),
            "synthetic_records": len(source_records) - len(_real_rows(source_records)),
            "synthetic_rows_count": len(source_records) - len(_real_rows(source_records)),
            "modules": sorted({str(row.get("module")) for row in source_records if row.get("module")}),
            "seasons": sorted({str(row.get("season")) for row in source_records if row.get("season") is not None}),
            "real_seasons": sorted({str(row.get("season")) for row in _real_rows(source_records) if row.get("season") is not None}),
        }
        for source, source_records in sorted(by_source.items())
    ]
    season_counts: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        season_counts[(str(row.get("module") or "unknown"), str(row.get("season") or "unknown"))].append(row)
    season_rows = [
        {
            "module": module,
            "season": season,
            "records_valid": len(season_records),
            "real_records": len(_real_rows(season_records)),
            "synthetic_records": len(season_records) - len(_real_rows(season_records)),
        }
        for (module, season), season_records in sorted(season_counts.items())
    ]
    real_module_season_counts = Counter(
        (str(row.get("module") or "unknown"), str(row.get("season") or "unknown"))
        for row in real_rows
    )
    real_rows_by_module_season: dict[str, dict[str, int]] = defaultdict(dict)
    for (module, season), count in sorted(real_module_season_counts.items()):
        real_rows_by_module_season[module][season] = count
    modules_ready_real_tier0 = [row["module"] for row in module_rows if row["tier0_with_real_data"]]
    modules_ready_real_tier1 = [row["module"] for row in module_rows if row["tier1_with_real_data"]]
    target_real_rows_by_season = {
        season: int(target_real_counts_all.get(season, 0))
        for season in target_seasons
        if int(target_real_counts_all.get(season, 0)) > 0
    }
    target_seasons_validated = [season for season in target_seasons if target_real_counts_all.get(season, 0) > 0]
    target_seasons_missing = [season for season in target_seasons if target_real_counts_all.get(season, 0) <= 0]
    rejected_session_counts = _rejected_rows_by_session_season(
        base_data_dir=base_data_dir,
        source_id=NFLVERSE_NFL_TARGET_SOURCE_ID,
    )
    target_rejected_rows_by_season = {
        season: int(rejected_session_counts.get(season, 0))
        for season in target_seasons
    }
    target_coverage_percentage = round((len(target_seasons_validated) / max(1, len(target_seasons))) * 100, 2)
    target_coverage = {
        "source_id": NFLVERSE_NFL_TARGET_SOURCE_ID,
        "module": NFLVERSE_NFL_TARGET_MODULE,
        "target_coverage_strategy": "all_available_completed_seasons",
        "target_coverage_years": len(target_seasons),
        "earliest_available_season": earliest_available_season,
        "latest_available_completed_season": latest_available_completed_season,
        "all_available_completed_seasons": target_seasons,
        "target_seasons": target_seasons,
        "seasons_available": target_seasons,
        "seasons_validated": target_seasons_validated,
        "seasons_missing": target_seasons_missing,
        "validated_completed_seasons": target_seasons_validated,
        "missing_completed_seasons": target_seasons_missing,
        "incomplete_or_future_seasons": incomplete_or_future_seasons,
        "real_rows_by_season": target_real_rows_by_season,
        "rejected_rows_by_season": target_rejected_rows_by_season,
        "source_completion_status": source_completion_status,
        "source_completion_status_blocker": source_completion_status_blocker,
        "coverage_percentage": target_coverage_percentage,
        "synthetic_rows_ignored_for_real_coverage": True,
    }
    covered_slots = len({(str(row.get("module") or "unknown"), str(row.get("season") or "unknown")) for row in real_rows if str(row.get("season") or "unknown") in target_seasons})
    total_slots = len(module_rows) * len(target_seasons)
    real_coverage_percentage = target_coverage_percentage
    next_recommended_backfill = (
        "run season_backfill with real open-data source"
        if not target_real_rows
        else "continue season_backfill for missing target seasons"
        if target_seasons_missing
        else "feed validated real-data rows into derived_feature_backfill_report"
    )
    return {
        **SAFETY_FIELDS,
        "ok": True,
        "status": "ok",
        "schema_version": OPEN_SPORTS_HISTORY_COVERAGE_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "run_id": sanitize_filename(f"open_sports_history_coverage_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
        "mode": "coverage_report",
        "source_id": NFLVERSE_NFL_TARGET_SOURCE_ID,
        "module": NFLVERSE_NFL_TARGET_MODULE,
        "runtime_data_dir": str(resolve_base_data_dir(base_data_dir)),
        "total_rows": len(rows),
        "records_valid": len(rows),
        "real_rows_count": len(real_rows),
        "real_records": len(real_rows),
        "synthetic_rows_count": len(synthetic_rows),
        "synthetic_records": len(synthetic_rows),
        "synthetic_rows_ignored_for_real_coverage": True,
        "target_coverage_strategy": "all_available_completed_seasons",
        "target_coverage_years": len(target_seasons),
        "earliest_available_season": earliest_available_season,
        "latest_available_completed_season": latest_available_completed_season,
        "all_available_completed_seasons": target_seasons,
        "seasons_available": target_seasons,
        "target_seasons": target_seasons,
        "target_source_id": NFLVERSE_NFL_TARGET_SOURCE_ID,
        "target_module": NFLVERSE_NFL_TARGET_MODULE,
        "seasons_targeted": target_seasons,
        "seasons_validated": target_seasons_validated,
        "validated_completed_seasons": target_seasons_validated,
        "seasons_missing_for_target": target_seasons_missing,
        "seasons_missing": target_seasons_missing,
        "missing_completed_seasons": target_seasons_missing,
        "incomplete_or_future_seasons": incomplete_or_future_seasons,
        "real_rows_by_target_season": target_real_rows_by_season,
        "rejected_rows_by_season": target_rejected_rows_by_season,
        "rejected_rows_by_target_season": target_rejected_rows_by_season,
        "source_completion_status": source_completion_status,
        "source_completion_status_blocker": source_completion_status_blocker,
        "coverage_percentage": target_coverage_percentage,
        "nflverse_nfl_coverage_percentage": target_coverage_percentage,
        "target_coverage": target_coverage,
        "real_rows_by_source": _count_by(real_rows, "source_id"),
        "real_rows_by_module": _count_by(real_rows, "module"),
        "real_rows_by_season": _count_by(real_rows, "season"),
        "real_rows_by_module_season": dict(sorted(real_rows_by_module_season.items())),
        "real_coverage_percentage": real_coverage_percentage,
        "real_coverage_percentage_by_module": dict(sorted(real_coverage_percentage_by_module.items())),
        "module_seasons_missing": seasons_missing,
        "modules_with_valid_rows": sorted(by_module),
        "sources_with_valid_rows": sorted(by_source),
        "modules_with_real_rows": sorted({str(row.get("module")) for row in real_rows if row.get("module")}),
        "sources_with_real_rows": sorted({str(row.get("source_id")) for row in real_rows if row.get("source_id")}),
        "modules_ready_for_tier0": modules_ready_real_tier0,
        "modules_ready_for_tier1_candidate": modules_ready_real_tier1,
        "modules_ready_for_real_tier0": modules_ready_real_tier0,
        "modules_ready_for_real_tier1": modules_ready_real_tier1,
        "module_coverage": module_rows,
        "source_coverage": source_rows,
        "season_coverage": season_rows,
        "provider_calls_attempted": 0,
        "downloads_attempted": 0,
        "outcome_persistence_attempted": False,
        "import_or_persist_endpoint_called": False,
        "persisted_outcomes": False,
        "recommended_next_action": next_recommended_backfill,
        "next_recommended_backfill": next_recommended_backfill,
        "storage_health": get_storage_health(),
    }


def render_open_sports_history_coverage_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Open Sports History Coverage",
        "",
        f"1. total_rows: {report.get('total_rows')}",
        f"2. real_rows_count: {report.get('real_rows_count')}",
        f"3. synthetic_rows_count: {report.get('synthetic_rows_count')}",
        f"4. modules_with_real_rows: {', '.join(report.get('modules_with_real_rows') or []) if report.get('modules_with_real_rows') else 'none'}",
        f"5. modules_ready_for_real_tier0: {', '.join(report.get('modules_ready_for_real_tier0') or []) if report.get('modules_ready_for_real_tier0') else 'none'}",
        f"6. modules_ready_for_real_tier1: {', '.join(report.get('modules_ready_for_real_tier1') or []) if report.get('modules_ready_for_real_tier1') else 'none'}",
        f"7. real_rows_by_source: {json.dumps(report.get('real_rows_by_source') or {}, sort_keys=True)}",
        f"8. nflverse_target_seasons: {', '.join(report.get('target_seasons') or [])}",
        f"9. nflverse_seasons_validated: {', '.join(report.get('seasons_validated') or []) if report.get('seasons_validated') else 'none'}",
        f"10. nflverse_coverage_percentage: {report.get('nflverse_nfl_coverage_percentage')}",
        f"11. safety: provider_calls_attempted=0; downloads_attempted=0; provider_write=false; execution_allowed=false; raw_payload_included=false; secrets_included=false",
        "",
    ]
    return "\n".join(lines)


def render_open_sports_history_session_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Open Sports History Backfill Session",
        "",
        f"1. session_id: {report.get('session_id')}",
        f"2. mode: {report.get('mode')}",
        f"3. source_id: {report.get('source_id')}",
        f"4. status: {report.get('status')}",
        f"5. blocked_reason: {report.get('blocked_reason')}",
        f"6. completed_seasons: {', '.join(str(item) for item in report.get('completed_seasons') or []) if report.get('completed_seasons') else 'none'}",
        f"7. pending_seasons: {', '.join(str(item) for item in list(report.get('pending_seasons') or [])[:10]) if report.get('pending_seasons') else 'none'}",
        f"8. downloads_attempted: {report.get('downloads_attempted', 0)}; downloads_succeeded: {report.get('downloads_succeeded', 0)}; provider_calls_attempted: {report.get('provider_calls_attempted', 0)}",
        "9. safety: provider_write=false; execution_allowed=false; raw_payload_included=false; secrets_included=false",
        "",
    ]
    return "\n".join(lines)


def write_open_sports_history_session_report(
    report: dict[str, Any],
    *,
    base_data_dir: str | Path | None = None,
) -> dict[str, str]:
    root = _sessions_root(base_data_dir)
    created = str(report.get("created_at") or utc_now_iso())
    day = created[:10]
    sid = sanitize_filename(str(report.get("session_id") or report.get("run_id") or _session_id(str(report.get("mode") or "session"), str(report.get("source_id") or "all"))))
    latest_json = root / "latest.json"
    item_json = root / "items" / f"{sid}.json"
    daily_json = root / "daily" / f"{day}.json"
    paths = {
        "session_latest_json_path": _rel(latest_json, base_data_dir),
        "session_item_json_path": _rel(item_json, base_data_dir),
        "session_daily_json_path": _rel(daily_json, base_data_dir),
    }
    payload = {**SAFETY_FIELDS, **report, **paths, "raw_payload_included": False, "secrets_included": False}
    _atomic_write_json(latest_json, payload)
    _atomic_write_json(item_json, payload)
    _atomic_write_json(daily_json, payload)
    return paths


def write_open_sports_history_coverage_report(
    report: dict[str, Any],
    *,
    base_data_dir: str | Path | None = None,
) -> dict[str, str]:
    root = _coverage_root(base_data_dir)
    created = str(report.get("created_at") or utc_now_iso())
    run_id = sanitize_filename(str(report.get("run_id") or f"open_sports_history_coverage_{created}_{uuid4().hex[:8]}"))
    latest_json = root / "latest.json"
    latest_md = root / "latest.md"
    item_json = root / "items" / f"{run_id}.json"
    item_md = root / "items" / f"{run_id}.md"
    paths = {
        "coverage_latest_json_path": _rel(latest_json, base_data_dir),
        "coverage_latest_markdown_path": _rel(latest_md, base_data_dir),
        "coverage_item_json_path": _rel(item_json, base_data_dir),
        "coverage_item_markdown_path": _rel(item_md, base_data_dir),
    }
    payload = {**SAFETY_FIELDS, **report, **paths, "raw_payload_included": False, "secrets_included": False}
    markdown = render_open_sports_history_coverage_markdown(payload)
    _atomic_write_json(latest_json, payload)
    _atomic_write_text(latest_md, markdown)
    _atomic_write_json(item_json, payload)
    _atomic_write_text(item_md, markdown)
    return paths


def write_open_sports_history_backfill_report(
    report: dict[str, Any],
    *,
    base_data_dir: str | Path | None = None,
) -> dict[str, str]:
    if report.get("mode") == "coverage_report":
        return write_open_sports_history_coverage_report(report, base_data_dir=base_data_dir)
    return write_open_sports_history_session_report(report, base_data_dir=base_data_dir)


def _parse_season_values(values: list[str] | None) -> list[int | str] | None:
    if not values:
        return None
    seasons: list[int | str] = []
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        for part in text.split(","):
            item = part.strip()
            if not item:
                continue
            try:
                seasons.append(int(item))
            except ValueError:
                seasons.append(item)
    return seasons or None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--source-id", default=None)
    parser.add_argument("--mode", default="coverage_report")
    parser.add_argument("--season", action="append", default=[])
    parser.add_argument("--target-years", default=str(DEFAULT_TARGET_YEARS))
    parser.add_argument("--input-path", default=None)
    parser.add_argument("--max-records", default=None)
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    parser.add_argument("--no-dry-run", dest="dry_run", action="store_false")
    parser.add_argument("--allow-download", action="store_true")
    parser.add_argument("--persist-preview", action="store_true")
    parser.add_argument("--resume", dest="resume", action="store_true", default=True)
    parser.add_argument("--no-resume", dest="resume", action="store_false")
    parser.add_argument("--session-id", default=None)
    args, unknown = parser.parse_known_args(argv)

    try:
        if unknown:
            report = _error_report(
                mode=str(args.mode),
                source_id=args.source_id,
                blocked_reason="unsupported_mode",
                message=f"unsupported arguments: {' '.join(unknown)}",
                base_data_dir=None,
                session_id=args.session_id,
            )
            print(json.dumps(report, indent=2, sort_keys=True))
            return 1
        try:
            target_years = int(args.target_years)
            max_records = int(args.max_records) if args.max_records is not None else None
        except (TypeError, ValueError):
            report = _error_report(
                mode=str(args.mode),
                source_id=args.source_id,
                blocked_reason="insufficient_fields",
                message="target-years and max-records must be integers",
                base_data_dir=None,
                session_id=args.session_id,
            )
            print(json.dumps(report, indent=2, sort_keys=True))
            return 1
        report = build_open_sports_history_backfill_report(
            source_id=args.source_id,
            mode=args.mode,
            seasons=_parse_season_values(args.season),
            target_years=target_years,
            input_path=args.input_path,
            max_records=max_records,
            dry_run=args.dry_run,
            allow_download=args.allow_download,
            persist_preview=args.persist_preview,
            resume=args.resume,
            session_id=args.session_id,
        )
        paths = write_open_sports_history_backfill_report(report)
        report.update(paths)
    except Exception as exc:
        report = _error_report(
            mode=str(getattr(args, "mode", "unknown")),
            source_id=getattr(args, "source_id", None),
            blocked_reason="source_error",
            message=str(exc),
            base_data_dir=None,
            session_id=getattr(args, "session_id", None),
        )
    print(
        json.dumps(
            {
                "ok": bool(report.get("ok")),
                "status": report.get("status"),
                "mode": report.get("mode"),
                "source_id": report.get("source_id"),
                "session_id": report.get("session_id"),
                "blocked_reason": report.get("blocked_reason"),
                "records_valid": int(report.get("records_valid", 0) or 0),
                "records_rejected": int(report.get("records_rejected", 0) or 0),
                "real_rows_count": int(report.get("real_rows_count", report.get("real_records", 0)) or 0),
                "synthetic_rows_count": int(report.get("synthetic_rows_count", report.get("synthetic_records", 0)) or 0),
                "downloads_attempted": int(report.get("downloads_attempted", 0) or 0),
                "downloads_succeeded": int(report.get("downloads_succeeded", 0) or 0),
                "provider_calls_attempted": int(report.get("provider_calls_attempted", 0) or 0),
                "provider_calls_succeeded": int(report.get("provider_calls_succeeded", 0) or 0),
                "provider_calls_failed": int(report.get("provider_calls_failed", 0) or 0),
                "enabled_source_count": 0,
                "paid_source_enabled_count": 0,
                "provider_write": False,
                "execution_allowed": False,
                "raw_payload_included": False,
                "secrets_included": False,
                "session_latest_json_path": report.get("session_latest_json_path"),
                "coverage_latest_json_path": report.get("coverage_latest_json_path"),
                "coverage_latest_markdown_path": report.get("coverage_latest_markdown_path"),
                "next_recommended_session": report.get("next_recommended_session"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

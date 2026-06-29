from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.data.data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from .nfl_open_data_adapters import DEFAULT_ONE_SEASON, DEFAULT_TINY_SAMPLE_RECORDS, adapter_by_id, build_adapters
from .nfl_open_data_sources import BLOCKED_FEATURE_FAMILIES, NFL_MODULE, nfl_open_data_sources
from .open_sports_history_sources import SAFETY_FIELDS
from src.services.scheduler_config import sanitize_filename, utc_now_iso


NFL_OPEN_DATA_BACKFILL_SCHEMA_VERSION = "nfl_open_data_backfill_v1"
NFL_OPEN_DATA_COVERAGE_SCHEMA_VERSION = "nfl_open_data_coverage_matrix_v1"
SUPPORTED_MODES = {
    "metadata_check",
    "tiny_sample",
    "one_season_import",
    "full_available_backfill",
    "full_backfill",
    "resume",
    "all",
    "coverage_report",
}


def _data_root(base_data_dir: str | Path | None = None) -> Path:
    base = get_data_sources_dir() if base_data_dir is None else resolve_base_data_dir(base_data_dir) / "data_sources"
    root = base / "nfl_open_data"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _sessions_root(base_data_dir: str | Path | None = None) -> Path:
    root = _data_root(base_data_dir) / "backfill_sessions"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _coverage_root(base_data_dir: str | Path | None = None) -> Path:
    root = _data_root(base_data_dir) / "coverage_matrix"
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


def _validated_latest(source_id: str, *, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    base = resolve_base_data_dir(base_data_dir)
    path = base / "data_sources" / "nfl_open_data" / "validated" / sanitize_filename(source_id) / "latest.json"
    payload = _read_json(path)
    return payload if isinstance(payload, dict) else {}


def _feature_flags(rows: list[dict[str, Any]]) -> dict[str, bool]:
    supported_by_category: dict[str, bool] = {}
    for row in rows:
        category = str(row.get("data_category") or "")
        if not category:
            continue
        has_records = bool(int(row.get("records_validated", 0) or 0))
        supported_by_category[category] = supported_by_category.get(category, False) or has_records
    play_by_play = supported_by_category.get("play_by_play", False)
    weekly_rosters = supported_by_category.get("weekly_rosters", False)
    rosters = supported_by_category.get("rosters", False)
    return {
        "play_by_play_available": play_by_play,
        "team_stats_available": supported_by_category.get("team_stats", False),
        "weekly_player_stats_available": supported_by_category.get("player_stats", False),
        "roster_data_available": rosters,
        "weekly_rosters_available": weekly_rosters,
        "snap_counts_available": supported_by_category.get("snap_counts", False),
        "participation_available": supported_by_category.get("participation", False),
        "depth_charts_available": supported_by_category.get("depth_charts", False),
        "injury_data_available": supported_by_category.get("injuries", False),
        "pace_play_volume_available": supported_by_category.get("pace_or_play_volume", False) or play_by_play,
        "roster_continuity_available": supported_by_category.get("roster_continuity", False) or weekly_rosters,
        "nextgen_stats_available": any(
            str(row.get("source_id")) == "nflverse_nextgen_stats" and bool(int(row.get("records_validated", 0) or 0))
            for row in rows
        ),
        "player_stats_available": supported_by_category.get("player_stats", False),
        "draft_combine_available": supported_by_category.get("draft", False) and supported_by_category.get("combine", False),
        "market_data_available": supported_by_category.get("betting_lines_or_market_odds", False),
    }


def _coverage_row(source: dict[str, Any], latest: dict[str, Any]) -> dict[str, Any]:
    supported = list(source.get("likely_supported_features") or [])
    records = int(latest.get("records_validated", 0) or 0)
    metadata_status = "succeeded" if latest.get("metadata") or latest.get("gate") else "not_run"
    nested_tiny = latest.get("tiny_sample_result") if isinstance(latest.get("tiny_sample_result"), dict) else {}
    nested_one = latest.get("one_season_result") if isinstance(latest.get("one_season_result"), dict) else {}
    tiny_status = (
        "succeeded"
        if (latest.get("gate") == "tiny_sample" and latest.get("ok")) or nested_tiny.get("ok")
        else "failed"
        if nested_tiny and not nested_tiny.get("ok")
        else "not_run"
    )
    one_status = (
        "succeeded"
        if (latest.get("gate") == "one_season_import" and latest.get("ok")) or nested_one.get("ok")
        else "failed"
        if nested_one and not nested_one.get("ok")
        else "not_run"
    )
    full_status = "not_run"
    if latest.get("full_backfill_status") == "complete":
        full_status = "succeeded"
    elif latest.get("gate") == "full_available_backfill" and latest.get("ok"):
        full_status = "succeeded"
    if latest.get("full_backfill_status") == "partial_bounded_session":
        full_status = "partial_bounded_session"
    if latest.get("blocked_reason") and latest.get("full_backfill_status") != "complete":
        if latest.get("gate") == "tiny_sample":
            tiny_status = "failed"
        if latest.get("gate") == "one_season_import":
            one_status = "failed"
        if latest.get("gate") == "full_available_backfill":
            full_status = "failed"
    source_status = "validated" if records > 0 else "blocked" if source.get("blockers") or not source.get("current_phase_allowed") else "metadata_ready"
    blocker = (
        None
        if latest.get("full_backfill_status") == "complete" and not source.get("blockers")
        else latest.get("blocked_reason") or (", ".join(source.get("blockers") or []) or None)
    )
    blocked_features = list(source.get("blocked_features") or [])
    if source.get("data_category") in {"coaching"} and "coaching_staff" not in blocked_features:
        blocked_features.append("coaching_staff")
    seasons_available = list(latest.get("seasons_available") or [])
    seasons_backfilled = list(latest.get("seasons_backfilled") or [])
    seasons_missing = list(latest.get("seasons_missing") or []) or [
        season
        for season in seasons_available
        if str(season) not in {str(item) for item in seasons_backfilled}
    ]
    completion_percentage = latest.get("completion_percentage")
    if completion_percentage is None and seasons_available:
        completion_percentage = round(len(seasons_backfilled) / len(seasons_available) * 100, 2)
    return {
        "source_id": source["source_id"],
        "data_category": source.get("data_category"),
        "source_status": source_status,
        "adapter_status": latest.get("status") or "not_run",
        "metadata_check_status": metadata_status,
        "tiny_sample_status": tiny_status,
        "one_season_status": one_status,
        "full_backfill_status": full_status,
        "records_validated": records,
        "records_rejected": int(latest.get("records_rejected", 0) or 0),
        "seasons_available": seasons_available,
        "seasons_backfilled": seasons_backfilled,
        "seasons_missing": seasons_missing,
        "completion_percentage": completion_percentage,
        "fields_available": list(latest.get("fields_available") or []),
        "fields_missing": [
            field
            for field in list(source.get("expected_join_keys") or [])
            if field not in set(latest.get("fields_available") or [])
        ],
        "join_keys_available": [
            key
            for key in list(source.get("expected_join_keys") or [])
            if key in set(latest.get("fields_available") or [])
        ],
        "feature_families_supported": supported if records > 0 or latest.get("metadata") else [],
        "feature_families_blocked": sorted(set(blocked_features)),
        "current_phase_allowed": bool(source.get("current_phase_allowed")),
        "enabled": False,
        "blocker": blocker,
        "next_safe_action": latest.get("next_recommended_session") or latest.get("next_safe_action") or ("terms review" if blocker else "run explicit AllowDownload sample"),
    }


def build_nfl_open_data_coverage_matrix(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    rows = [_coverage_row(source, _validated_latest(source["source_id"], base_data_dir=base_data_dir)) for source in nfl_open_data_sources()]
    flags = _feature_flags(rows)
    records_by_source = {row["source_id"]: row["records_validated"] for row in rows}
    rejected_by_source = {row["source_id"]: row["records_rejected"] for row in rows}
    blocked_features = set(BLOCKED_FEATURE_FAMILIES)
    if flags["roster_data_available"] and flags["weekly_rosters_available"]:
        blocked_features.discard("roster_continuity")
    if flags["injury_data_available"]:
        blocked_features.discard("injury_lineup_profile")
    if flags["market_data_available"]:
        blocked_features.discard("market_price_or_odds")
    if flags["play_by_play_available"]:
        blocked_features.discard("pace_or_advanced_efficiency")
    return {
        **SAFETY_FIELDS,
        "ok": True,
        "status": "ok",
        "schema_version": NFL_OPEN_DATA_COVERAGE_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "run_id": sanitize_filename(f"nfl_open_data_coverage_matrix_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
        "module": NFL_MODULE,
        "coverage_rows": rows,
        "source_count": len(rows),
        "sources_validated": [row["source_id"] for row in rows if row["records_validated"] > 0],
        "sources_blocked": [row["source_id"] for row in rows if row["blocker"]],
        "records_validated_by_source": records_by_source,
        "records_rejected_by_source": rejected_by_source,
        "feature_availability": flags,
        "feature_families_covered": sorted(
            {feature for row in rows for feature in row.get("feature_families_supported") or []}
        ),
        "feature_families_still_blocked": sorted(blocked_features),
        "blocked_feature_families_tracked": BLOCKED_FEATURE_FAMILIES,
        "provider_calls_attempted": 0,
        "downloads_attempted": 0,
        "downloads_succeeded": 0,
        "enabled_source_count": 0,
        "paid_source_enabled_count": 0,
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
        "storage_health": get_storage_health(),
    }


def render_coverage_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# NFL Open Data Coverage Matrix",
        "",
        f"1. source_count: {report.get('source_count')}",
        f"2. sources_validated: {', '.join(report.get('sources_validated') or []) if report.get('sources_validated') else 'none'}",
        f"3. sources_blocked: {', '.join(report.get('sources_blocked') or []) if report.get('sources_blocked') else 'none'}",
        f"4. feature_families_covered: {', '.join(report.get('feature_families_covered') or []) if report.get('feature_families_covered') else 'none'}",
        f"5. feature_families_still_blocked: {', '.join(report.get('feature_families_still_blocked') or []) if report.get('feature_families_still_blocked') else 'none'}",
        f"6. feature_availability: {json.dumps(report.get('feature_availability') or {}, sort_keys=True)}",
        "7. safety: provider_calls_attempted=0; downloads_attempted=0; provider_write=false; execution_allowed=false; raw_payload_included=false; secrets_included=false",
        "",
        "## Rows",
    ]
    for row in report.get("coverage_rows") or []:
        lines.append(
            f"- {row.get('source_id')}: metadata={row.get('metadata_check_status')}; tiny={row.get('tiny_sample_status')}; one_season={row.get('one_season_status')}; full={row.get('full_backfill_status')}; records={row.get('records_validated')}; blocker={row.get('blocker') or 'none'}"
        )
    return "\n".join(lines) + "\n"


def write_coverage_matrix(report: dict[str, Any], *, base_data_dir: str | Path | None = None) -> dict[str, str]:
    root = _coverage_root(base_data_dir)
    run_id = sanitize_filename(str(report.get("run_id") or f"nfl_open_data_coverage_matrix_{uuid4().hex[:8]}"))
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
    markdown = render_coverage_markdown(payload)
    _atomic_write_json(latest_json, payload)
    _atomic_write_text(latest_md, markdown)
    _atomic_write_json(item_json, payload)
    _atomic_write_text(item_md, markdown)
    return paths


def build_nfl_open_data_backfill_report(
    *,
    source_id: str | None = None,
    mode: str = "coverage_report",
    season: int | str = DEFAULT_ONE_SEASON,
    allow_download: bool = False,
    max_records: int = DEFAULT_TINY_SAMPLE_RECORDS,
    max_full_assets: int | None = None,
    start_season: int | str | None = None,
    end_season: int | str | None = None,
    resume: bool = True,
    session_id: str | None = None,
    base_data_dir: str | Path | None = None,
) -> dict[str, Any]:
    if mode == "full_backfill":
        mode = "full_available_backfill"
    if mode == "resume":
        mode = "full_available_backfill"
        resume = True
    if mode not in SUPPORTED_MODES:
        return _blocked_session(mode=mode, source_id=source_id, blocker="unsupported_source", base_data_dir=base_data_dir)
    if mode == "coverage_report":
        return build_nfl_open_data_coverage_matrix(base_data_dir=base_data_dir)
    adapters = [adapter_by_id(source_id)] if source_id else build_adapters()
    adapters = [adapter for adapter in adapters if adapter is not None]
    session_id = sanitize_filename(f"nfl_open_data_{mode}_{source_id or 'all'}_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}")
    results: list[dict[str, Any]] = []
    for adapter in adapters:
        if mode == "metadata_check":
            result = adapter.build_compact_report()
        elif mode == "tiny_sample":
            result = adapter.run_tiny_sample(allow_download=allow_download, max_records=max_records)
        elif mode == "one_season_import":
            result = adapter.run_one_season_import(season=season, allow_download=allow_download, safe_override=True)
        elif mode == "full_available_backfill":
            result = adapter.run_full_available_backfill(
                allow_download=allow_download,
                one_season_passed=True,
                max_full_assets=max_full_assets,
                resume=resume,
                start_season=start_season,
                end_season=end_season,
                base_data_dir=base_data_dir,
                session_id=session_id,
            )
        else:
            tiny = adapter.run_tiny_sample(allow_download=allow_download, max_records=max_records)
            if tiny.get("gate"):
                adapter.write_compact_validated_rows(tiny, base_data_dir=base_data_dir)
            one = adapter.run_one_season_import(season=season, allow_download=allow_download, tiny_sample_passed=bool(tiny.get("ok")))
            if one.get("gate"):
                adapter.write_compact_validated_rows(one, base_data_dir=base_data_dir)
            full = adapter.run_full_available_backfill(
                allow_download=allow_download,
                one_season_passed=bool(one.get("ok")),
                max_full_assets=max_full_assets,
                resume=resume,
                start_season=start_season,
                end_season=end_season,
                base_data_dir=base_data_dir,
                session_id=session_id,
            )
            result = {
                **full,
                "tiny_sample_result": _result_summary(tiny),
                "one_season_result": _result_summary(one),
            }
        if result.get("gate"):
            adapter.write_compact_validated_rows(result, base_data_dir=base_data_dir)
        results.append(result)
    downloads_attempted = sum(int(result.get("downloads_attempted", 0) or 0) for result in results)
    downloads_succeeded = sum(int(result.get("downloads_succeeded", 0) or 0) for result in results)
    provider_calls_attempted = sum(int(result.get("provider_calls_attempted", 0) or 0) for result in results)
    provider_calls_succeeded = sum(int(result.get("provider_calls_succeeded", 0) or 0) for result in results)
    records_validated = sum(int(result.get("records_validated", 0) or 0) for result in results)
    records_rejected = sum(int(result.get("records_rejected", 0) or 0) for result in results)
    blocker_counts = Counter(str(result.get("blocked_reason")) for result in results if result.get("blocked_reason"))
    known_blockers = {
        "terms_review_required",
        "source_not_current_phase_allowed",
        "sports_reference_scraping_blocked",
        "source_not_available",
        "metadata_not_available",
        "tiny_sample_required",
        "one_season_required",
        "provider_error",
        "source_timeout",
        "field_shape_unverified",
    }
    unknown_blockers = sorted({blocker for blocker in blocker_counts if blocker not in known_blockers})
    ok = records_validated > 0 and not unknown_blockers
    return {
        **SAFETY_FIELDS,
        "ok": ok,
        "status": "ok_with_blockers" if blocker_counts and ok else "ok" if ok else "blocked",
        "schema_version": NFL_OPEN_DATA_BACKFILL_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "run_id": session_id,
        "session_id": session_id,
        "mode": mode,
        "source_id": source_id,
        "season": str(season),
        "allow_download": bool(allow_download),
        "max_records": int(max_records),
        "max_full_assets": max_full_assets,
        "results": [_strip_heavy(result) for result in results],
        "records_validated": records_validated,
        "records_rejected": records_rejected,
        "downloads_attempted": downloads_attempted,
        "downloads_succeeded": downloads_succeeded,
        "provider_calls_attempted": provider_calls_attempted,
        "provider_calls_succeeded": provider_calls_succeeded,
        "provider_calls_failed": max(0, provider_calls_attempted - provider_calls_succeeded),
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "unknown_blockers": unknown_blockers,
        "enabled_source_count": 0,
        "paid_source_enabled_count": 0,
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
        "storage_health": get_storage_health(),
    }


def _blocked_session(
    *,
    mode: str,
    source_id: str | None,
    blocker: str,
    base_data_dir: str | Path | None,
) -> dict[str, Any]:
    return {
        **SAFETY_FIELDS,
        "ok": False,
        "status": "blocked",
        "schema_version": NFL_OPEN_DATA_BACKFILL_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "run_id": sanitize_filename(f"nfl_open_data_{mode}_{source_id or 'all'}_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
        "session_id": None,
        "mode": mode,
        "source_id": source_id,
        "blocked_reason": blocker,
        "results": [],
        "records_validated": 0,
        "records_rejected": 0,
        "downloads_attempted": 0,
        "downloads_succeeded": 0,
        "provider_calls_attempted": 0,
        "provider_calls_succeeded": 0,
        "provider_calls_failed": 0,
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
        "storage_health": get_storage_health(),
    }


def _result_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(result.get("ok")),
        "status": result.get("status"),
        "gate": result.get("gate"),
        "blocked_reason": result.get("blocked_reason"),
        "records_validated": int(result.get("records_validated", 0) or 0),
        "downloads_attempted": int(result.get("downloads_attempted", 0) or 0),
        "downloads_succeeded": int(result.get("downloads_succeeded", 0) or 0),
    }


def _strip_heavy(result: dict[str, Any]) -> dict[str, Any]:
    safe = dict(result)
    if len(list(safe.get("sample_rows") or [])) > 5:
        safe["sample_rows"] = list(safe.get("sample_rows") or [])[:5]
    return safe


def render_session_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# NFL Open Data Backfill Session",
            "",
            f"1. session_id: {report.get('session_id')}",
            f"2. mode: {report.get('mode')}",
            f"3. source_id: {report.get('source_id') or 'all'}",
            f"4. records_validated: {report.get('records_validated')}",
            f"5. records_rejected: {report.get('records_rejected')}",
            f"6. downloads_attempted: {report.get('downloads_attempted')}; downloads_succeeded: {report.get('downloads_succeeded')}; provider_calls_attempted: {report.get('provider_calls_attempted')}",
            f"7. blockers: {json.dumps(report.get('blocker_counts') or {}, sort_keys=True)}",
            "8. safety: provider_write=false; execution_allowed=false; raw_payload_included=false; secrets_included=false",
            "",
        ]
    )


def write_nfl_open_data_backfill_report(
    report: dict[str, Any],
    *,
    base_data_dir: str | Path | None = None,
) -> dict[str, str]:
    if report.get("schema_version") == NFL_OPEN_DATA_COVERAGE_SCHEMA_VERSION:
        return write_coverage_matrix(report, base_data_dir=base_data_dir)
    root = _sessions_root(base_data_dir)
    created = str(report.get("created_at") or utc_now_iso())
    day = created[:10]
    session_id = sanitize_filename(str(report.get("session_id") or report.get("run_id") or f"nfl_open_data_session_{uuid4().hex[:8]}"))
    latest_json = root / "latest.json"
    item_json = root / "items" / f"{session_id}.json"
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
    latest_md = root / "latest.md"
    _atomic_write_text(latest_md, render_session_markdown(payload))
    paths["session_latest_markdown_path"] = _rel(latest_md, base_data_dir)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-id", default=None)
    parser.add_argument("--mode", default="coverage_report")
    parser.add_argument("--season", default=str(DEFAULT_ONE_SEASON))
    parser.add_argument("--max-records", type=int, default=DEFAULT_TINY_SAMPLE_RECORDS)
    parser.add_argument("--allow-download", action="store_true")
    parser.add_argument("--max-full-assets", type=int, default=None)
    parser.add_argument("--start-season", type=int, default=None)
    parser.add_argument("--end-season", type=int, default=None)
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--resume", dest="resume", action="store_true", default=True)
    parser.add_argument("--no-resume", dest="resume", action="store_false")
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    report = build_nfl_open_data_backfill_report(
        source_id=args.source_id,
        mode=args.mode,
        season=args.season,
        allow_download=args.allow_download,
        max_records=args.max_records,
        max_full_assets=args.max_full_assets,
        start_season=args.start_season,
        end_season=args.end_season,
        resume=args.resume,
        session_id=args.session_id,
    )
    paths: dict[str, Any] = {}
    if args.persist or args.mode == "coverage_report":
        paths = write_nfl_open_data_backfill_report(report)
        report.update(paths)
    print(
        json.dumps(
            {
                "ok": bool(report.get("ok")),
                "status": report.get("status"),
                "mode": report.get("mode") or "coverage_report",
                "source_id": report.get("source_id"),
                "records_validated": int(report.get("records_validated", 0) or 0),
                "records_rejected": int(report.get("records_rejected", 0) or 0),
                "downloads_attempted": int(report.get("downloads_attempted", 0) or 0),
                "downloads_succeeded": int(report.get("downloads_succeeded", 0) or 0),
                "provider_calls_attempted": int(report.get("provider_calls_attempted", 0) or 0),
                "provider_calls_succeeded": int(report.get("provider_calls_succeeded", 0) or 0),
                "enabled_source_count": 0,
                "paid_source_enabled_count": 0,
                "provider_write": False,
                "execution_allowed": False,
                "raw_payload_included": False,
                "secrets_included": False,
                "session_latest_json_path": paths.get("session_latest_json_path"),
                "coverage_latest_json_path": paths.get("coverage_latest_json_path"),
                "coverage_latest_markdown_path": paths.get("coverage_latest_markdown_path"),
                "feature_availability": report.get("feature_availability"),
                "feature_families_still_blocked": report.get("feature_families_still_blocked"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

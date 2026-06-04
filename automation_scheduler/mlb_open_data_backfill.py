from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any
from uuid import uuid4

from .data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from .mlb_open_data_adapters import DEFAULT_ONE_SEASON, DEFAULT_TINY_SAMPLE_RECORDS, adapter_by_id, build_adapters
from .mlb_open_data_sources import BLOCKED_FEATURE_FAMILIES, MLB_MODULE, mlb_open_data_sources
from .open_sports_history_sources import SAFETY_FIELDS
from .scheduler_config import sanitize_filename, utc_now_iso
from .mlb_open_data_common import mlb_safe_payload


MLB_OPEN_DATA_BACKFILL_SCHEMA_VERSION = "mlb_open_data_backfill_v1"
MLB_OPEN_DATA_COVERAGE_SCHEMA_VERSION = "mlb_open_data_coverage_matrix_v1"
SUPPORTED_MODES = {
    "metadata_check",
    "tiny_sample",
    "one_season_import",
    "small_window_import",
    "full_available_backfill",
    "full_backfill",
    "resume",
    "all",
    "coverage_report",
}


def _data_root(base_data_dir: str | Path | None = None) -> Path:
    base = get_data_sources_dir() if base_data_dir is None else resolve_base_data_dir(base_data_dir) / "data_sources"
    root = base / "mlb_open_data"
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
    path = base / "data_sources" / "mlb_open_data" / "validated" / sanitize_filename(source_id) / "latest.json"
    payload = _read_json(path)
    return payload if isinstance(payload, dict) else {}


def _feature_flags(rows: list[dict[str, Any]]) -> dict[str, bool]:
    by_source: dict[str, bool] = {}
    by_category: dict[str, bool] = {}
    for row in rows:
        source_id = str(row.get("source_id") or "")
        category = str(row.get("data_category") or "")
        records = int(row.get("records_validated", 0) or 0)
        if source_id:
            by_source[source_id] = by_source.get(source_id, False) or records > 0
        if category:
            by_category[category] = by_category.get(category, False) or records > 0
    return {
        "mlb_team_game_run_profile_available": by_source.get("team_stats_lahman", False) or by_source.get("standings_mlb_stats_api", False),
        "mlb_batting_profile_available": by_source.get("batting_stats_lahman", False),
        "mlb_pitching_profile_available": by_source.get("pitching_stats_lahman", False),
        "mlb_fielding_profile_available": by_source.get("fielding_stats_lahman", False),
        "mlb_bullpen_usage_available": by_source.get("bullpen_usage_mlb_stats_api", False),
        "mlb_starting_pitcher_profile_available": by_source.get("starting_pitchers_mlb_stats_api", False) or by_source.get("probable_pitchers_mlb_stats_api", False),
        "mlb_roster_continuity_available": by_source.get("rosters_mlb_stats_api", False),
        "mlb_lineup_stability_available": by_source.get("lineups_mlb_stats_api", False),
        "mlb_player_availability_available": by_source.get("injuries_mlb_stats_api", False),
        "mlb_park_factor_available": by_source.get("park_factors_lahman", False),
        "mlb_stadium_weather_available": by_source.get("weather_mlb_stats_api", False) or by_source.get("stadiums_lahman", False),
        "mlb_postseason_context_available": by_source.get("postseason_labels_retrosheet", False),
        "mlb_manager_continuity_available": by_source.get("managers_coaches_mlb_stats_api", False),
        "mlb_team_identity_available": by_source.get("franchises_lahman", False) or by_source.get("player_master_lahman", False),
        "mlb_people_identifier_crosswalk_available": by_source.get("people_identifiers_chadwick", False),
        "mlb_pitch_quality_candidates_available": False,
        "mlb_batted_ball_quality_candidates_available": False,
        "mlb_market_odds_available": by_category.get("market_odds", False),
        "mlb_structured_seed_available": by_source.get("wikidata_mlb_seed", False),
    }


def _coverage_row(source: dict[str, Any], latest: dict[str, Any]) -> dict[str, Any]:
    supported = list(source.get("likely_supported_features") or [])
    blocked_features = list(source.get("blocked_features") or [])
    records = int(latest.get("records_validated", 0) or 0)
    metadata_status = "succeeded" if latest.get("metadata") or latest.get("gate") else "not_run"
    nested_tiny = latest.get("sample_rows") if isinstance(latest.get("sample_rows"), list) and latest.get("gate") == "tiny_sample" else []
    tiny_status = "succeeded" if (latest.get("gate") == "tiny_sample" and latest.get("ok")) or records > 0 else "failed" if latest.get("blocked_reason") else "not_run"
    one_status = "succeeded" if latest.get("gate") == "one_season_import" and latest.get("ok") else "not_run"
    full_status = "succeeded" if latest.get("status") == "full_backfill_complete" or latest.get("full_backfill_status") == "complete" else "partial_bounded_session" if latest.get("full_backfill_status") == "partial_bounded_session" else "not_run"
    source_status = "validated" if records > 0 else "blocked" if source.get("blockers") or not source.get("current_phase_allowed") else "metadata_ready"
    blocker = latest.get("blocked_reason") or (", ".join(source.get("blockers") or []) or None)
    seasons_available = list(latest.get("seasons_available") or [])
    seasons_backfilled = list(latest.get("seasons_backfilled") or [])
    seasons_missing = list(latest.get("seasons_missing") or []) or [season for season in seasons_available if str(season) not in {str(item) for item in seasons_backfilled}]
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


def build_mlb_open_data_coverage_matrix(*, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    rows = [_coverage_row(source, _validated_latest(source["source_id"], base_data_dir=base_data_dir)) for source in mlb_open_data_sources()]
    flags = _feature_flags(rows)
    records_by_source = {row["source_id"]: row["records_validated"] for row in rows}
    rejected_by_source = {row["source_id"]: row["records_rejected"] for row in rows}
    blocked_features = set(BLOCKED_FEATURE_FAMILIES)
    if flags["mlb_batting_profile_available"]:
        blocked_features.discard("batting_profile")
    if flags["mlb_pitching_profile_available"]:
        blocked_features.discard("pitching_profile")
    if flags["mlb_fielding_profile_available"]:
        blocked_features.discard("fielding_profile")
    if flags["mlb_team_game_run_profile_available"]:
        blocked_features.discard("team_game_run_profile")
    return mlb_safe_payload(
        {
            "ok": True,
            "status": "ok",
            "schema_version": MLB_OPEN_DATA_COVERAGE_SCHEMA_VERSION,
            "created_at": utc_now_iso(),
            "run_id": sanitize_filename(f"mlb_open_data_coverage_matrix_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
            "module": MLB_MODULE,
            "coverage_rows": rows,
            "source_count": len(rows),
            "sources_validated": [row["source_id"] for row in rows if row["records_validated"] > 0],
            "sources_blocked": [row["source_id"] for row in rows if row["blocker"]],
            "records_validated_by_source": records_by_source,
            "records_rejected_by_source": rejected_by_source,
            "feature_availability": flags,
            "feature_families_covered": sorted({feature for row in rows for feature in row.get("feature_families_supported") or []}),
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
    )


def render_coverage_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# MLB Open Data Coverage Matrix",
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
    run_id = sanitize_filename(str(report.get("run_id") or f"mlb_open_data_coverage_matrix_{uuid4().hex[:8]}"))
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


def _session_result(
    adapter: Any,
    *,
    source_id: str,
    mode: str,
    season: int | str = DEFAULT_ONE_SEASON,
    allow_download: bool = False,
    max_records: int = DEFAULT_TINY_SAMPLE_RECORDS,
    input_path: str | None = None,
    allow_structured_seed: bool = False,
    allow_manual_import: bool = False,
    max_full_assets: int | None = None,
    start_season: int | str | None = None,
    end_season: int | str | None = None,
) -> dict[str, Any]:
    if mode == "metadata_check":
        return adapter.run_metadata_check()
    if mode == "tiny_sample":
        return adapter.run_tiny_sample(
            allow_download=allow_download,
            max_records=max_records,
            input_path=input_path,
            allow_structured_seed=allow_structured_seed,
            allow_manual_import=allow_manual_import,
        )
    if mode == "one_season_import":
        return adapter.run_one_season_import(
            season=season,
            allow_download=allow_download,
            input_path=input_path,
            allow_structured_seed=allow_structured_seed,
            allow_manual_import=allow_manual_import,
        )
    if mode == "small_window_import":
        return adapter.run_small_window_import(
            allow_download=allow_download,
            input_path=input_path,
            allow_structured_seed=allow_structured_seed,
            allow_manual_import=allow_manual_import,
        )
    if mode in {"full_available_backfill", "full_backfill", "resume"}:
        seasons = None
        if start_season is not None and end_season is not None:
            try:
                start = int(start_season)
                end = int(end_season)
                seasons = [str(year) for year in range(min(start, end), max(start, end) + 1)]
            except (TypeError, ValueError):
                seasons = None
        return adapter.run_full_available_backfill(
            allow_download=allow_download,
            input_path=input_path,
            allow_structured_seed=allow_structured_seed,
            allow_manual_import=allow_manual_import,
            max_full_assets=max_full_assets,
            seasons=seasons,
        )
    return adapter.run_metadata_check()


def build_mlb_open_data_backfill_report(
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
    input_path: str | None = None,
    allow_structured_seed: bool = False,
    allow_manual_import: bool = False,
    base_data_dir: str | Path | None = None,
) -> dict[str, Any]:
    if mode == "full_backfill":
        mode = "full_available_backfill"
    if mode == "resume":
        mode = "full_available_backfill"
        resume = True
    if mode not in SUPPORTED_MODES:
        return mlb_safe_payload(
            {
                "ok": False,
                "status": "blocked",
                "schema_version": MLB_OPEN_DATA_BACKFILL_SCHEMA_VERSION,
                "created_at": utc_now_iso(),
                "run_id": sanitize_filename(f"mlb_open_data_backfill_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
                "module": MLB_MODULE,
                "mode": mode,
                "blocked_reason": "unsupported_source",
                "provider_calls_attempted": 0,
                "downloads_attempted": 0,
                "downloads_succeeded": 0,
                "enabled_source_count": 0,
                "paid_source_enabled_count": 0,
                "provider_write": False,
                "execution_allowed": False,
            }
        )
    if mode == "coverage_report":
        return build_mlb_open_data_coverage_matrix(base_data_dir=base_data_dir)
    if mode == "all":
        adapters = build_adapters()
        source_reports = [adapter.run_metadata_check() for adapter in adapters]
        source_status_counts = Counter(str(report.get("status") or "unknown") for report in source_reports)
        return mlb_safe_payload(
            {
                "ok": True,
                "status": "ok",
                "schema_version": MLB_OPEN_DATA_BACKFILL_SCHEMA_VERSION,
                "created_at": utc_now_iso(),
                "run_id": sanitize_filename(f"mlb_open_data_backfill_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
                "module": MLB_MODULE,
                "mode": mode,
                "session_id": session_id or None,
                "source_reports": source_reports,
                "source_count": len(source_reports),
                "source_status_counts": dict(sorted(source_status_counts.items())),
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
        )
    if source_id is None or not str(source_id).strip():
        return mlb_safe_payload(
            {
                "ok": False,
                "status": "blocked",
                "schema_version": MLB_OPEN_DATA_BACKFILL_SCHEMA_VERSION,
                "created_at": utc_now_iso(),
                "run_id": sanitize_filename(f"mlb_open_data_backfill_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
                "module": MLB_MODULE,
                "mode": mode,
                "blocked_reason": "missing_source_id",
                "provider_calls_attempted": 0,
                "downloads_attempted": 0,
                "downloads_succeeded": 0,
                "enabled_source_count": 0,
                "paid_source_enabled_count": 0,
                "provider_write": False,
                "execution_allowed": False,
            }
        )
    adapter = adapter_by_id(source_id)
    if adapter is None:
        return mlb_safe_payload(
            {
                "ok": False,
                "status": "blocked",
                "schema_version": MLB_OPEN_DATA_BACKFILL_SCHEMA_VERSION,
                "created_at": utc_now_iso(),
                "run_id": sanitize_filename(f"mlb_open_data_backfill_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
                "module": MLB_MODULE,
                "mode": mode,
                "source_id": source_id,
                "blocked_reason": "unsupported_source",
                "provider_calls_attempted": 0,
                "downloads_attempted": 0,
                "downloads_succeeded": 0,
                "enabled_source_count": 0,
                "paid_source_enabled_count": 0,
                "provider_write": False,
                "execution_allowed": False,
            }
        )
    report = _session_result(
        adapter,
        source_id=source_id,
        mode=mode,
        season=season,
        allow_download=allow_download,
        max_records=max_records,
        input_path=input_path,
        allow_structured_seed=allow_structured_seed,
        allow_manual_import=allow_manual_import,
        max_full_assets=max_full_assets,
        start_season=start_season,
        end_season=end_season,
    )
    report["mode"] = mode
    report["source_id"] = source_id
    report["session_id"] = session_id or report.get("run_id")
    report["resume"] = bool(resume)
    return report


def _render_session_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# MLB Open Data Backfill Session",
        "",
        f"1. mode: {report.get('mode')}",
        f"2. source_id: {report.get('source_id') or 'none'}",
        f"3. status: {report.get('status')}",
        f"4. records_validated: {report.get('records_validated')}",
        f"5. records_rejected: {report.get('records_rejected')}",
        f"6. fields_available: {', '.join(report.get('fields_available') or []) if report.get('fields_available') else 'none'}",
        f"7. seasons_backfilled: {', '.join(report.get('seasons_backfilled') or []) if report.get('seasons_backfilled') else 'none'}",
        "8. safety: provider_write=false; execution_allowed=false; raw_payload_included=false; raw_html_persisted=false; secrets_included=false",
        "",
    ]
    return "\n".join(lines) + "\n"


def write_mlb_open_data_backfill_report(report: dict[str, Any], *, base_data_dir: str | Path | None = None) -> dict[str, str]:
    if "coverage_rows" in report:
        return write_coverage_matrix(report, base_data_dir=base_data_dir)
    root = _sessions_root(base_data_dir)
    run_id = sanitize_filename(str(report.get("run_id") or f"mlb_open_data_backfill_{uuid4().hex[:8]}"))
    latest_json = root / "latest.json"
    latest_md = root / "latest.md"
    item_json = root / "items" / f"{run_id}.json"
    item_md = root / "items" / f"{run_id}.md"
    paths = {
        "session_latest_json_path": _rel(latest_json, base_data_dir),
        "session_latest_markdown_path": _rel(latest_md, base_data_dir),
        "session_item_json_path": _rel(item_json, base_data_dir),
        "session_item_markdown_path": _rel(item_md, base_data_dir),
    }
    payload = {**SAFETY_FIELDS, **report, **paths, "raw_payload_included": False, "secrets_included": False}
    markdown = _render_session_markdown(payload)
    _atomic_write_json(latest_json, payload)
    _atomic_write_text(latest_md, markdown)
    _atomic_write_json(item_json, payload)
    _atomic_write_text(item_md, markdown)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-id", default="")
    parser.add_argument("--mode", default="coverage_report")
    parser.add_argument("--season", default=str(DEFAULT_ONE_SEASON))
    parser.add_argument("--max-records", type=int, default=DEFAULT_TINY_SAMPLE_RECORDS)
    parser.add_argument("--allow-download", action="store_true")
    parser.add_argument("--max-full-assets", type=int, default=0)
    parser.add_argument("--start-season", default=None)
    parser.add_argument("--end-season", default=None)
    parser.add_argument("--session-id", default="")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--allow-structured-seed", action="store_true")
    parser.add_argument("--allow-manual-import", action="store_true")
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    report = build_mlb_open_data_backfill_report(
        source_id=args.source_id or None,
        mode=args.mode,
        season=args.season,
        allow_download=args.allow_download,
        max_records=args.max_records,
        max_full_assets=args.max_full_assets or None,
        start_season=args.start_season,
        end_season=args.end_season,
        resume=args.resume,
        session_id=args.session_id or None,
        allow_structured_seed=args.allow_structured_seed,
        allow_manual_import=args.allow_manual_import,
    )
    paths: dict[str, str] = {}
    if args.persist:
        paths = write_mlb_open_data_backfill_report(report)
        report.update(paths)
    print(
        json.dumps(
            {
                "ok": bool(report.get("ok")),
                "status": report.get("status"),
                "source_id": report.get("source_id"),
                "mode": report.get("mode"),
                "blocked_reason": report.get("blocked_reason"),
                "records_validated": int(report.get("records_validated", 0) or 0),
                "records_rejected": int(report.get("records_rejected", 0) or 0),
                "fields_available": report.get("fields_available"),
                "seasons_backfilled": report.get("seasons_backfilled"),
                "downloads_attempted": int(report.get("downloads_attempted", 0) or 0),
                "downloads_succeeded": int(report.get("downloads_succeeded", 0) or 0),
                "provider_calls_attempted": int(report.get("provider_calls_attempted", 0) or 0),
                "enabled_source_count": 0,
                "paid_source_enabled_count": 0,
                "provider_write": False,
                "execution_allowed": False,
                "raw_payload_included": False,
                "raw_html_persisted": False,
                "secrets_included": False,
                "latest_json_path": paths.get("session_latest_json_path") or paths.get("coverage_latest_json_path"),
                "latest_markdown_path": paths.get("session_latest_markdown_path") or paths.get("coverage_latest_markdown_path"),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

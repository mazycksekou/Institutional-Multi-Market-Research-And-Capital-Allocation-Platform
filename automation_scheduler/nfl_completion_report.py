from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from .data_paths import get_data_sources_dir, get_storage_health, resolve_base_data_dir
from .nfl_coaching_sources import nfl_coaching_sources
from .nfl_historical_pattern_lab import build_nfl_historical_pattern_lab_report, build_validation_guard_summary
from .nfl_open_data_adapters import build_adapters
from .nfl_open_data_backfill import build_nfl_open_data_backfill_report
from .nfl_open_data_feature_builders import build_expanded_feature_readiness, build_nfl_feature_builder_report
from .nfl_coaching_feature_builders import build_nfl_coaching_feature_report
from .nfl_open_data_feature_readiness import build_nfl_feature_readiness_report
from .nfl_open_data_source_exhaustion import build_nfl_source_exhaustion_report
from .nfl_open_data_sources import nfl_open_data_sources
from .nfl_coaching_sources import build_nfl_coaching_source_report
from .open_sports_history_sources import SAFETY_FIELDS
from .scheduler_config import sanitize_filename, utc_now_iso
from .nfl_cutoff_week_features import cutoff_feature_availability_summary


NFL_COMPLETION_REPORT_SCHEMA_VERSION = "nfl_completion_final_report_v1"
NFL_MODULE = "americanfootball_nfl"
REPORT_ROOT = Path("reports")


def _stable_hash(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _file_hash(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _git_commit_hash() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return ""


def _json_field(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(key): _json_field(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_field(item) for item in value]
    return str(value)


def _latest_validated_report(source_id: str, *, base: Path) -> dict[str, Any]:
    path = base / "data_sources" / "nfl_open_data" / "validated" / sanitize_filename(source_id) / "latest.json"
    return _read_json(path)


def _latest_coaching_report(source_id: str, *, base: Path) -> dict[str, Any]:
    path = base / "data_sources" / "nfl_open_data" / "coaching" / "validated" / sanitize_filename(source_id) / "latest.json"
    return _read_json(path)


def _season_coverage_from_report(report: dict[str, Any]) -> list[str]:
    seasons = list(report.get("seasons_backfilled") or report.get("seasons_covered") or report.get("seasons_available") or [])
    return [str(season) for season in seasons if str(season).strip()]


def _date_coverage_from_rows(rows: Iterable[dict[str, Any]]) -> dict[str, str]:
    candidates: list[str] = []
    for row in rows:
        for key in ("event_date", "game_date", "start_date", "end_date", "source_effective_date", "source_updated_date", "created_at"):
            value = row.get(key)
            if isinstance(value, str) and value:
                candidates.append(value)
    candidates = sorted(set(candidates))
    return {
        "earliest_observed": candidates[0] if candidates else "",
        "latest_observed": candidates[-1] if candidates else "",
    }


def _source_table_row(
    *,
    sport: str,
    source: dict[str, Any],
    report: dict[str, Any],
    policy_status: str,
    retrieval_method: str,
    fallback: str,
    model_eligible: bool,
    cutoff_safe: bool,
    last_attempted_at: str | None = None,
    last_success_at: str | None = None,
    manifest_hash: str | None = None,
) -> dict[str, Any]:
    records = int(report.get("records_validated", 0) or 0)
    rejected = int(report.get("records_rejected", 0) or 0)
    seasons = _season_coverage_from_report(report)
    date_coverage = report.get("date_coverage") or {}
    schema_hash = _stable_hash(
        {
            "module": sport,
            "source_id": source.get("source_id"),
            "source_family": source.get("source_family"),
            "data_category": source.get("data_category"),
            "retrieval_method": retrieval_method,
            "policy_status": policy_status,
            "expected_join_keys": source.get("expected_join_keys") or source.get("target_fields") or [],
        }
    )
    data_hash = manifest_hash or _stable_hash(_json_field(report.get("sample_rows") or report.get("rejected") or []))
    return {
        "sport": sport,
        "source_id": source.get("source_id"),
        "source_family": source.get("source_family"),
        "policy_status": policy_status,
        "retrieval_method": retrieval_method,
        "license_or_terms_note": source.get("license_status") or source.get("terms_review_status") or source.get("safety_notes") or "",
        "season_coverage": seasons,
        "date_coverage": date_coverage if isinstance(date_coverage, dict) else {"earliest_observed": "", "latest_observed": ""},
        "record_count": records,
        "rejected_count": rejected,
        "schema_hash": schema_hash,
        "data_hash_or_manifest_hash": data_hash,
        "last_attempted_at": last_attempted_at or report.get("created_at") or "",
        "last_success_at": last_success_at or (report.get("created_at") if records > 0 else ""),
        "blocker": report.get("blocked_reason") or source.get("blocker") or "",
        "fallback": fallback,
        "model_eligible": bool(model_eligible),
        "cutoff_safe": bool(cutoff_safe),
    }


def _coaching_manifest_hash(base: Path) -> str:
    path = base / "manual_imports" / "nfl_coaching" / "team_wikidata_qids.csv"
    return _file_hash(path)


def _source_family_tables(*, base: Path) -> list[dict[str, Any]]:
    open_sources = nfl_open_data_sources()
    coaching_sources = nfl_coaching_sources()
    open_reports = {source["source_id"]: _latest_validated_report(source["source_id"], base=base) for source in open_sources}
    coaching_reports = {source["source_id"]: _latest_coaching_report(source["source_id"], base=base) for source in coaching_sources}
    rows: list[dict[str, Any]] = []

    for source in open_sources:
        report = open_reports[source["source_id"]]
        records = int(report.get("records_validated", 0) or 0)
        if source["source_id"] == "nflverse_play_by_play":
            fallback = "nflverse_release_download"
        elif source["source_id"] == "nflverse_coaching_research":
            fallback = "structured_open_source_unverified"
        elif source["source_id"] == "nflverse_pfr_advstats_blocked":
            fallback = "blocked_terms_review"
        elif source["source_id"] == "nflverse_ftn_charting_blocked":
            fallback = "blocked_terms_review"
        else:
            fallback = "open_release_download"
        rows.append(
            _source_table_row(
                sport=NFL_MODULE,
                source=source,
                report=report,
                policy_status="populated" if records > 0 else ("blocked" if source.get("approval_status") == "blocked" or source.get("current_phase_allowed") is False else "approved_empty"),
                retrieval_method=str(source.get("source_access_type") or "open_release"),
                fallback=fallback,
                model_eligible=records > 0 and source.get("current_phase_allowed", False) and source.get("approval_status") != "blocked",
                cutoff_safe=records > 0 and source.get("data_category") not in {"betting_lines_or_market_odds", "advanced_efficiency"},
                last_attempted_at=report.get("created_at"),
                last_success_at=report.get("created_at") if records > 0 else "",
            )
        )

    for source in coaching_sources:
        report = coaching_reports[source["source_id"]]
        records = int(report.get("records_validated", 0) or 0)
        if source["source_id"] == "wikidata_coaching_seed":
            fallback = "wikidata_entity_api"
        elif source["source_id"] == "wikidata_entity_api":
            fallback = "wikidata_entity_api"
        elif source["source_id"] == "wikidata_local_dump":
            fallback = "wikidata_local_dump"
        elif source["source_id"] == "wikipedia_coaching_tables":
            fallback = "wikipedia_structured_tables"
        elif source["source_id"] == "wikipedia_coaching_seed":
            fallback = "wikipedia_supplemental_only"
        elif source["source_id"] == "manual_csv_import":
            fallback = "manual_csv_import"
        elif source["source_id"] in {"official_team_staff_pages", "official_team_press_releases", "official_nfl_staff_or_news_pages", "team_sitemaps"}:
            fallback = "oxylabs_paid_retrieval" if source["current_phase_allowed"] else "blocked_terms_review"
        else:
            fallback = "blocked_policy"
        manifest_hash = _coaching_manifest_hash(base) if source["source_id"] in {"wikidata_entity_api", "manual_csv_import"} else ""
        rows.append(
            _source_table_row(
                sport=NFL_MODULE,
                source=source,
                report=report,
                policy_status="populated" if records > 0 else ("blocked" if source.get("approval_status") == "blocked" or source.get("current_phase_allowed") is False or report.get("blocked_reason") else "approved_empty"),
                retrieval_method=str(source.get("source_access_type") or "structured_open_data"),
                fallback=fallback,
                model_eligible=records > 0 and source.get("current_phase_allowed", False) and not source.get("supplemental_only"),
                cutoff_safe=records > 0 and source.get("source_family") not in {"official_team_staff_pages", "official_team_press_releases", "official_nfl_staff_or_news_pages"},
                last_attempted_at=report.get("created_at"),
                last_success_at=report.get("created_at") if records > 0 else "",
                manifest_hash=manifest_hash,
            )
        )
    return rows


def _feature_group_summary(*, base: Path) -> dict[str, Any]:
    builder_report = build_nfl_feature_builder_report(base_data_dir=base)
    expanded = build_expanded_feature_readiness(base_data_dir=base)
    coaching_feature_report = build_nfl_coaching_feature_report(base_data_dir=base)
    guard = build_validation_guard_summary(base_data_dir=base)
    cutoff_summary = cutoff_feature_availability_summary()
    feature_groups_built = sorted(
        set(builder_report.get("feature_builders_added") or []) | set(coaching_feature_report.get("coaching_feature_builders_available") or [])
    )
    feature_groups_blocked = sorted(
        {
            *(row.get("feature_name") for row in builder_report.get("feature_builders_blocked") or []),
            *(row.get("feature_name") for row in coaching_feature_report.get("coaching_feature_builder_blockers") or []),
            *guard.get("blocked_by_leakage", []),
            *guard.get("blocked_by_cutoff", []),
            *guard.get("blocked_by_future_data", []),
            *guard.get("blocked_by_missing_provenance", []),
        }
    )
    feature_groups_model_eligible = sorted(
        set(feature_groups_built) | set(expanded.get("expanded_regular_season_features_candidate") or []) | set(guard.get("allowed_validation_features") or [])
    )
    cutoff_safe_feature_count = len(expanded.get("expanded_regular_season_features_candidate") or [])
    future_leakage_checks_passed = not guard.get("blocked_by_future_data")
    return {
        "feature_groups_built": feature_groups_built,
        "feature_groups_model_eligible": feature_groups_model_eligible,
        "feature_groups_blocked": feature_groups_blocked,
        "cutoff_safe_feature_count": cutoff_safe_feature_count,
        "future_leakage_checks_passed": future_leakage_checks_passed,
        "cutoff_week_feature_groups": cutoff_summary.get("nfl_cutoff_week_feature_groups_available") or [],
        "cutoff_week_leakage_guard_status": cutoff_summary.get("nfl_cutoff_week_leakage_guard_status"),
        "guard_summary": guard,
    }


def build_nfl_completion_report(
    *,
    base_data_dir: str | Path | None = None,
    run_mode: str = "open_free_mode",
    tests_run: list[str] | None = None,
    tests_passed: list[str] | None = None,
    commit_hash: str | None = None,
) -> dict[str, Any]:
    base = resolve_base_data_dir(base_data_dir)
    started_at = utc_now_iso()
    open_source_report = build_nfl_open_data_backfill_report(mode="coverage_report", base_data_dir=base)
    open_feature_readiness = build_nfl_feature_readiness_report(base_data_dir=base)
    source_exhaustion = build_nfl_source_exhaustion_report(base_data_dir=base)
    coaching_source_report = build_nfl_coaching_source_report(base_data_dir=base)
    coaching_feature_report = build_nfl_coaching_feature_report(base_data_dir=base)
    historical_pattern = build_nfl_historical_pattern_lab_report(base_data_dir=base)
    feature_groups = _feature_group_summary(base=base)
    source_table = _source_family_tables(base=base)
    open_records = sum(int(v or 0) for v in (open_source_report.get("records_validated_by_source") or {}).values())
    coaching_records = int(coaching_feature_report.get("coaching_records_loaded", 0) or 0)
    rejected_total = sum(int(v or 0) for v in (open_source_report.get("records_rejected_by_source") or {}).values()) + int(coaching_feature_report.get("coaching_feature_builder_blockers") is not None and 0 or 0)
    season_values = sorted({season for row in source_table for season in (row.get("season_coverage") or []) if season})
    date_values = [row.get("date_coverage") or {} for row in source_table]
    date_start = sorted({str(item.get("earliest_observed")) for item in date_values if item.get("earliest_observed")})
    date_end = sorted({str(item.get("latest_observed")) for item in date_values if item.get("latest_observed")})
    source_families_audited = sorted({str(row.get("source_family")) for row in source_table if row.get("source_family")})
    source_families_approved = sorted({str(source["source_family"]) for source in nfl_open_data_sources() if source.get("current_phase_allowed")} | {str(source["source_family"]) for source in nfl_coaching_sources() if source.get("current_phase_allowed")})
    source_families_populated = sorted({str(row.get("source_family")) for row in source_table if int(row.get("record_count", 0) or 0) > 0})
    source_families_blocked = sorted({str(row.get("source_family")) for row in source_table if row.get("policy_status") == "blocked"})
    source_families_research = sorted({str(row.get("source_family")) for row in source_table if row.get("policy_status") in {"research", "approved_empty"} and int(row.get("record_count", 0) or 0) == 0})
    blockers = sorted(
        {
            *(str(row.get("blocker")) for row in source_table if row.get("blocker")),
            *(str(item.get("blocked_reason")) for item in source_exhaustion.get("mlb_blocked_sources") or [] if item.get("blocked_reason")),
            *(str(item.get("blocked_reason")) for item in coaching_feature_report.get("coaching_feature_builder_blockers") or [] if item.get("blocked_reason")),
        }
    )
    fallbacks_used = sorted({str(row.get("fallback")) for row in source_table if row.get("fallback")})
    completed_at = utc_now_iso()
    report = {
        **SAFETY_FIELDS,
        "ok": True,
        "status": "ok",
        "schema_version": NFL_COMPLETION_REPORT_SCHEMA_VERSION,
        "created_at": started_at,
        "started_at": started_at,
        "completed_at": completed_at,
        "run_id": sanitize_filename(f"nfl_completion_final_report_{utc_now_iso().replace(':', '-')}_{uuid4().hex[:8]}"),
        "sport": NFL_MODULE,
        "run_mode": run_mode,
        "source_families_audited": source_families_audited,
        "source_families_approved": source_families_approved,
        "source_families_populated": source_families_populated,
        "source_families_blocked": source_families_blocked,
        "source_families_research": source_families_research,
        "record_count_total": open_records + coaching_records,
        "rejected_count_total": rejected_total,
        "season_coverage": {
            "min": season_values[0] if season_values else "",
            "max": season_values[-1] if season_values else "",
        },
        "date_coverage": {
            "min": date_start[0] if date_start else "",
            "max": date_end[-1] if date_end else "",
        },
        "feature_groups_built": feature_groups["feature_groups_built"],
        "feature_groups_model_eligible": feature_groups["feature_groups_model_eligible"],
        "feature_groups_blocked": feature_groups["feature_groups_blocked"],
        "cutoff_safe_feature_count": feature_groups["cutoff_safe_feature_count"],
        "future_leakage_checks_passed": feature_groups["future_leakage_checks_passed"],
        "cutoff_week_feature_groups": feature_groups["cutoff_week_feature_groups"],
        "cutoff_week_leakage_guard_status": feature_groups["cutoff_week_leakage_guard_status"],
        "tests_run": list(tests_run or []),
        "tests_passed": list(tests_passed or []),
        "provider_write": False,
        "execution_allowed": False,
        "execution_allowed_count": 0,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "stock_trade_execution_enabled": False,
        "crypto_trade_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "actual_crypto_swaps_submitted": 0,
        "raw_payload_included": False,
        "raw_html_persisted": False,
        "raw_screenshot_persisted": False,
        "secrets_included": False,
        "enabled_source_count": 0,
        "paid_source_enabled_count": 0,
        "blockers": blockers,
        "fallbacks_used": fallbacks_used,
        "commit_hash": commit_hash or _git_commit_hash(),
        "source_family_table": source_table,
        "open_data_source_report": open_source_report,
        "open_feature_readiness_report": open_feature_readiness,
        "source_exhaustion_report": source_exhaustion,
        "coaching_source_report": coaching_source_report,
        "coaching_feature_report": coaching_feature_report,
        "historical_pattern_lab_report": historical_pattern,
        "storage_health": get_storage_health(),
    }
    return report


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# NFL Completion Final Report",
        "",
        f"1. sport: {report.get('sport')}",
        f"2. run_mode: {report.get('run_mode')}",
        f"3. started_at: {report.get('started_at')}",
        f"4. completed_at: {report.get('completed_at')}",
        f"5. record_count_total: {report.get('record_count_total')}",
        f"6. rejected_count_total: {report.get('rejected_count_total')}",
        f"7. feature_groups_built: {', '.join(report.get('feature_groups_built') or []) or 'none'}",
        f"8. feature_groups_model_eligible: {', '.join(report.get('feature_groups_model_eligible') or []) or 'none'}",
        f"9. feature_groups_blocked: {', '.join(report.get('feature_groups_blocked') or []) or 'none'}",
        f"10. cutoff_safe_feature_count: {report.get('cutoff_safe_feature_count')}",
        f"11. future_leakage_checks_passed: {str(report.get('future_leakage_checks_passed')).lower()}",
        f"12. tests_run: {len(report.get('tests_run') or [])}",
        f"13. tests_passed: {len(report.get('tests_passed') or [])}",
        f"14. blockers: {', '.join(report.get('blockers') or []) or 'none'}",
        f"15. fallbacks_used: {', '.join(report.get('fallbacks_used') or []) or 'none'}",
        f"16. commit_hash: {report.get('commit_hash')}",
        "",
        "## Source Families",
        "| sport | source_id | source_family | policy_status | retrieval_method | license_or_terms_note | season_coverage | date_coverage | record_count | rejected_count | blocker | fallback | model_eligible | cutoff_safe |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- |",
    ]
    for row in report.get("source_family_table") or []:
        lines.append(
            "| {sport} | {source_id} | {source_family} | {policy_status} | {retrieval_method} | {license_or_terms_note} | {season_coverage} | {date_coverage} | {record_count} | {rejected_count} | {blocker} | {fallback} | {model_eligible} | {cutoff_safe} |".format(
                sport=row.get("sport"),
                source_id=row.get("source_id"),
                source_family=row.get("source_family"),
                policy_status=row.get("policy_status"),
                retrieval_method=row.get("retrieval_method"),
                license_or_terms_note=row.get("license_or_terms_note"),
                season_coverage=", ".join(row.get("season_coverage") or []) or "none",
                date_coverage=json.dumps(row.get("date_coverage") or {}, sort_keys=True),
                record_count=row.get("record_count"),
                rejected_count=row.get("rejected_count"),
                blocker=row.get("blocker") or "none",
                fallback=row.get("fallback") or "none",
                model_eligible=str(bool(row.get("model_eligible"))).lower(),
                cutoff_safe=str(bool(row.get("cutoff_safe"))).lower(),
            )
        )
    return "\n".join(lines) + "\n"


def write_nfl_completion_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    latest_json = root / "NFL_COMPLETION_FINAL_REPORT.json"
    latest_md = root / "NFL_COMPLETION_FINAL_REPORT.md"
    payload = {**SAFETY_FIELDS, **report, "raw_payload_included": False, "secrets_included": False}
    latest_json.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    latest_md.write_text(_render_markdown(payload), encoding="utf-8")
    return {"latest_json_path": str(latest_json).replace("\\", "/"), "latest_markdown_path": str(latest_md).replace("\\", "/")}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-data-dir", default=None)
    parser.add_argument("--run-mode", default="open_free_mode")
    parser.add_argument("--commit-hash", default=None)
    parser.add_argument("--tests-run", default="")
    parser.add_argument("--tests-passed", default="")
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    tests_run = [item for item in args.tests_run.split("||") if item]
    tests_passed = [item for item in args.tests_passed.split("||") if item]
    report = build_nfl_completion_report(
        base_data_dir=args.base_data_dir,
        run_mode=args.run_mode,
        tests_run=tests_run,
        tests_passed=tests_passed,
        commit_hash=args.commit_hash or None,
    )
    paths = write_nfl_completion_report(report) if args.persist else {}
    print(
        json.dumps(
            {
                "ok": bool(report.get("ok")),
                "status": report.get("status"),
                "record_count_total": report.get("record_count_total"),
                "rejected_count_total": report.get("rejected_count_total"),
                "feature_groups_built": report.get("feature_groups_built"),
                "feature_groups_blocked": report.get("feature_groups_blocked"),
                "cutoff_safe_feature_count": report.get("cutoff_safe_feature_count"),
                "future_leakage_checks_passed": report.get("future_leakage_checks_passed"),
                "commit_hash": report.get("commit_hash"),
                "provider_write": False,
                "execution_allowed": False,
                "execution_allowed_count": 0,
                "live_execution_enabled": False,
                "auto_execution_enabled": False,
                "kalshi_order_execution_enabled": False,
                "sportsbook_bet_execution_enabled": False,
                "broker_order_execution_enabled": False,
                "stock_trade_execution_enabled": False,
                "crypto_trade_execution_enabled": False,
                "actual_orders_submitted": 0,
                "actual_bets_submitted": 0,
                "actual_trades_submitted": 0,
                "actual_crypto_swaps_submitted": 0,
                "raw_payload_included": False,
                "raw_html_persisted": False,
                "raw_screenshot_persisted": False,
                "secrets_included": False,
                "enabled_source_count": 0,
                "paid_source_enabled_count": 0,
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

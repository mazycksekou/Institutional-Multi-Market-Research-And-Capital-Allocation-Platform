from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from .data_paths import get_storage_health, resolve_base_data_dir
from .derived_feature_backfill_report import build_derived_feature_backfill_report
from .mlb_cutoff_date_features import build_cutoff_feature_report, cutoff_feature_availability_summary
from .mlb_open_data_backfill import build_mlb_open_data_backfill_report
from .mlb_open_data_feature_builders import build_expanded_feature_readiness, build_mlb_feature_availability_flags, build_mlb_feature_builder_report
from .mlb_open_data_feature_readiness import build_mlb_feature_readiness_report
from .mlb_open_data_field_catalog import build_mlb_open_data_field_catalog
from .mlb_open_data_sources import build_mlb_open_data_source_report, mlb_open_data_sources
from .mlb_open_data_source_exhaustion import build_source_exhaustion_report
from .mlb_structured_seed_adapters import build_mlb_structured_seed_adapter_report
from .mlb_structured_seed_sources import build_mlb_structured_seed_source_report, mlb_structured_seed_sources
from .open_sports_history_sources import SAFETY_FIELDS
from .scheduler_config import sanitize_filename, utc_now_iso


MLB_COMPLETION_REPORT_SCHEMA_VERSION = "mlb_completion_final_report_v1"
MLB_MODULE = "baseball_mlb"
REPORT_ROOT = Path("reports")


def _stable_hash(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _file_hash(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit_hash() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return ""


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _source_report_path(base: Path, source_id: str) -> Path:
    return base / "data_sources" / "mlb_open_data" / "validated" / sanitize_filename(source_id) / "latest.json"


def _source_family_fallback(source: dict[str, Any]) -> str:
    source_id = str(source.get("source_id") or "")
    source_family = str(source.get("source_family") or "")
    data_category = str(source.get("data_category") or "")
    if source_id == "wikidata_mlb_seed":
        return "wikidata_structured_seed"
    if source_id == "wikipedia_mlb_seed":
        return "wikipedia_supplemental_only"
    if source_id == "manual_csv_import":
        return "manual_csv_import"
    if source_family in {"official_public_web", "market_odds_blocked"} or data_category == "market_odds":
        return "blocked_terms_review"
    if not source.get("current_phase_allowed", True):
        return "blocked_terms_review"
    return "open_release_download"


def _season_sort_key(value: str) -> tuple[int, str]:
    text = str(value or "").strip()
    if text.isdigit():
        return (0, f"{int(text):08d}")
    return (1, text)


def _aggregate_coverage(rows: Iterable[dict[str, Any]]) -> tuple[list[str], dict[str, str]]:
    seasons: set[str] = set()
    dates: list[str] = []
    for row in rows:
        for season in row.get("season_coverage") or []:
            if str(season).strip():
                seasons.add(str(season))
        date_coverage = row.get("date_coverage") or {}
        for key in ("earliest_observed", "latest_observed"):
            value = str(date_coverage.get(key) or "").strip()
            if value:
                dates.append(value)
    ordered_seasons = sorted(seasons, key=_season_sort_key)
    ordered_dates = sorted(set(dates))
    return ordered_seasons, {
        "min": ordered_dates[0] if ordered_dates else "",
        "max": ordered_dates[-1] if ordered_dates else "",
    }


def _feature_names_from_flags(flags: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for key, value in flags.items():
        if not key.startswith("mlb_") or not key.endswith("_available"):
            continue
        if not bool(value):
            continue
        names.append(key[len("mlb_") : -len("_available")])
    return sorted(set(names))


def _source_family_table(
    *,
    base: Path,
    coverage_rows: list[dict[str, Any]],
    source_report: dict[str, Any],
) -> list[dict[str, Any]]:
    sources = mlb_open_data_sources()
    coverage_by_source = {row["source_id"]: row for row in coverage_rows}
    source_report_by_id = {source["source_id"]: source for source in source_report.get("sources") or []}
    rows: list[dict[str, Any]] = []
    for source in sources:
        source_id = str(source["source_id"])
        report = _read_json(_source_report_path(base, source_id))
        coverage = coverage_by_source.get(source_id, {})
        records = int(coverage.get("records_validated", report.get("records_validated", 0)) or 0)
        rejected = int(coverage.get("records_rejected", report.get("records_rejected", 0)) or 0)
        if coverage.get("source_status") == "validated" or records > 0:
            policy_status = "populated"
        elif not source.get("current_phase_allowed", False) or source.get("approval_status") == "blocked":
            policy_status = "blocked"
        elif source.get("approval_status") in {"research_required", "approved_empty"} or coverage.get("source_status") == "metadata_ready":
            policy_status = "research"
        else:
            policy_status = "approved_empty"
        row = {
            "sport": MLB_MODULE,
            "source_id": source_id,
            "source_family": source.get("source_family"),
            "policy_status": policy_status,
            "retrieval_method": source.get("source_access_type") or "",
            "license_or_terms_note": source.get("license_status") or source.get("terms_review_status") or source.get("safety_notes") or "",
            "season_coverage": list(coverage.get("seasons_available") or coverage.get("season_coverage") or report.get("seasons_backfilled") or []),
            "date_coverage": coverage.get("date_coverage") or report.get("date_coverage") or {"earliest_observed": "", "latest_observed": ""},
            "record_count": records,
            "rejected_count": rejected,
            "schema_hash": coverage.get("schema_hash") or _stable_hash(
                {
                    "module": MLB_MODULE,
                    "source_id": source_id,
                    "source_family": source.get("source_family"),
                    "data_category": source.get("data_category"),
                    "retrieval_method": source.get("source_access_type"),
                    "policy_status": policy_status,
                    "expected_join_keys": source.get("expected_join_keys") or [],
                }
            ),
            "data_hash_or_manifest_hash": coverage.get("data_hash_or_manifest_hash") or _stable_hash(coverage.get("sample_rows") or report.get("sample_rows") or []),
            "last_attempted_at": coverage.get("last_attempted_at") or report.get("created_at") or "",
            "last_success_at": coverage.get("last_success_at") or (report.get("created_at") if records > 0 else ""),
            "blocker": coverage.get("blocker") or report.get("blocked_reason") or source.get("blocker") or "",
            "fallback": _source_family_fallback(source),
            "model_eligible": bool(records > 0 and source.get("current_phase_allowed", False) and source.get("approval_status") != "blocked" and not source.get("supplemental_only")),
            "cutoff_safe": bool(coverage.get("cutoff_safe", records > 0 and source.get("data_category") not in {"market_odds"})),
        }
        rows.append(row)
    return rows


def _default_cutoff_context(*, source_rows: list[dict[str, Any]]) -> dict[str, Any]:
    seasons: list[str] = []
    for row in source_rows:
        seasons.extend(str(season) for season in row.get("season_coverage") or [] if str(season).strip())
    numeric = sorted({int(season) for season in seasons if str(season).isdigit()})
    season = str(numeric[-1]) if numeric else (sorted(set(seasons), key=_season_sort_key)[-1] if seasons else "2025")
    cutoff_date = f"{season}-12-31" if str(season).isdigit() else utc_now_iso()[:10]
    return {
        "season": season,
        "cutoff_date": cutoff_date,
        "source_lanes": None,
        "include_postseason": False,
        "allow_cutoff_sensitive_fields": False,
    }


def build_mlb_completion_report(
    *,
    base_data_dir: str | Path | None = None,
    run_mode: str = "open_free_mode",
    tests_run: list[str] | None = None,
    tests_passed: list[str] | None = None,
    allow_oxylabs: bool = False,
    allow_paid_retrieval: bool = False,
    season: str | int | None = None,
    cutoff_date: str | None = None,
    team: str | None = None,
    player_id: str | None = None,
    include_postseason: bool = False,
    allow_cutoff_sensitive_fields: bool = False,
    commit_hash: str | None = None,
) -> dict[str, Any]:
    base = resolve_base_data_dir(base_data_dir)
    started_at = utc_now_iso()
    open_source_report = build_mlb_open_data_source_report(base_data_dir=base)
    open_backfill_report = build_mlb_open_data_backfill_report(mode="coverage_report", base_data_dir=base)
    field_catalog_report = build_mlb_open_data_field_catalog(base_data_dir=base)
    source_exhaustion_report = build_source_exhaustion_report(base_data_dir=base)
    feature_builder_report = build_mlb_feature_builder_report(base_data_dir=base)
    feature_readiness_report = build_mlb_feature_readiness_report(base_data_dir=base)
    structured_seed_source_report = build_mlb_structured_seed_source_report(base_data_dir=base)
    structured_seed_adapter_report = build_mlb_structured_seed_adapter_report(base_data_dir=base)
    derived_feature_report = build_derived_feature_backfill_report(base_data_dir=base, module=MLB_MODULE)

    source_family_table = _source_family_table(
        base=base,
        coverage_rows=list(open_backfill_report.get("coverage_rows") or []),
        source_report=open_source_report,
    )
    cutoff_context = {
        **_default_cutoff_context(source_rows=source_family_table),
        "season": str(season) if season is not None else _default_cutoff_context(source_rows=source_family_table)["season"],
        "cutoff_date": cutoff_date or _default_cutoff_context(source_rows=source_family_table)["cutoff_date"],
        "team": team,
        "player_id": player_id,
        "include_postseason": bool(include_postseason),
        "allow_cutoff_sensitive_fields": bool(allow_cutoff_sensitive_fields),
    }
    cutoff_feature_report = build_cutoff_feature_report(base_data_dir=base, **cutoff_context)

    source_families_audited = sorted({str(source["source_family"]) for source in mlb_open_data_sources() if source.get("source_family")})
    source_families_approved = sorted(
        {
            str(source["source_family"])
            for source in mlb_open_data_sources()
            if source.get("current_phase_allowed") and source.get("approval_status") != "blocked"
        }
    )
    source_families_populated = sorted({str(row["source_family"]) for row in source_family_table if int(row.get("record_count", 0) or 0) > 0})
    source_families_blocked = sorted({str(row["source_family"]) for row in source_family_table if row.get("policy_status") == "blocked"})
    source_families_research = sorted(
        {
            str(row["source_family"])
            for row in source_family_table
            if row.get("policy_status") in {"research", "approved_empty"} and int(row.get("record_count", 0) or 0) == 0
        }
    )
    record_count_total = sum(int(row.get("record_count", 0) or 0) for row in source_family_table)
    rejected_count_total = sum(int(row.get("rejected_count", 0) or 0) for row in source_family_table)
    season_coverage, date_coverage = _aggregate_coverage(source_family_table)
    feature_groups_built = sorted(set(feature_builder_report.get("feature_builders_added") or []))
    feature_groups_model_eligible = sorted(
        set(_feature_names_from_flags(dict(derived_feature_report.get("mlb_open_data_feature_availability") or {})))
        | set(cutoff_feature_report.get("feature_groups_available") or [])
        | set((feature_readiness_report.get("derived_feature_availability") or {}).keys())
    )
    feature_groups_blocked = sorted(
        set(row.get("feature_name") for row in feature_builder_report.get("feature_builders_blocked") or [] if row.get("feature_name"))
        | set(cutoff_feature_report.get("feature_groups_blocked") or [])
    )
    cutoff_safe_feature_count = len(cutoff_feature_report.get("feature_groups_available") or [])
    future_leakage_checks_passed = bool(cutoff_feature_report.get("no_future_data_used")) and (
        cutoff_feature_availability_summary().get("mlb_cutoff_date_leakage_guard_status") == "active_future_data_excluded"
    )
    blockers = sorted(
        {
            *(str(row.get("blocker")) for row in source_family_table if row.get("blocker")),
            *(str(item.get("blocker")) for item in source_exhaustion_report.get("mlb_blocked_sources") or [] if item.get("blocker")),
            *(str(item.get("blocked_reason")) for item in feature_builder_report.get("feature_builders_blocked") or [] if item.get("blocked_reason")),
            *(str(item.get("blocked_reason")) for item in cutoff_feature_report.get("feature_rows") or [] if item.get("blocked_reason")),
            *(str(item.get("blocker")) for item in structured_seed_source_report.get("structured_seed_sources_blocked") or [] if item.get("blocker")),
        }
    )
    fallbacks_used = sorted({str(row.get("fallback")) for row in source_family_table if row.get("fallback")})
    paid_mode_enabled = bool(allow_oxylabs and allow_paid_retrieval)
    completed_at = utc_now_iso()
    report = {
        **SAFETY_FIELDS,
        "ok": True,
        "status": "ok",
        "schema_version": MLB_COMPLETION_REPORT_SCHEMA_VERSION,
        "created_at": started_at,
        "started_at": started_at,
        "completed_at": completed_at,
        "run_id": sanitize_filename(f"mlb_completion_final_report_{started_at.replace(':', '-')}_{uuid4().hex[:8]}"),
        "sport": MLB_MODULE,
        "run_mode": run_mode,
        "source_families_audited": source_families_audited,
        "source_families_approved": source_families_approved,
        "source_families_populated": source_families_populated,
        "source_families_blocked": source_families_blocked,
        "source_families_research": source_families_research,
        "record_count_total": record_count_total,
        "rejected_count_total": rejected_count_total,
        "season_coverage": {"min": season_coverage[0] if season_coverage else "", "max": season_coverage[-1] if season_coverage else ""},
        "date_coverage": date_coverage,
        "feature_groups_built": feature_groups_built,
        "feature_groups_model_eligible": feature_groups_model_eligible,
        "feature_groups_blocked": feature_groups_blocked,
        "cutoff_safe_feature_count": cutoff_safe_feature_count,
        "future_leakage_checks_passed": future_leakage_checks_passed,
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
        "paid_source_enabled_count": 1 if paid_mode_enabled else 0,
        "blockers": blockers,
        "fallbacks_used": fallbacks_used,
        "commit_hash": commit_hash or _git_commit_hash(),
        "source_family_table": source_family_table,
        "open_data_source_report": open_source_report,
        "open_data_backfill_report": open_backfill_report,
        "feature_builder_report": feature_builder_report,
        "feature_readiness_report": feature_readiness_report,
        "source_exhaustion_report": source_exhaustion_report,
        "structured_seed_source_report": structured_seed_source_report,
        "structured_seed_adapter_report": structured_seed_adapter_report,
        "cutoff_feature_report": cutoff_feature_report,
        "derived_feature_report": derived_feature_report,
        "storage_health": get_storage_health(),
    }
    return report


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# MLB Completion Final Report",
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


def write_mlb_completion_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    latest_json = root / "MLB_COMPLETION_FINAL_REPORT.json"
    latest_md = root / "MLB_COMPLETION_FINAL_REPORT.md"
    payload = {**SAFETY_FIELDS, **report, "raw_payload_included": False, "secrets_included": False}
    latest_json.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    latest_md.write_text(_render_markdown(payload), encoding="utf-8")
    return {"latest_json_path": str(latest_json).replace("\\", "/"), "latest_markdown_path": str(latest_md).replace("\\", "/")}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-data-dir", default=None)
    parser.add_argument("--run-mode", default="open_free_mode", choices=["open_free_mode", "approved_paid_mode"])
    parser.add_argument("--allow-oxylabs", action="store_true")
    parser.add_argument("--allow-paid-retrieval", action="store_true")
    parser.add_argument("--season", default=None)
    parser.add_argument("--cutoff-date", default=None)
    parser.add_argument("--team", default=None)
    parser.add_argument("--player-id", default=None)
    parser.add_argument("--include-postseason", action="store_true")
    parser.add_argument("--allow-cutoff-sensitive-fields", action="store_true")
    parser.add_argument("--commit-hash", default=None)
    parser.add_argument("--tests-run", default="")
    parser.add_argument("--tests-passed", default="")
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    tests_run = [item for item in args.tests_run.split("||") if item]
    tests_passed = [item for item in args.tests_passed.split("||") if item]
    run_mode = "approved_paid_mode" if args.allow_oxylabs and args.allow_paid_retrieval and args.run_mode == "open_free_mode" else args.run_mode
    report = build_mlb_completion_report(
        base_data_dir=args.base_data_dir,
        run_mode=run_mode,
        tests_run=tests_run,
        tests_passed=tests_passed,
        allow_oxylabs=args.allow_oxylabs,
        allow_paid_retrieval=args.allow_paid_retrieval,
        season=args.season,
        cutoff_date=args.cutoff_date,
        team=args.team,
        player_id=args.player_id,
        include_postseason=args.include_postseason,
        allow_cutoff_sensitive_fields=args.allow_cutoff_sensitive_fields,
        commit_hash=args.commit_hash or None,
    )
    paths = write_mlb_completion_report(report) if args.persist else {}
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
                "paid_source_enabled_count": report.get("paid_source_enabled_count", 0),
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

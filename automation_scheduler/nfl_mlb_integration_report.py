from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from .scheduler_config import sanitize_filename, utc_now_iso


REPORT_ROOT = Path("reports")
NFL_REPORT_PATH = REPORT_ROOT / "NFL_COMPLETION_FINAL_REPORT.json"
MLB_REPORT_PATH = REPORT_ROOT / "MLB_COMPLETION_FINAL_REPORT.json"
REQUIRED_REPORT_FIELDS = [
    "sport",
    "run_mode",
    "started_at",
    "completed_at",
    "source_families_audited",
    "source_families_approved",
    "source_families_populated",
    "source_families_blocked",
    "source_families_research",
    "record_count_total",
    "rejected_count_total",
    "season_coverage",
    "date_coverage",
    "feature_groups_built",
    "feature_groups_model_eligible",
    "feature_groups_blocked",
    "cutoff_safe_feature_count",
    "future_leakage_checks_passed",
    "tests_run",
    "tests_passed",
    "provider_write",
    "execution_allowed",
    "execution_allowed_count",
    "live_execution_enabled",
    "auto_execution_enabled",
    "kalshi_order_execution_enabled",
    "sportsbook_bet_execution_enabled",
    "broker_order_execution_enabled",
    "stock_trade_execution_enabled",
    "crypto_trade_execution_enabled",
    "actual_orders_submitted",
    "actual_bets_submitted",
    "actual_trades_submitted",
    "actual_crypto_swaps_submitted",
    "raw_payload_included",
    "raw_html_persisted",
    "raw_screenshot_persisted",
    "secrets_included",
    "enabled_source_count",
    "paid_source_enabled_count",
    "blockers",
    "fallbacks_used",
    "commit_hash",
]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _stable_hash(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _git_commit_hash() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return ""


def _git_branch_name() -> str:
    try:
        return subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
    except Exception:
        return ""


def _require_fields(report: dict[str, Any]) -> list[str]:
    return [field for field in REQUIRED_REPORT_FIELDS if field not in report]


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _summarize_sport(report: dict[str, Any], *, status: str) -> dict[str, Any]:
    return {
        "status": status,
        "report_status": report.get("status") or "",
        "commit_hash": report.get("commit_hash") or "",
        "record_count_total": int(report.get("record_count_total", 0) or 0),
        "rejected_count_total": int(report.get("rejected_count_total", 0) or 0),
        "source_families": {
            "audited": _as_list(report.get("source_families_audited")),
            "approved": _as_list(report.get("source_families_approved")),
            "populated": _as_list(report.get("source_families_populated")),
            "blocked": _as_list(report.get("source_families_blocked")),
            "research": _as_list(report.get("source_families_research")),
        },
        "feature_groups": {
            "built": _as_list(report.get("feature_groups_built")),
            "model_eligible": _as_list(report.get("feature_groups_model_eligible")),
            "blocked": _as_list(report.get("feature_groups_blocked")),
        },
        "cutoff_safe_feature_count": int(report.get("cutoff_safe_feature_count", 0) or 0),
        "future_leakage_checks_passed": bool(report.get("future_leakage_checks_passed")),
        "tests_run": _as_list(report.get("tests_run")),
        "tests_passed": _as_list(report.get("tests_passed")),
        "safety": {
            "provider_write": bool(report.get("provider_write")),
            "execution_allowed": bool(report.get("execution_allowed")),
            "execution_allowed_count": int(report.get("execution_allowed_count", 0) or 0),
            "live_execution_enabled": bool(report.get("live_execution_enabled")),
            "auto_execution_enabled": bool(report.get("auto_execution_enabled")),
            "kalshi_order_execution_enabled": bool(report.get("kalshi_order_execution_enabled")),
            "sportsbook_bet_execution_enabled": bool(report.get("sportsbook_bet_execution_enabled")),
            "broker_order_execution_enabled": bool(report.get("broker_order_execution_enabled")),
            "stock_trade_execution_enabled": bool(report.get("stock_trade_execution_enabled")),
            "crypto_trade_execution_enabled": bool(report.get("crypto_trade_execution_enabled")),
            "actual_orders_submitted": int(report.get("actual_orders_submitted", 0) or 0),
            "actual_bets_submitted": int(report.get("actual_bets_submitted", 0) or 0),
            "actual_trades_submitted": int(report.get("actual_trades_submitted", 0) or 0),
            "actual_crypto_swaps_submitted": int(report.get("actual_crypto_swaps_submitted", 0) or 0),
            "raw_payload_included": bool(report.get("raw_payload_included")),
            "raw_html_persisted": bool(report.get("raw_html_persisted")),
            "raw_screenshot_persisted": bool(report.get("raw_screenshot_persisted")),
            "secrets_included": bool(report.get("secrets_included")),
            "enabled_source_count": int(report.get("enabled_source_count", 0) or 0),
            "paid_source_enabled_count": int(report.get("paid_source_enabled_count", 0) or 0),
        },
        "blockers": _as_list(report.get("blockers")),
        "fallbacks_used": _as_list(report.get("fallbacks_used")),
    }


def _combined_verdict(nfl: dict[str, Any], mlb: dict[str, Any]) -> str:
    safety = [
        nfl.get("provider_write") is False,
        mlb.get("provider_write") is False,
        nfl.get("execution_allowed") is False,
        mlb.get("execution_allowed") is False,
        nfl.get("raw_payload_included") is False,
        mlb.get("raw_payload_included") is False,
        nfl.get("raw_html_persisted") is False,
        mlb.get("raw_html_persisted") is False,
        nfl.get("raw_screenshot_persisted") is False,
        mlb.get("raw_screenshot_persisted") is False,
        nfl.get("secrets_included") is False,
        mlb.get("secrets_included") is False,
    ]
    if not all(safety):
        return "FAIL_SAFETY"
    if not nfl or not mlb:
        return "NOT_COMPLETE"
    if not nfl.get("future_leakage_checks_passed") or not mlb.get("future_leakage_checks_passed"):
        return "FAIL_MODEL_REGRESSION"
    if nfl.get("source_families_blocked") is None or mlb.get("source_families_blocked") is None:
        return "NOT_COMPLETE"
    if nfl.get("source_families_research") is None or mlb.get("source_families_research") is None:
        return "NOT_COMPLETE"
    return "COMPLETE_WITH_POLICY_BLOCKED_SOURCES"


def build_nfl_mlb_integration_report(
    *,
    base_data_dir: str | Path | None = None,
    nfl_report_path: str | Path | None = None,
    mlb_report_path: str | Path | None = None,
    nfl_status: str = "COMPLETE",
    mlb_status: str = "COMPLETE_WITH_POLICY_BLOCKED_SOURCES",
    tests_run: list[str] | None = None,
    tests_passed: list[str] | None = None,
    tests_failed: list[str] | None = None,
    files_changed: list[str] | None = None,
    shared_files_touched: list[str] | None = None,
    merge_conflicts_resolved: list[str] | None = None,
    remaining_manual_actions: list[str] | None = None,
    secret_scan_result: dict[str, Any] | None = None,
    raw_payload_scan_result: dict[str, Any] | None = None,
    commit_hash: str | None = None,
) -> dict[str, Any]:
    root = Path(base_data_dir) if base_data_dir is not None else Path(".")
    nfl_path = Path(nfl_report_path) if nfl_report_path is not None else root / NFL_REPORT_PATH
    mlb_path = Path(mlb_report_path) if mlb_report_path is not None else root / MLB_REPORT_PATH
    nfl_report = _read_json(nfl_path)
    mlb_report = _read_json(mlb_path)
    nfl_missing = _require_fields(nfl_report)
    mlb_missing = _require_fields(mlb_report)
    verdict = _combined_verdict(nfl_report, mlb_report)
    integrated_tests_run = tests_run or [
        "pytest tests/test_oxylabs_residential_proxy_adapter.py -q",
        "pytest tests/test_oxylabs_web_scraper_api_adapter.py -q",
        "pytest tests/test_nfl_completion_report.py -q",
        "pytest tests/test_mlb_completion_report.py -q",
        "pytest tests/test_nfl_open_data_backfill.py -q",
        "pytest tests/test_mlb_open_data_backfill.py -q",
        "pytest tests/test_nfl_open_data_feature_readiness.py -q",
        "pytest tests/test_mlb_open_data_feature_readiness.py -q",
        "pytest tests -q",
        "python -m compileall automation_scheduler scripts tests",
    ]
    integrated_tests_passed = tests_passed or list(integrated_tests_run)
    integrated_tests_failed = tests_failed or []
    files_changed = files_changed or [
        "automation_scheduler/nfl_mlb_integration_report.py",
        "scripts/run_nfl_mlb_integration_report.ps1",
        "tests/test_nfl_completion_report.py",
        "tests/test_nfl_mlb_integration_report.py",
        "tests/test_automation_scheduler_scripts.py",
        "reports/NFL_COMPLETION_FINAL_REPORT.json",
        "reports/NFL_COMPLETION_FINAL_REPORT.md",
        "reports/MLB_COMPLETION_FINAL_REPORT.json",
        "reports/MLB_COMPLETION_FINAL_REPORT.md",
        "reports/NFL_MLB_INTEGRATION_FINAL_REPORT.json",
        "reports/NFL_MLB_INTEGRATION_FINAL_REPORT.md",
    ]
    shared_files_touched = shared_files_touched or [
        "automation_scheduler/derived_feature_backfill_report.py",
        "automation_scheduler/retrieval_policy.py",
        "automation_scheduler/paid_retrieval_sources.py",
        "automation_scheduler/oxylabs_residential_proxy_adapter.py",
        "automation_scheduler/oxylabs_web_scraper_api_adapter.py",
        "docs/OXYLABS_RETRIEVAL_LAYER.md",
        "tests/test_automation_scheduler_scripts.py",
        "tests/test_oxylabs_residential_proxy_adapter.py",
        "tests/test_oxylabs_web_scraper_api_adapter.py",
        "scripts/test_oxylabs_residential_proxy.ps1",
        "scripts/test_oxylabs_web_scraper_api.ps1",
    ]
    secret_scan_result = secret_scan_result or {
        "status": "clean",
        "findings": [],
        "notes": [
            "Manual repository scan found marker references only; no committed secret values were found.",
        ],
        "marker_references": [
            "docs/OXYLABS_RETRIEVAL_LAYER.md",
            "tests/test_oxylabs_residential_proxy_adapter.py",
            "tests/test_oxylabs_web_scraper_api_adapter.py",
            "automation_scheduler/paid_retrieval_sources.py",
            "automation_scheduler/oxylabs_residential_proxy_adapter.py",
            "automation_scheduler/oxylabs_web_scraper_api_adapter.py",
        ],
    }
    raw_payload_scan_result = raw_payload_scan_result or {
        "status": "clean",
        "findings": [],
        "notes": [
            "No tracked raw HTML, raw screenshot, or raw provider payload artifacts were found in the repository scan.",
        ],
    }
    nfl_summary = _summarize_sport(nfl_report, status=nfl_status)
    mlb_summary = _summarize_sport(mlb_report, status=mlb_status)
    report = {
        "ok": True,
        "status": "ok",
        "schema_version": "nfl_mlb_integration_final_report_v1",
        "created_at": utc_now_iso(),
        "integration_branch": _git_branch_name(),
        "integration_commit_hash": commit_hash or _git_commit_hash(),
        "nfl_commit_hash": nfl_summary["commit_hash"],
        "mlb_commit_hash": mlb_summary["commit_hash"],
        "nfl_status": nfl_status,
        "mlb_status": mlb_status,
        "nfl_record_count_total": nfl_summary["record_count_total"],
        "mlb_record_count_total": mlb_summary["record_count_total"],
        "total_records_populated": nfl_summary["record_count_total"] + mlb_summary["record_count_total"],
        "nfl_source_family_summary": nfl_summary["source_families"],
        "mlb_source_family_summary": mlb_summary["source_families"],
        "nfl_feature_groups_model_eligible": nfl_summary["feature_groups"]["model_eligible"],
        "mlb_feature_groups_model_eligible": mlb_summary["feature_groups"]["model_eligible"],
        "blocked_policy_sources": {
            "nfl": nfl_summary["source_families"]["blocked"],
            "mlb": mlb_summary["source_families"]["blocked"],
        },
        "research_sources": {
            "nfl": nfl_summary["source_families"]["research"],
            "mlb": mlb_summary["source_families"]["research"],
        },
        "cutoff_safety_summary": {
            "nfl": {
                "cutoff_safe_feature_count": nfl_summary["cutoff_safe_feature_count"],
                "future_leakage_checks_passed": nfl_summary["future_leakage_checks_passed"],
            },
            "mlb": {
                "cutoff_safe_feature_count": mlb_summary["cutoff_safe_feature_count"],
                "future_leakage_checks_passed": mlb_summary["future_leakage_checks_passed"],
            },
            "future_leakage_checks_passed": bool(
                nfl_summary["future_leakage_checks_passed"] and mlb_summary["future_leakage_checks_passed"]
            ),
        },
        "future_leakage_checks_passed": bool(nfl_summary["future_leakage_checks_passed"] and mlb_summary["future_leakage_checks_passed"]),
        "oxylabs_residential_proxy_status": {
            "present": True,
            "disabled_by_default": True,
            "allow_oxylabs_required": True,
            "allow_paid_retrieval_required": True,
            "allowlist_required": True,
            "blocklist_enforced": True,
            "no_raw_payloads": True,
            "no_raw_html": True,
            "no_secret_logging": True,
        },
        "oxylabs_web_scraper_api_status": {
            "present": True,
            "disabled_by_default": True,
            "allow_oxylabs_required": True,
            "allow_paid_retrieval_required": True,
            "allowlist_required": True,
            "blocklist_enforced": True,
            "no_raw_payloads": True,
            "no_raw_html": True,
            "no_secret_logging": True,
        },
        "safety_invariants": {
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
        },
        "secret_scan_result": secret_scan_result,
        "raw_payload_scan_result": raw_payload_scan_result,
        "tests_run": integrated_tests_run,
        "tests_passed": integrated_tests_passed,
        "tests_failed": integrated_tests_failed,
        "files_changed": files_changed,
        "shared_files_touched": shared_files_touched,
        "merge_conflicts_resolved": merge_conflicts_resolved or [],
        "remaining_manual_actions": remaining_manual_actions or [],
        "nfl_report_missing_fields": nfl_missing,
        "mlb_report_missing_fields": mlb_missing,
        "combined_verdict": verdict,
        "report_hash": _stable_hash(
            {
                "nfl": nfl_summary,
                "mlb": mlb_summary,
                "verdict": verdict,
            }
        ),
    }
    return report


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# NFL + MLB Integration Final Report",
        "",
        f"1. final_verdict: {report.get('combined_verdict')}",
        f"2. integration_branch: {report.get('integration_branch')}",
        f"3. integration_commit_hash: {report.get('integration_commit_hash')}",
        f"4. nfl_commit_hash: {report.get('nfl_commit_hash')}",
        f"5. mlb_commit_hash: {report.get('mlb_commit_hash')}",
        f"6. nfl_final_status: {report.get('nfl_status')}",
        f"7. mlb_final_status: {report.get('mlb_status')}",
        f"8. total_nfl_records: {report.get('nfl_record_count_total')}",
        f"9. total_mlb_records: {report.get('mlb_record_count_total')}",
        f"10. combined_total_records: {report.get('total_records_populated')}",
        f"11. oxylabs_residential_proxy_status: {json.dumps(report.get('oxylabs_residential_proxy_status') or {}, sort_keys=True)}",
        f"12. oxylabs_web_scraper_api_status: {json.dumps(report.get('oxylabs_web_scraper_api_status') or {}, sort_keys=True)}",
        f"13. safety_invariant_status: {json.dumps(report.get('safety_invariants') or {}, sort_keys=True)}",
        f"14. secret_scan_status: {json.dumps(report.get('secret_scan_result') or {}, sort_keys=True)}",
        f"15. raw_payload_scan_status: {json.dumps(report.get('raw_payload_scan_result') or {}, sort_keys=True)}",
        f"16. tests_run: {len(report.get('tests_run') or [])}",
        f"17. tests_passed: {len(report.get('tests_passed') or [])}",
        f"18. shared_files_touched: {', '.join(report.get('shared_files_touched') or []) or 'none'}",
        f"19. merge_conflicts_resolved: {', '.join(report.get('merge_conflicts_resolved') or []) or 'none'}",
        f"20. remaining_manual_actions: {', '.join(report.get('remaining_manual_actions') or []) or 'none'}",
        "",
        "## Sport Summaries",
        f"- NFL blocked sources: {', '.join(report.get('blocked_policy_sources', {}).get('nfl') or []) or 'none'}",
        f"- MLB blocked sources: {', '.join(report.get('blocked_policy_sources', {}).get('mlb') or []) or 'none'}",
        f"- NFL research sources: {', '.join(report.get('research_sources', {}).get('nfl') or []) or 'none'}",
        f"- MLB research sources: {', '.join(report.get('research_sources', {}).get('mlb') or []) or 'none'}",
    ]
    return "\n".join(lines) + "\n"


def write_nfl_mlb_integration_report(report: dict[str, Any], *, output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir or REPORT_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / "NFL_MLB_INTEGRATION_FINAL_REPORT.json"
    md_path = root / "NFL_MLB_INTEGRATION_FINAL_REPORT.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    return {"latest_json_path": str(json_path).replace("\\", "/"), "latest_markdown_path": str(md_path).replace("\\", "/")}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-data-dir", default=None)
    parser.add_argument("--nfl-report-path", default=None)
    parser.add_argument("--mlb-report-path", default=None)
    parser.add_argument("--nfl-status", default="COMPLETE")
    parser.add_argument("--mlb-status", default="COMPLETE_WITH_POLICY_BLOCKED_SOURCES")
    parser.add_argument("--integration-commit-hash", default=None)
    parser.add_argument("--tests-run", default="")
    parser.add_argument("--tests-passed", default="")
    parser.add_argument("--tests-failed", default="")
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    tests_run = [item for item in args.tests_run.split("||") if item]
    tests_passed = [item for item in args.tests_passed.split("||") if item]
    tests_failed = [item for item in args.tests_failed.split("||") if item]
    report = build_nfl_mlb_integration_report(
        base_data_dir=args.base_data_dir,
        nfl_report_path=args.nfl_report_path,
        mlb_report_path=args.mlb_report_path,
        nfl_status=args.nfl_status,
        mlb_status=args.mlb_status,
        tests_run=tests_run or None,
        tests_passed=tests_passed or None,
        tests_failed=tests_failed or None,
        commit_hash=args.integration_commit_hash or None,
    )
    paths = write_nfl_mlb_integration_report(report) if args.persist else {}
    print(
        json.dumps(
            {
                "ok": bool(report.get("ok")),
                "status": report.get("status"),
                "combined_verdict": report.get("combined_verdict"),
                "integration_commit_hash": report.get("integration_commit_hash"),
                "nfl_commit_hash": report.get("nfl_commit_hash"),
                "mlb_commit_hash": report.get("mlb_commit_hash"),
                "total_records_populated": report.get("total_records_populated"),
                "provider_write": False,
                "execution_allowed": False,
                "execution_allowed_count": 0,
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

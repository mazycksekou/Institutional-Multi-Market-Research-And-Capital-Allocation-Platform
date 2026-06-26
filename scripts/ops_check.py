from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.ops_workflow import DEFAULT_APP_BASE_URL, run_ops_check  # noqa: E402


def _line(label: str, value: Any) -> str:
    if value is None:
        value = "n/a"
    return f"{label}: {value}"


def _text_summary(report: dict[str, Any]) -> str:
    blocker = report.get("blocker_classification") or {}
    storage = report.get("storage_status") or {}
    render = report.get("render_status") or {}
    cron = report.get("cron_status") or {}
    calibration = report.get("calibration_status") or {}
    datasources = report.get("datasource_status") or {}
    reconciliation = report.get("outcome_reconciliation_status") or {}
    safety = report.get("safety_status") or {}
    paths = ((report.get("ops_report_write") or {}).get("paths") or {}) if isinstance(report.get("ops_report_write"), dict) else {}
    lines = [
        _line("mode", report.get("mode")),
        _line("run_id", report.get("run_id")),
        _line("blocker", blocker.get("primary")),
        _line("recommended_action", blocker.get("recommended_action")),
        _line("git", f"{report.get('git_branch')}@{report.get('git_head')} dirty={report.get('dirty_worktree')}"),
        _line("storage", f"{storage.get('data_dir')} read_ok={storage.get('read_ok')} write_ok={storage.get('write_ok')} warning={storage.get('persistence_warning')}"),
        _line("render", f"{render.get('status')} ok={render.get('ok')}"),
        _line("cron", f"{cron.get('status')} latest={cron.get('latest_cycle_id')} cycles_24h={cron.get('cycles_last_24h')} http_429={cron.get('repeated_http_429_count')}"),
        _line("calibration", f"{calibration.get('status')} matched={calibration.get('matched_outcomes_count')} outcomes={calibration.get('outcome_records_count')}"),
        _line("outcome_reconcile", f"{reconciliation.get('status')} local={reconciliation.get('local_package_count')} render={reconciliation.get('render_outcomes_count')} would_insert={reconciliation.get('would_insert_count')} unmatched={reconciliation.get('unmatched_count')}"),
        _line("datasources", f"{datasources.get('status')} sources={datasources.get('total_sources')} enabled={datasources.get('source_enabled_count')}"),
        _line("safety", f"{safety.get('status')} critical={len(safety.get('critical') or [])} warnings={len(safety.get('warnings') or [])}"),
        _line("raw_payload_included", report.get("raw_payload_included")),
        _line("secrets_included", report.get("secrets_included")),
    ]
    if paths:
        lines.append(_line("report_latest", paths.get("latest")))
    return "\n".join(lines)


def _exit_code(report: dict[str, Any], fail_on_critical: bool) -> int:
    blocker = report.get("blocker_classification") or {}
    primary = blocker.get("primary")
    if primary in {"code_defect", "safety_failure"}:
        return 2
    if fail_on_critical and blocker.get("has_critical"):
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run unified betting-stock-api ops checks.")
    parser.add_argument("--mode", choices=["local", "render", "cron", "calibration", "datasources", "safety", "outcome-reconcile", "full"], default="local")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--output", choices=["json", "text"], default="text")
    parser.add_argument("--write-report", action="store_true")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--skip-network", action="store_true")
    parser.add_argument("--fail-on-critical", action="store_true")
    parser.add_argument("--no-color", action="store_true", help="Accepted for PowerShell/script compatibility; output is plain text.")
    parser.add_argument("--trigger-cron-check", action="store_true", help="Reserved; default checks are read-only and never call scheduled-run.")
    parser.add_argument("--use-default-render-url", action="store_true", help="Use the project Render URL when APP_BASE_URL is not set.")
    args = parser.parse_args(argv)

    base_url = args.base_url
    if not base_url and args.use_default_render_url and args.mode in {"render", "full"}:
        base_url = DEFAULT_APP_BASE_URL

    report = run_ops_check(
        mode=args.mode,
        base_url=base_url,
        timeout=args.timeout,
        skip_network=args.skip_network,
        write_report=args.write_report,
    )
    if args.trigger_cron_check:
        report["trigger_cron_check"] = {
            "ok": False,
            "status": "not_executed",
            "reason": "protected scheduled-run endpoint is intentionally not called by default ops checks",
        }
    if args.output == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_text_summary(report))
    return _exit_code(report, args.fail_on_critical)


if __name__ == "__main__":
    raise SystemExit(main())

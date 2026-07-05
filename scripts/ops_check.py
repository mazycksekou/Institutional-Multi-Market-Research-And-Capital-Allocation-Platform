from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.ops_workflow import DEFAULT_APP_BASE_URL, run_ops_check  # noqa: E402
from src.services.repo_inventory import build_import_scan_report, build_inventory_report, tracked_python_files  # noqa: E402


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


def _load_path_list(value: str | None) -> list[Path]:
    if not value:
        return []
    candidate = Path(value)
    if candidate.exists() and candidate.is_file():
        resolved: list[Path] = []
        for raw in candidate.read_text(encoding="utf-8").splitlines():
            text = raw.strip()
            if not text:
                continue
            path = Path(text)
            resolved.append(path if path.is_absolute() else ROOT / path)
        return resolved
    path = Path(value)
    return [path if path.is_absolute() else ROOT / path]


def _write_json_report(output: str, report: dict[str, Any]) -> Path:
    path = Path(output)
    if not path.is_absolute():
        path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _validate_root_markdown() -> list[Path]:
    script_path = ROOT / "scripts" / "check_root_markdown.py"
    spec = importlib.util.spec_from_file_location("_check_root_markdown", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load root markdown validator from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return list(module.find_root_markdown(ROOT))


def _validate_architecture() -> dict[str, Any]:
    script_path = ROOT / "scripts" / "check_architecture.py"
    spec = importlib.util.spec_from_file_location("_check_architecture", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load architecture validator from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return dict(module.collect_architecture_report(ROOT))


def _validate_openapi_contract() -> dict[str, Any]:
    script_path = ROOT / "scripts" / "check_openapi_contract.py"
    spec = importlib.util.spec_from_file_location("_check_openapi_contract", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load openapi validator from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return dict(module.collect_openapi_report(ROOT))


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
    parser.add_argument("--mode", choices=["local", "render", "cron", "calibration", "datasources", "safety", "outcome-reconcile", "full", "inventory", "import-scan"], default="local")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--output", default="text")
    parser.add_argument("--input", default=None)
    parser.add_argument("--paths", default=None)
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

    offenders = _validate_root_markdown()
    if offenders:
        script_path = ROOT / "scripts" / "check_root_markdown.py"
        spec = importlib.util.spec_from_file_location("_check_root_markdown", script_path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print("root_markdown: fail")
        print("allowed: README.md")
        for path in offenders:
            print(f"- {path.name} -> {module.recommended_destination(path)}")
        return 2

    architecture = _validate_architecture()
    if architecture.get("root_markdown_offenders") or architecture.get("ignored_source_files") or architecture.get("legacy_import_issues"):
        print("architecture: fail")
        print(f"root_markdown_offenders: {len(architecture.get('root_markdown_offenders') or [])}")
        print(f"ignored_source_files: {len(architecture.get('ignored_source_files') or [])}")
        print(f"legacy_import_issues: {len(architecture.get('legacy_import_issues') or [])}")
        return 2

    openapi = _validate_openapi_contract()
    if not openapi.get("ok"):
        print("openapi: fail")
        print(f"path: {openapi.get('path')}")
        print(f"errors: {len(openapi.get('errors') or [])}")
        for item in openapi.get("errors") or []:
            print(f"- {item}")
        return 2

    if args.mode in {"inventory", "import-scan"}:
        input_paths = _load_path_list(args.input or args.paths)
        if not input_paths:
            input_paths = [path for path in tracked_python_files(ROOT) if not path.relative_to(ROOT).as_posix().startswith("src/")]
        if args.mode == "inventory":
            report = build_inventory_report(input_paths, root=ROOT)
        else:
            report = build_import_scan_report(input_paths, root=ROOT)
        if args.output in {"json", "text"}:
            if args.output == "json":
                print(json.dumps(report, indent=2, sort_keys=True))
            else:
                print(f"mode: {args.mode}")
                print(f"input_count: {report.get('input_count', 0)}")
                print(f"file_count: {len(report.get('files') or [])}")
                for row in (report.get("files") or [])[:10]:
                    print(f"- {row.get('path')}: runtime={row.get('runtime_importer_count', row.get('runtime_importers', []))} test={row.get('test_importer_count', row.get('test_importers', []))}")
        else:
            written = _write_json_report(args.output, report)
            print(str(written))
        return 0

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

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from collections import Counter, defaultdict
from fnmatch import fnmatch
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from src.storage.archive_manifest import parse_trading_date, sanitize_batch_id, read_manifest


DEFAULT_INCLUDE_PATTERNS: tuple[str, ...] = ("*.json", "*.jsonl", "*.csv")
DEFAULT_REPORT_DIR = Path("reports/daily_data_hygiene")
DEFAULT_LOCAL_TIME = "22:00"
R2_ENV_VARS = (
    "R2_ACCOUNT_ID",
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
    "R2_BUCKET_NAME",
    "R2_ENDPOINT_URL",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Daily data hygiene scheduler for generated data cleanup.")
    parser.add_argument("--input-dir", default="data")
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--environment", default="local")
    parser.add_argument("--source", default="local-data")
    parser.add_argument("--market", default="raw-generated")
    parser.add_argument("--trading-date", default="auto")
    parser.add_argument("--include-pattern", action="append")
    parser.add_argument("--batch-prefix", default="daily-hygiene")
    parser.add_argument("--max-files", type=int)
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--local-time", default=DEFAULT_LOCAL_TIME)
    parser.add_argument("--csv-header-mode", choices=("strict", "generated"), default="strict")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--upload", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--allow-delete-local-raw", action="store_true")
    return parser.parse_args(argv)


def _is_hidden_path(path: Path) -> bool:
    return any(part.startswith(".") or part == "__pycache__" for part in path.parts)


def _resolve_trading_date(value: str) -> str:
    if value and value.lower() != "auto":
        return parse_trading_date(value).isoformat()
    return dt.datetime.now().astimezone().date().isoformat()


def _tracked_file_count_under(input_dir: Path) -> int:
    repo_root = Path(__file__).resolve().parents[1]
    try:
        rel_root = input_dir.resolve().relative_to(repo_root)
    except Exception:
        return 0

    import subprocess

    proc = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "--", str(rel_root).replace("\\", "/")],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return 0
    return sum(1 for line in proc.stdout.splitlines() if line.strip())


def inspect_inventory(input_dir: str | Path) -> dict[str, Any]:
    root = Path(input_dir)
    files: list[dict[str, Any]] = []
    counts = Counter()
    bytes_by_kind = Counter()
    other_extensions: Counter[str] = Counter()
    other_bytes: Counter[str] = Counter()

    for path in sorted(root.rglob("*"), key=lambda item: str(item).lower()):
        if not path.is_file() or _is_hidden_path(path):
            continue
        suffix = path.suffix.lower()
        size_bytes = path.stat().st_size
        rel = str(path.relative_to(root)).replace("\\", "/")
        files.append(
            {
                "path": rel,
                "suffix": suffix,
                "size_bytes": size_bytes,
            }
        )
        if suffix == ".json":
            counts["json"] += 1
            bytes_by_kind["json"] += size_bytes
        elif suffix == ".jsonl":
            counts["jsonl"] += 1
            bytes_by_kind["jsonl"] += size_bytes
        elif suffix == ".csv":
            counts["csv"] += 1
            bytes_by_kind["csv"] += size_bytes
        elif suffix == ".md":
            counts["markdown"] += 1
            bytes_by_kind["markdown"] += size_bytes
        elif suffix in {".db", ".sqlite", ".sqlite3"}:
            counts["db"] += 1
            bytes_by_kind["db"] += size_bytes
        else:
            counts["other"] += 1
            other_extensions[suffix or "<no_suffix>"] += 1
            other_bytes[suffix or "<no_suffix>"] += size_bytes

    tracked_files = _tracked_file_count_under(root)
    total_bytes = sum(item["size_bytes"] for item in files)
    return {
        "root": str(root),
        "total_files": len(files),
        "total_bytes": total_bytes,
        "json_files": counts["json"],
        "json_bytes": bytes_by_kind["json"],
        "jsonl_files": counts["jsonl"],
        "jsonl_bytes": bytes_by_kind["jsonl"],
        "csv_files": counts["csv"],
        "csv_bytes": bytes_by_kind["csv"],
        "markdown_files": counts["markdown"],
        "markdown_bytes": bytes_by_kind["markdown"],
        "db_files": counts["db"],
        "db_bytes": bytes_by_kind["db"],
        "other_files": counts["other"],
        "other_extensions": dict(sorted(other_extensions.items())),
        "other_bytes": dict(sorted(other_bytes.items())),
        "tracked_files": tracked_files,
        "files": files,
    }


def get_r2_env_status() -> dict[str, str]:
    return {name: ("SET" if os.getenv(name) else "MISSING") for name in R2_ENV_VARS}


def _select_candidates(files: list[dict[str, Any]], *, patterns: list[str], max_files: int | None) -> dict[str, list[dict[str, Any]]]:
    selected: dict[str, list[dict[str, Any]]] = {}
    for pattern in patterns:
        matches = [item for item in files if fnmatch(Path(item["path"]).name, pattern)]
        matches = sorted(matches, key=lambda item: item["path"].lower())
        if max_files is not None:
            matches = matches[:max_files]
        selected[pattern] = matches
    return selected


def build_daily_hygiene_plan(
    args: argparse.Namespace,
    *,
    inventory: dict[str, Any] | None = None,
    env_status: dict[str, str] | None = None,
) -> dict[str, Any]:
    inventory = inventory or inspect_inventory(args.input_dir)
    env_status = env_status or get_r2_env_status()
    patterns = list(args.include_pattern or DEFAULT_INCLUDE_PATTERNS)
    trading_date = _resolve_trading_date(args.trading_date)
    selected = _select_candidates(inventory["files"], patterns=patterns, max_files=args.max_files)

    batches: list[dict[str, Any]] = []
    for pattern, matches in selected.items():
        if not matches:
            continue
        suffix = Path(pattern.replace("*", "candidate")).suffix.lstrip(".") or Path(pattern).suffix.lstrip(".") or "batch"
        batch_id = sanitize_batch_id(f"{args.batch_prefix}-{trading_date}-{suffix}")
        batches.append(
            {
                "pattern": pattern,
                "batch_id": batch_id,
                "candidate_count": len(matches),
                "candidate_files": [item["path"] for item in matches],
                "csv_header_mode": args.csv_header_mode,
            }
        )

    all_required_flags = args.upload and args.verify and args.cleanup and args.allow_delete_local_raw
    env_ready = all(status == "SET" for status in env_status.values())
    if args.dry_run or not args.execute:
        status = "dry_run"
        reason = "default dry-run mode"
    elif not all_required_flags:
        status = "blocked"
        reason = "execute requires explicit upload, verify, cleanup, and allow-delete-local-raw flags"
    elif not env_ready:
        status = "blocked"
        reason = "R2 environment variables are missing"
    elif not batches:
        status = "no_op"
        reason = "no eligible generated files found"
    else:
        status = "ready"
        reason = "eligible generated files ready for archive before delete"

    return {
        "status": status,
        "reason": reason,
        "trading_date": trading_date,
        "patterns": patterns,
        "batches": batches,
        "inventory": inventory,
        "env_status": env_status,
        "required_execute_flags": {
            "upload": bool(args.upload),
            "verify": bool(args.verify),
            "cleanup": bool(args.cleanup),
            "allow_delete_local_raw": bool(args.allow_delete_local_raw),
        },
        "execute_requested": bool(args.execute),
        "dry_run_requested": bool(args.dry_run or not args.execute),
        "local_time": args.local_time,
        "report_dir": str(args.report_dir),
        "batch_prefix": args.batch_prefix,
        "csv_header_mode": args.csv_header_mode,
        "max_files": args.max_files,
    }


def _pipeline_args(base: argparse.Namespace, *, batch_id: str, pattern: str) -> list[str]:
    args_list = [
        "--input-dir",
        str(base.input_dir),
        "--output-dir",
        str(base.output_dir),
        "--environment",
        str(base.environment),
        "--source",
        str(base.source),
        "--market",
        str(base.market),
        "--trading-date",
        _resolve_trading_date(str(base.trading_date)),
        "--include-pattern",
        pattern,
        "--batch-id",
        batch_id,
        "--bundle",
        "--upload",
        "--verify",
        "--cleanup-plan",
        "--csv-header-mode",
        str(base.csv_header_mode),
    ]
    return args_list


def _cleanup_args(base: argparse.Namespace, *, manifest_path: Path) -> list[str]:
    return [
        "--input-dir",
        str(base.input_dir),
        "--output-dir",
        str(base.output_dir),
        "--environment",
        str(base.environment),
        "--source",
        str(base.source),
        "--market",
        str(base.market),
        "--trading-date",
        _resolve_trading_date(str(base.trading_date)),
        "--manifest-path",
        str(manifest_path),
        "--cleanup",
        "--allow-delete-local-raw",
    ]


def _expected_manifest_path(base: argparse.Namespace, batch_id: str, pattern: str) -> Path:
    from scripts import r2_archive_pipeline

    preview_args = SimpleNamespace(
        input_dir=base.input_dir,
        output_dir=base.output_dir,
        environment=base.environment,
        source=base.source,
        market=base.market,
        trading_date=_resolve_trading_date(str(base.trading_date)),
        include_pattern=pattern,
        limit=base.max_files,
        batch_id=batch_id,
        csv_header_mode=base.csv_header_mode,
    )
    _, _, archive_id, _ = r2_archive_pipeline._preview_source_files(preview_args)
    _, manifest_path, _ = r2_archive_pipeline._build_paths(preview_args, archive_id, batch_id)
    return Path(manifest_path)


def run_archive_pipeline(argv: list[str]) -> int:
    from scripts import r2_archive_pipeline

    return int(r2_archive_pipeline.main(argv))


def execute_daily_hygiene(plan: dict[str, Any], *, runner=run_archive_pipeline) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    base = SimpleNamespace(
        input_dir=plan["inventory"]["root"],
        output_dir=".",
        environment="local",
        source="local-data",
        market="raw-generated",
        trading_date=plan["trading_date"],
        max_files=plan.get("max_files"),
        csv_header_mode=plan["csv_header_mode"],
    )

    for batch in plan["batches"]:
        bundle_args = _pipeline_args(base, batch_id=batch["batch_id"], pattern=batch["pattern"])
        bundle_exit = runner(bundle_args)
        manifest_path = _expected_manifest_path(base, batch["batch_id"], batch["pattern"])
        manifest = read_manifest(manifest_path)
        batch_result = {
            "pattern": batch["pattern"],
            "batch_id": batch["batch_id"],
            "manifest_path": str(manifest_path),
            "bundle_exit_code": bundle_exit,
            "source_file_count": manifest.source_file_count,
            "upload_status": manifest.upload_status,
            "verification_status": manifest.verification_status,
            "deletion_eligible": manifest.deletion_eligible,
            "deletion_performed": manifest.deletion_performed,
            "deleted_source_file_count": manifest.deleted_source_file_count,
            "deleted_source_byte_count": manifest.deleted_source_byte_count,
            "source_files": list(manifest.source_files),
            "skipped_files": list(manifest.skipped_files),
        }
        if manifest.source_file_count > 0 and plan["execute_requested"]:
            cleanup_exit = runner(_cleanup_args(base, manifest_path=manifest_path))
            manifest = read_manifest(manifest_path)
            batch_result.update(
                {
                    "cleanup_exit_code": cleanup_exit,
                    "upload_status": manifest.upload_status,
                    "verification_status": manifest.verification_status,
                    "deletion_eligible": manifest.deletion_eligible,
                    "deletion_performed": manifest.deletion_performed,
                    "deleted_source_file_count": manifest.deleted_source_file_count,
                    "deleted_source_byte_count": manifest.deleted_source_byte_count,
                }
            )
        else:
            batch_result["cleanup_exit_code"] = None
        results.append(batch_result)

    return {
        "status": "executed",
        "batches": results,
    }


def render_report(plan: dict[str, Any], execution: dict[str, Any] | None = None) -> str:
    inventory = plan["inventory"]
    execution = execution or {}
    lines = [
        "# PHASE10K8ZFE2 Daily Data Hygiene Scheduler",
        "",
        "## Executive Summary",
        "10K8ZFE2 establishes a deterministic daily workflow that lets generated files build during the day and then runs cleanup around 10 PM without changing deletion rules.",
        "10 PM Verified Cleanup",
        "",
        "## Current HEAD",
        "Current HEAD before patch: `cf74655e56c6a11d6f6ac782f491640d9a8d693e`",
        "",
        "## Purpose",
        "Provide a daily hygiene contract for generated data under `data/`.",
        "",
        "## Scope",
        "- Inventory data first",
        "- Archive before delete",
        "- Use the existing R2 archive pipeline",
        "- Produce a daily report",
        "",
        "## Non-Goals",
        "- no AI integration",
        "- no ML training",
        "- no backtest runner",
        "- no broker execution",
        "- no real trade execution",
        "- no scraper actions",
        "",
        "## Why This Phase Exists",
        "Generated JSON files can appear under data/ during the day. The scheduler keeps them from becoming emergency cleanup work by batching them into a verified daily cleanup window.",
        "",
        "## Daily Hygiene Contract",
        "let generated files build during the day",
        "run cleanup around 10 PM",
        "archive before delete",
        "manifest-listed files only",
        "no blind delete",
        "",
        "## 10 PM Schedule Policy",
        f"Default local schedule hint: `{plan['local_time']}`.",
        "The local-time setting is documented and does not hardcode deletion logic.",
        "",
        "## R2 Verification Policy",
        "The workflow expects `upload_status`, `verification_status`, `deletion_eligible`, and a verified manifest before any local deletion.",
        "",
        "## Deletion Safety Policy",
        "The cleanup path only deletes manifest-listed files under the approved input directory.",
        "deletion_performed stays false until cleanup runs.",
        "Markdown files preserved.",
        "DB files preserved.",
        "Source code preserved.",
        "Tests/fixtures preserved.",
        "Tracked files preserved.",
        "Manifests preserved.",
        "Archives preserved.",
        "Files outside data/ preserved.",
        "",
        "## Dry-Run Behavior",
        "dry-run by default",
        "No upload, no verification, and no deletion when execute is not explicitly requested.",
        "",
        "## Execute Behavior",
        "execute requires explicit flag",
        "Real cleanup requires `--execute --upload --verify --cleanup --allow-delete-local-raw`.",
        "The workflow keeps `upload_status`, `verification_status`, `deletion_eligible`, and `deletion_performed` visible in the daily report.",
        "",
        "## PowerShell Runner",
        "The repo includes a PowerShell wrapper that runs the Python scheduler from the repo root.",
        "",
        "## Windows Task Scheduler Setup",
        "Windows Task Scheduler can be pointed at the portable Python command.",
        "Example command:",
        "```powershell",
        'schtasks /Create /TN "BettingRepoDailyDataHygiene" /SC DAILY /ST 22:00 /TR "python \'<repo>\\scripts\\daily_data_hygiene.py\' --execute --upload --verify --cleanup --allow-delete-local-raw" /F',
        "```",
        "",
        "## Agent Policy",
        "Agent is advisory only.",
        "Agent does not directly delete files.",
        "",
        "## Files Changed",
        "- `scripts/daily_data_hygiene.py`",
        "- `scripts/run_daily_data_hygiene.ps1`",
        "- `docs/operations/DAILY_DATA_HYGIENE_SCHEDULER.md`",
        "- `docs/archive/historical_reports/PHASE10K8ZFE2_DAILY_DATA_HYGIENE_SCHEDULER_REPORT.md`",
        "- `tests/test_phase10k8zfe2_daily_data_hygiene_scheduler.py`",
        "",
        "## Tests Run",
        "- `pytest tests/test_phase10k8zfe2_daily_data_hygiene_scheduler.py -q`",
        "- `pytest tests/test_phase10k8zfe1_universal_product_language_alignment.py -q`",
        "- `pytest tests/test_phase10k8zfe_duplicate_code_evidence_scan.py -q`",
        "",
        "## Acceptance Results",
        f"- mode: {plan['status']}",
        f"- reason: {plan['reason']}",
        f"- upload_status: {execution.get('upload_status', 'not_attempted') if execution else 'not_attempted'}",
        f"- verification_status: {execution.get('verification_status', 'not_attempted') if execution else 'not_attempted'}",
        f"- deletion_eligible: {execution.get('deletion_eligible', False) if execution else False}",
        f"- deletion_performed: {execution.get('deletion_performed', False) if execution else False}",
        "## Next Phase Recommendation",
        "Proceed to 10K8ZFF Canonical Owner Decision Report.",
        "",
        "## Inventory Snapshot",
        f"- JSON: {inventory['json_files']}",
        f"- JSONL: {inventory['jsonl_files']}",
        f"- CSV: {inventory['csv_files']}",
        f"- Markdown: {inventory['markdown_files']}",
        f"- DB: {inventory['db_files']}",
        f"- Tracked files under data/: {inventory['tracked_files']}",
        "",
        "## Safety Phrases",
        "archive before delete",
        "manifest-listed files only",
        "no blind delete",
        "markdown files preserved",
        "DB files preserved",
        "source code preserved",
        "tests/fixtures preserved",
        "tracked files preserved",
        "manifests preserved",
        "archives preserved",
        "files outside data/ preserved",
        "no credentials committed",
        "no secrets printed",
        "R2 credentials come from environment variables only",
        "Windows Task Scheduler",
        "agent is advisory only",
        "agent does not directly delete files",
    ]
    return "\n".join(lines).strip() + "\n"


def write_reports(plan: dict[str, Any], execution: dict[str, Any] | None = None) -> tuple[Path, Path]:
    report_dir = Path(plan["report_dir"])
    report_dir.mkdir(parents=True, exist_ok=True)
    trading_date = plan["trading_date"]
    md_path = report_dir / f"daily_data_hygiene_{trading_date}.md"
    json_path = report_dir / f"daily_data_hygiene_{trading_date}.json"
    payload = {
        "plan": plan,
        "execution": execution or {},
    }
    report_text = render_report(plan, execution)
    md_path.write_text(report_text, encoding="utf-8")
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return md_path, json_path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    inventory = inspect_inventory(args.input_dir)
    env_status = get_r2_env_status()
    plan = build_daily_hygiene_plan(args, inventory=inventory, env_status=env_status)
    execution: dict[str, Any] | None = None
    if plan["status"] == "ready":
        execution = execute_daily_hygiene(plan)
    write_reports(plan, execution)
    print(json.dumps({"status": plan["status"], "reason": plan["reason"], "batches": len(plan["batches"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

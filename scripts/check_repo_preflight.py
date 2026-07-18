from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ACCEPTED_BRANCHES = {
    "phase-6-api-slimming",
    "feature/external-research-data-storage",
    "feature/nfl-backtesting",
    "main",
}
DEFAULT_EXPECTED_BRANCH = "feature/external-research-data-storage"
ALLOWED_MODES = {"start-task", "end-task", "before-commit", "before-push"}

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.check_architecture import collect_architecture_report  # noqa: E402
from scripts.check_audit_lifecycle import collect_audit_lifecycle_report  # noqa: E402
from scripts.check_document_lifecycle import collect_document_lifecycle_report  # noqa: E402
from scripts.check_openapi_contract import collect_openapi_report  # noqa: E402
from scripts.check_root_markdown import find_root_markdown, recommended_destination  # noqa: E402
from src.services.ops_workflow import run_ops_check  # noqa: E402


def _run_git(args: list[str], root: Path = ROOT, timeout: int = 10) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except Exception as exc:  # pragma: no cover - defensive fallback
        return 127, f"{exc.__class__.__name__}: {exc}"
    output = (completed.stdout or completed.stderr or "").strip()
    return int(completed.returncode), output


def _git_value(args: list[str], root: Path = ROOT) -> str | None:
    code, output = _run_git(args, root=root)
    return output if code == 0 and output else None


def _git_lines(args: list[str], root: Path = ROOT) -> list[str]:
    code, output = _run_git(args, root=root)
    if code != 0 or not output:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def _git_state(root: Path = ROOT) -> dict[str, Any]:
    branch = _git_value(["branch", "--show-current"], root=root) or "detached"
    head = _git_value(["rev-parse", "HEAD"], root=root)
    upstream = _git_value(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], root=root)
    ahead: int | None = None
    behind: int | None = None
    if upstream:
        counts = _git_value(["rev-list", "--left-right", "--count", "HEAD...@{u}"], root=root)
        if counts:
            parts = counts.split()
            if len(parts) >= 2:
                try:
                    ahead = int(parts[0])
                    behind = int(parts[1])
                except ValueError:
                    ahead = behind = None
    staged_files = _git_lines(["diff", "--cached", "--name-only", "--diff-filter=ACMRDTUXB"], root=root)
    modified_files = _git_lines(["diff", "--name-only", "--diff-filter=ACMRDTUXB"], root=root)
    untracked_files = _git_lines(["ls-files", "--others", "--exclude-standard"], root=root)
    status_summary = _git_value(["status", "--short", "--branch"], root=root) or ""
    return {
        "branch": branch,
        "head": head,
        "upstream": upstream,
        "ahead": ahead,
        "behind": behind,
        "staged_files": staged_files,
        "modified_files": modified_files,
        "untracked_files": untracked_files,
        "status_summary": status_summary,
    }


def _check_root_markdown(root: Path = ROOT) -> dict[str, Any]:
    offenders = find_root_markdown(root)
    return {
        "status": "ok" if not offenders else "fail",
        "offenders": [
            {
                "path": path.relative_to(root).as_posix() if path.is_absolute() else path.as_posix(),
                "recommended_destination": recommended_destination(path),
            }
            for path in offenders
        ],
    }


def _check_openapi(root: Path = ROOT) -> dict[str, Any]:
    return dict(collect_openapi_report(root))


def _check_architecture(root: Path = ROOT) -> dict[str, Any]:
    return dict(collect_architecture_report(root))


def _check_audit_lifecycle(root: Path = ROOT) -> dict[str, Any]:
    return dict(collect_audit_lifecycle_report(root))


def _check_document_lifecycle(root: Path = ROOT) -> dict[str, Any]:
    return dict(collect_document_lifecycle_report(root))


def _check_ops(root: Path = ROOT) -> dict[str, Any]:
    del root
    return dict(run_ops_check(mode="local", skip_network=True, write_report=False))


def collect_repo_preflight_report(
    root: Path = ROOT,
    *,
    mode: str = "start-task",
    include_ops: bool = False,
) -> dict[str, Any]:
    mode = (mode or "start-task").strip().lower()
    if mode not in ALLOWED_MODES:
        raise ValueError(f"unsupported preflight mode: {mode}")

    git = _git_state(root)
    checks: dict[str, dict[str, Any]] = {
        "root_markdown": _check_root_markdown(root),
        "openapi": _check_openapi(root),
        "architecture": _check_architecture(root),
        "audit_lifecycle": _check_audit_lifecycle(root),
        "document_lifecycle": _check_document_lifecycle(root),
    }
    if include_ops:
        ops_report = _check_ops(root)
        blocker = ops_report.get("blocker_classification") or {}
        ops_report["status"] = "ok" if blocker.get("primary") in {None, "ok"} else "reported"
        checks["ops"] = ops_report

    warnings: list[str] = []
    clear_violations: list[str] = []

    branch = git["branch"]
    head = git["head"]
    upstream = git["upstream"]
    staged_files = list(git["staged_files"])
    modified_files = list(git["modified_files"])
    untracked_files = list(git["untracked_files"])
    ahead = git["ahead"]
    behind = git["behind"]

    expected_branch = branch if branch in ACCEPTED_BRANCHES else DEFAULT_EXPECTED_BRANCH
    expected_upstream = f"origin/{expected_branch}"

    if branch not in ACCEPTED_BRANCHES:
        allowed = ", ".join(sorted(repr(item) for item in ACCEPTED_BRANCHES))
        clear_violations.append(f"branch mismatch: expected one of [{allowed}], found {branch!r}")
    if not head:
        clear_violations.append("HEAD could not be resolved")
    if not upstream:
        clear_violations.append(f"upstream is not configured for {branch!r}")
    elif upstream != expected_upstream:
        clear_violations.append(f"upstream mismatch: expected {expected_upstream!r}, found {upstream!r}")
    if ahead is None or behind is None:
        if upstream:
            clear_violations.append(f"branch divergence could not be determined for upstream {upstream!r}")
    else:
        if mode in {"start-task", "end-task", "before-commit"}:
            if ahead != 0 or behind != 0:
                clear_violations.append(f"branch divergence: ahead={ahead} behind={behind}")
        elif mode == "before-push":
            if behind != 0:
                clear_violations.append(f"branch divergence: ahead={ahead} behind={behind}")
            elif ahead <= 0:
                clear_violations.append(f"no local commits available to push: ahead={ahead} behind={behind}")

    if mode in {"start-task", "end-task", "before-push"} and staged_files:
        clear_violations.append(f"index is not clean: {len(staged_files)} staged file(s)")
    if modified_files or untracked_files:
        dirty_count = len(modified_files) + len(untracked_files)
        clear_violations.append(f"working tree is not clean: {dirty_count} file(s)")
    elif mode == "before-commit" and not staged_files:
        warnings.append("before-commit mode has no staged files to review")

    root_markdown = checks["root_markdown"]
    if root_markdown["status"] != "ok":
        offender_list = ", ".join(item["path"] for item in root_markdown["offenders"]) or "unknown"
        clear_violations.append(f"root markdown violations: {offender_list}")

    openapi = checks["openapi"]
    if not openapi.get("ok"):
        clear_violations.append(f"openapi contract violations: {len(openapi.get('errors') or [])}")

    architecture = checks["architecture"]
    if architecture.get("root_markdown_offenders") or architecture.get("ignored_source_files") or architecture.get("legacy_import_issues"):
        clear_violations.append(
            "architecture violations: "
            f"root_markdown={len(architecture.get('root_markdown_offenders') or [])}, "
            f"ignored_source_files={len(architecture.get('ignored_source_files') or [])}, "
            f"legacy_import_issues={len(architecture.get('legacy_import_issues') or [])}"
        )

    audit = checks["audit_lifecycle"]
    if audit.get("clear_violations"):
        clear_violations.append(f"audit lifecycle violations: {len(audit.get('clear_violations') or [])}")

    document = checks["document_lifecycle"]
    if document.get("clear_violations"):
        clear_violations.append(f"document lifecycle violations: {len(document.get('clear_violations') or [])}")

    report: dict[str, Any] = {
        "mode": mode,
        "root": str(root),
        "expected_branch": expected_branch,
        "expected_upstream": expected_upstream,
        "accepted_branches": sorted(ACCEPTED_BRANCHES),
        "branch": branch,
        "head": head,
        "upstream": upstream,
        "ahead": ahead,
        "behind": behind,
        "working_tree_clean": not modified_files and not untracked_files,
        "index_clean": not staged_files,
        "staged_files": staged_files,
        "modified_files": modified_files,
        "untracked_files": untracked_files,
        "checks": checks,
        "warnings": warnings,
        "clear_violations": clear_violations,
        "ok": not clear_violations,
        "status": "ok" if not clear_violations else "fail",
        "status_summary": git["status_summary"],
    }
    return report


def _render_text(report: dict[str, Any]) -> str:
    checks = report.get("checks") or {}
    lines = [
        f"repo_preflight: {report.get('status')}",
        f"mode: {report.get('mode')}",
        f"branch: {report.get('branch')}",
        f"expected_branch: {report.get('expected_branch')}",
        f"upstream: {report.get('upstream')}",
        f"head: {report.get('head')}",
        f"ahead: {report.get('ahead')}",
        f"behind: {report.get('behind')}",
        f"working_tree_clean: {report.get('working_tree_clean')}",
        f"index_clean: {report.get('index_clean')}",
        f"staged_files: {len(report.get('staged_files') or [])}",
        f"modified_files: {len(report.get('modified_files') or [])}",
        f"untracked_files: {len(report.get('untracked_files') or [])}",
        f"root_markdown: {checks.get('root_markdown', {}).get('status')}",
        f"openapi: {'ok' if (checks.get('openapi') or {}).get('ok') else 'fail'}",
        f"architecture: {'ok' if not ((checks.get('architecture') or {}).get('root_markdown_offenders') or (checks.get('architecture') or {}).get('ignored_source_files') or (checks.get('architecture') or {}).get('legacy_import_issues')) else 'fail'}",
        f"audit_lifecycle: {'ok' if not (checks.get('audit_lifecycle') or {}).get('clear_violations') else 'fail'}",
        f"document_lifecycle: {'ok' if not (checks.get('document_lifecycle') or {}).get('clear_violations') else 'fail'}",
        f"warnings: {len(report.get('warnings') or [])}",
        f"clear_violations: {len(report.get('clear_violations') or [])}",
    ]
    if "ops" in checks:
        blocker = (checks["ops"].get("blocker_classification") or {})
        lines.append(f"ops: {checks['ops'].get('blocker_classification', {}).get('primary')}")
        lines.append(f"ops_recommended_action: {blocker.get('recommended_action')}")
    if report.get("clear_violations"):
        lines.append("clear_violation_details:")
        for item in report["clear_violations"]:
            lines.append(f"- {item}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check repository pre-flight safety conditions.")
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--start-task", dest="mode", action="store_const", const="start-task", help="Check safety before beginning work.")
    mode_group.add_argument("--end-task", dest="mode", action="store_const", const="end-task", help="Check safety before finishing work.")
    mode_group.add_argument("--before-commit", dest="mode", action="store_const", const="before-commit", help="Check safety before committing.")
    mode_group.add_argument("--before-push", dest="mode", action="store_const", const="before-push", help="Check safety before pushing.")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    parser.add_argument("--include-ops", action="store_true", help="Also run the local ops workflow and report its status.")
    args = parser.parse_args(argv)

    report = collect_repo_preflight_report(ROOT, mode=args.mode, include_ops=args.include_ops)
    if args.output == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_render_text(report))
    return 0 if report.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

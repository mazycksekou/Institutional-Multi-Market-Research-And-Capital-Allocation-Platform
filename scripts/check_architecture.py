from __future__ import annotations

import argparse
import json
import subprocess
import sys
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.services.repo_inventory import build_import_index, tracked_python_files


ALLOWED_ROOT_MARKDOWN = {"README.md"}
ALLOWED_ROOT_PYTHON = {"api_server.py", "main.py", "streamlit_app.py"}
ARCHIVE_HINTS = (
    'ROOT / "PHASE',
    'ROOT.glob("PHASE',
    'Path("PHASE',
    'LEGACY_ROOT = ROOT / "src" / "automation_scheduler_legacy"',
    "src/automation_scheduler_legacy",
    "automation_scheduler_legacy",
)
ARCHIVE_ALLOWLIST = {
    "tests/test_phase1_legacy_inventory.py",
    "tests/test_phase3b_local_data_platform.py",
}
LEGACY_IMPORT_TARGET_PREFIXES = (
    "automation_scheduler",
    "automation_scheduler_legacy",
    "src.automation_scheduler_legacy",
    "src.services.automation_scheduler_facade",
)


def _is_archived_test(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    if rel in ARCHIVE_ALLOWLIST:
        return False
    if not rel.startswith("tests/test_phase"):
        return False
    if path.name.startswith("test_phase10k") or path.name.startswith("test_phase_x"):
        return True
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return False
    return any(hint in text for hint in ARCHIVE_HINTS)


def _root_python_files(root: Path = ROOT) -> list[str]:
    return sorted(
        path.name
        for path in root.iterdir()
        if path.is_file() and path.suffix == ".py"
    )


def _root_markdown_offenders(root: Path = ROOT) -> list[str]:
    return sorted(
        path.name
        for path in root.iterdir()
        if path.is_file() and path.suffix.lower() == ".md" and path.name not in ALLOWED_ROOT_MARKDOWN
    )


def _ignored_source_files(root: Path = ROOT) -> list[dict[str, str]]:
    offenders: list[dict[str, str]] = []
    git_path = shutil.which("git")
    if git_path is None:
        return [{"path": "<git>", "rule": "git is required for ignored source file validation"}]
    for path in tracked_python_files(root):
        rel = path.relative_to(root).as_posix()
        if not rel.startswith("src/") or path.suffix != ".py":
            continue
        try:
            result = subprocess.run(
                [git_path, "check-ignore", "-v", rel],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            return [{"path": "<git>", "rule": "git is required for ignored source file validation"}]
        if result.returncode == 0 and result.stdout.strip():
            offenders.append({"path": rel, "rule": result.stdout.strip()})
    return offenders


def _legacy_import_issues(root: Path = ROOT) -> list[dict[str, Any]]:
    import_index = build_import_index(root)
    issues: list[dict[str, Any]] = []
    for module, categories in sorted(import_index.items()):
        if not module.startswith(LEGACY_IMPORT_TARGET_PREFIXES):
            continue
        runtime_importers = sorted(
            importer
            for importer in categories.get("runtime", [])
            if not (importer.startswith("tests/") and _is_archived_test(root / importer))
        )
        test_importers = sorted(
            importer
            for importer in categories.get("test", [])
            if not _is_archived_test(root / importer)
        )
        script_importers = sorted(
            importer
            for importer in categories.get("script", [])
            if not _is_archived_test(root / importer)
        )
        if runtime_importers or test_importers or script_importers:
            issues.append(
                {
                    "module": module,
                    "runtime_importers": runtime_importers,
                    "test_importers": test_importers,
                    "script_importers": script_importers,
                }
            )
    return issues


def collect_architecture_report(root: Path = ROOT) -> dict[str, Any]:
    tracked = tracked_python_files(root)
    active_tests = [path for path in tracked if not _is_archived_test(path)]
    root_python_files = _root_python_files(root)
    non_src_runtime_python_files = sorted(
        path.relative_to(root).as_posix()
        for path in tracked
        if path.suffix == ".py"
        and not path.relative_to(root).as_posix().startswith(("src/", "tests/", "scripts/"))
    )
    return {
        "root": str(root),
        "root_python_files": root_python_files,
        "non_src_runtime_python_files": non_src_runtime_python_files,
        "approved_entrypoints": sorted(ALLOWED_ROOT_PYTHON),
        "root_markdown_offenders": _root_markdown_offenders(root),
        "ignored_source_files": _ignored_source_files(root),
        "legacy_import_issues": _legacy_import_issues(root),
        "archived_tests": sorted(
            path.relative_to(root).as_posix()
            for path in tracked
            if path.relative_to(root).as_posix().startswith("tests/") and path not in active_tests
        ),
    }


def _text_report(report: dict[str, Any]) -> str:
    lines = [
        f"root: {report['root']}",
        f"root_python_files: {', '.join(report['root_python_files']) or 'none'}",
        f"non_src_runtime_python_files: {len(report['non_src_runtime_python_files'])}",
        f"approved_entrypoints: {', '.join(report['approved_entrypoints'])}",
        f"root_markdown_offenders: {len(report['root_markdown_offenders'])}",
        f"ignored_source_files: {len(report['ignored_source_files'])}",
        f"legacy_import_issues: {len(report['legacy_import_issues'])}",
        f"archived_tests: {len(report['archived_tests'])}",
    ]
    for offender in report["root_markdown_offenders"]:
        lines.append(f"root_markdown_offender: {offender}")
    for offender in report["ignored_source_files"]:
        lines.append(f"ignored_source_file: {offender['path']} :: {offender['rule']}")
    for issue in report["legacy_import_issues"]:
        runtime = ", ".join(issue["runtime_importers"]) or "-"
        tests = ", ".join(issue["test_importers"]) or "-"
        scripts = ", ".join(issue["script_importers"]) or "-"
        lines.append(f"legacy_import: {issue['module']} runtime=[{runtime}] test=[{tests}] script=[{scripts}]")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check repository architecture constraints.")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    report = collect_architecture_report(ROOT)
    if args.output == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_text_report(report))

    failures = bool(report["root_markdown_offenders"] or report["ignored_source_files"] or report["legacy_import_issues"])
    return 2 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

from __future__ import annotations

import ast
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXCLUDED_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "build",
    "dist",
}


def _is_excluded(path: Path) -> bool:
    return bool(set(path.parts) & EXCLUDED_DIRS)


def _python_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*.py")
        if path.is_file() and not _is_excluded(path)
    )


def _read_python(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def test_all_repo_python_files_parse_cleanly():
    failures = []

    for path in _python_files():
        text = _read_python(path)
        try:
            ast.parse(text)
        except SyntaxError as exc:
            failures.append(f"{path.relative_to(ROOT)}:{exc.lineno}: {exc.msg}")

    assert failures == []


def test_no_direct_python_imports_from_main_module():
    failures = []

    for path in _python_files():
        rel = path.relative_to(ROOT).as_posix()
        text = _read_python(path)
        tree = ast.parse(text)

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "main":
                failures.append(f"{rel}:{node.lineno}: from main import ...")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "main":
                        failures.append(f"{rel}:{node.lineno}: import main")

    assert failures == []


def test_main_py_remains_app_assembly_without_direct_route_decorators():
    main_path = ROOT / "main.py"
    assert main_path.exists()

    tree = ast.parse(_read_python(main_path))
    direct_routes = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        for decorator in node.decorator_list:
            try:
                rendered = ast.unparse(decorator)
            except Exception:
                rendered = ""

            if rendered.startswith("app."):
                direct_routes.append(f"{node.name}:{node.lineno}:{rendered}")

    assert direct_routes == []


def test_generated_runtime_data_is_not_tracked_by_git():
    tracked = subprocess.check_output(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
    ).splitlines()

    runtime_prefixes = (
        "data/backtests/",
        "data/calibration/",
        "data/clv/",
        "data/paper_ledger/",
        "data/review_queue/",
        "data/reports/",
        "data/performance_reports/",
        "data/system_health/",
        "logs/",
    )

    bad = [
        path
        for path in tracked
        if path.startswith(runtime_prefixes)
        and not path.startswith("data/fixtures/")
    ]

    assert bad == []

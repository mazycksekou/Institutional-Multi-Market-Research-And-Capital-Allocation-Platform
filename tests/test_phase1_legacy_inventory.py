from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
LEGACY_ROOT = ROOT / "src" / "automation_scheduler_legacy"
DOCS = [
    ROOT / "docs" / "reports" / "inventories" / "PHASE1_LEGACY_INVENTORY.md",
    ROOT / "docs" / "archive" / "historical_reports" / "PHASE1_CLASSIFICATION.md",
    ROOT / "docs" / "archive" / "historical_reports" / "PHASE1_DELETE_LIST.md",
    ROOT / "docs" / "archive" / "historical_reports" / "PHASE1_IMPORT_GRAPH.md",
]
ALLOWED_BRANCHES = {
    "feature/external-research-data-storage",
    "feature/nfl-backtesting",
    "phase-6-api-slimming",
    "main",
}

pytestmark = pytest.mark.smoke


def _read_json(path: Path) -> dict:
    assert path.is_file(), path
    return json.loads(path.read_text(encoding="utf-8"))


def _legacy_python_files() -> list[str]:
    return sorted(path.relative_to(ROOT).as_posix() for path in LEGACY_ROOT.rglob("*.py"))


def _resolve_branch_name() -> str | None:
    for env_var in ("GITHUB_HEAD_REF", "GITHUB_REF_NAME"):
        value = os.environ.get(env_var, "").strip()
        if value:
            return value

    for command in (
        ["git", "branch", "--show-current"],
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
    ):
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        branch = (completed.stdout or completed.stderr or "").strip()
        if completed.returncode == 0 and branch and branch != "HEAD":
            return branch
    return None


def _run_ops_check(mode: str, input_path: Path, output_path: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            "scripts/ops_check.py",
            "--mode",
            mode,
            "--input",
            str(input_path),
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        check=True,
    )


def test_phase1_legacy_inventory_reflects_final_decommission() -> None:
    for doc in DOCS:
        assert doc.is_file(), doc

    assert not LEGACY_ROOT.exists()
    assert not (ROOT / "automation_scheduler").exists()

    branch_name = _resolve_branch_name()
    if branch_name is not None:
        assert branch_name in ALLOWED_BRANCHES

    assert _legacy_python_files() == []


def test_phase1_legacy_inventory_branch_resolution_prefers_ci_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_HEAD_REF", "phase-6-api-slimming")
    monkeypatch.setenv("GITHUB_REF_NAME", "pull/123/merge")
    assert _resolve_branch_name() == "phase-6-api-slimming"


def test_phase1_legacy_inventory_accepts_main_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_HEAD_REF", raising=False)
    monkeypatch.setenv("GITHUB_REF_NAME", "main")
    assert _resolve_branch_name() == "main"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))

from __future__ import annotations

import json
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

pytestmark = pytest.mark.smoke


def _read_json(path: Path) -> dict:
    assert path.is_file(), path
    return json.loads(path.read_text(encoding="utf-8"))


def _legacy_python_files() -> list[str]:
    return sorted(path.relative_to(ROOT).as_posix() for path in LEGACY_ROOT.rglob("*.py"))


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
    assert subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip() == "phase-6-api-slimming"

    assert _legacy_python_files() == []

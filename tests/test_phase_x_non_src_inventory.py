from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.services.repo_inventory import tracked_python_files


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs" / "reports" / "inventories" / "inventory_PHASE_X.json"
IMPORT_SCAN = ROOT / "docs" / "reports" / "inventories" / "import_scan_PHASE_X.json"

pytestmark = pytest.mark.smoke


def _read_json(path: Path) -> dict:
    assert path.exists(), f"missing report: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def test_inventory_reports_cover_current_non_src_python_files() -> None:
    inventory = _read_json(INVENTORY)
    import_scan = _read_json(IMPORT_SCAN)
    current_non_src = [
        path
        for path in tracked_python_files(ROOT)
        if not path.relative_to(ROOT).as_posix().startswith("src/")
    ]

    assert len(inventory["files"]) == len(current_non_src)
    assert len(import_scan["files"]) == len(current_non_src)

    for row in inventory["files"]:
        assert row["path"]
        assert row["classification"]
        assert row["canonical_target"].startswith("src.")

    for row in import_scan["files"]:
        assert row["path"]
        assert row["canonical_target"].startswith("src.")


def test_safe_legacy_files_were_deleted_during_cleanup() -> None:
    for rel in (
        "asian_markets.py",
        "authentication_scheduler/line_movement_import_contract.py",
        "betting_providers/__init__.py",
        "betting_providers/aliases.py",
        "config.py",
        "logger_setup.py",
        "parlay_engine.py",
        "providers/__init__.py",
        "research/__init__.py",
        "research_engine/__init__.py",
        "research_engine/decision_committee.py",
        "research_engine/evidence_scorecard.py",
    ):
        assert not (ROOT / rel).exists(), rel

    assert not (ROOT / "automation_scheduler").exists()
    assert not (ROOT / "We'll produce SEARCH/REPLACE block.automation_scheduler/streamlit_dashboard_data.py").exists()

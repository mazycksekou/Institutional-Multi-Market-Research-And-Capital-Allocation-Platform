from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8ZFH_SAFE_MIGRATION_BATCH_2_BOUNDARY_GUARDS_REPORT.md"
README = ROOT / "README.md"
STREAMLIT_APP = ROOT / "streamlit_app.py"
DASHBOARD_DATA = ROOT / "automation_scheduler" / "streamlit_dashboard_data.py"
DAILY_HYGIENE_SCRIPT = ROOT / "scripts" / "daily_data_hygiene.py"
RUNNER = ROOT / "scripts" / "run_daily_data_hygiene.ps1"
ARCHIVE_MANIFEST = ROOT / "src" / "storage" / "archive_manifest.py"
R2_ADAPTER = ROOT / "src" / "storage" / "r2_archive_adapter.py"
MAIN = ROOT / "main.py"
API_SERVER = ROOT / "api_server.py"
SRC_API_DIR = ROOT / "src" / "api"
CANONICAL_REPORT = ROOT / "PHASE10K8ZFF_CANONICAL_OWNER_DECISION_REPORT.md"
BATCH1_REPORT = ROOT / "PHASE10K8ZFG_SAFE_MIGRATION_BATCH_1_REPORT.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains_all(text: str, items: list[str], label: str) -> None:
    for item in items:
        assert item in text, f"Missing {label} string: {item}"


def test_phase10k8zfh_safe_migration_batch_2_boundary_guards() -> None:
    assert REPORT.exists()
    assert MAIN.exists()
    assert API_SERVER.exists()
    assert SRC_API_DIR.exists()
    assert DAILY_HYGIENE_SCRIPT.exists()
    assert RUNNER.exists()
    assert ARCHIVE_MANIFEST.exists()
    assert R2_ADAPTER.exists()
    assert CANONICAL_REPORT.exists()
    assert BATCH1_REPORT.exists()

    report = read_text(REPORT)
    readme = read_text(README)
    streamlit_text = read_text(STREAMLIT_APP)
    dashboard_text = read_text(DASHBOARD_DATA)
    hygiene_text = read_text(DAILY_HYGIENE_SCRIPT)
    canonical_report = read_text(CANONICAL_REPORT)
    batch1_report = read_text(BATCH1_REPORT)

    required_sections = [
        "Executive Summary",
        "Current HEAD",
        "Purpose",
        "Scope",
        "Non-Goals",
        "Relationship to 10K8ZFF",
        "Relationship to 10K8ZFG",
        "Boundary Guard Strategy",
        "API Ownership Boundary",
        "Dashboard Ownership Boundary",
        "Daily Hygiene / Storage Operation Boundary",
        "Risk Preset / Scenario Language Boundary",
        "Orchestration Boundary",
        "Canonical Report Preservation",
        "Files Changed",
        "Source Changes",
        "Functions Migrated Or Wrapped",
        "Functions Deferred",
        "Must-Not-Delete-Yet Compliance",
        "Behavior Preservation Evidence",
        "Safety Gate Results",
        "Tests Run",
        "Acceptance Results",
        "Next Phase Recommendation",
    ]
    for section in required_sections:
        assert f"## {section}" in report

    assert_contains_all(
        report,
        [
            "10K8ZFH",
            "Safe Migration Batch 2",
            "Ownership Boundary Guards",
            "boundary guard phase",
            "canonical owner",
            "canonical ownership map",
            "migration direction",
            "old import path preserved",
            "behavior unchanged",
            "no files deleted",
            "no files moved",
            "no public functions removed",
            "no source-function migration",
            "no code migrated without tests",
            "no AI integration",
            "no ML training",
            "no backtest runner",
            "no controlled data loader",
            "no broker execution",
            "no real trade execution",
            "no scraper actions",
            "source code was preserved",
            "tests/fixtures were preserved",
            "manifests were preserved",
            "archives were preserved",
            "tracked files were preserved",
            "must_not_delete_yet complied",
            "daily data hygiene scheduler remains operational",
            "dry-run by default",
            "execute requires explicit flag",
            "agent is advisory only",
            "agent does not directly delete files",
            "risk preset controls sizing",
            "scenario mode controls missing-data handling",
            "API ownership boundary",
            "dashboard ownership boundary",
            "storage operation boundary",
            "orchestration boundary",
            "This phase does not authorize deletion.",
            "Proceed to 10K8ZFI automation_scheduler Decomposition Plan",
        ],
        "report",
    )

    assert "This phase does not authorize deletion." in report
    assert "no files deleted" in report
    assert "no files moved" in report
    assert "no public functions removed" in report
    assert "no source-function migration" in report
    assert "behavior unchanged" in report

    assert "API ownership boundary" in report
    assert "dashboard ownership boundary" in report
    assert "storage operation boundary" in report
    assert "orchestration boundary" in report

    assert "Aggressive paper only" not in streamlit_text
    assert "Aggressive" in dashboard_text
    assert "risk preset controls sizing" in dashboard_text.lower()
    assert "scenario mode controls missing-data handling" in dashboard_text.lower()
    assert "Baseline / Imputed" in dashboard_text
    assert "Strict / Complete Cases Only" in dashboard_text
    assert "Stress / Adverse Missing-Data Fill" in dashboard_text

    assert "dry-run by default" in hygiene_text
    assert "--execute" in hygiene_text
    assert "allow-delete-local-raw" in hygiene_text

    assert "from src.services.streamlit_dashboard_facade import" in streamlit_text

    assert re.search(r"AKIA[0-9A-Z]{16}", report) is None
    assert re.search(r"ASIA[0-9A-Z]{16}", report) is None
    assert "your_real_secret" not in report
    assert re.search(r"AKIA[0-9A-Z]{16}", readme) is None
    assert re.search(r"ASIA[0-9A-Z]{16}", readme) is None
    assert "your_real_secret" not in readme
    assert re.search(r"AKIA[0-9A-Z]{16}", canonical_report) is None
    assert re.search(r"ASIA[0-9A-Z]{16}", canonical_report) is None
    assert "your_real_secret" not in canonical_report
    assert re.search(r"AKIA[0-9A-Z]{16}", batch1_report) is None
    assert re.search(r"ASIA[0-9A-Z]{16}", batch1_report) is None
    assert "your_real_secret" not in batch1_report

    assert not any(ROOT.glob("pages/*.py"))
    assert not any(ROOT.glob("app/pages/*.py"))
    assert not any(ROOT.glob("frontend/*.py"))
    assert not any(ROOT.glob("frontend/pages/*.py"))

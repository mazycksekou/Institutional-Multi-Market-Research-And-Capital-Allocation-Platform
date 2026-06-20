from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8ZFI_AUTOMATION_SCHEDULER_DECOMPOSITION_PLAN.md"
README = ROOT / "README.md"
STREAMLIT_APP = ROOT / "streamlit_app.py"
DASHBOARD_DATA = ROOT / "automation_scheduler" / "streamlit_dashboard_data.py"
DAILY_HYGIENE_SCRIPT = ROOT / "scripts" / "daily_data_hygiene.py"
RUNNER = ROOT / "scripts" / "run_daily_data_hygiene.ps1"
CANONICAL_REPORT = ROOT / "PHASE10K8ZFF_CANONICAL_OWNER_DECISION_REPORT.md"
REPORT_BATCH_1 = ROOT / "PHASE10K8ZFG_SAFE_MIGRATION_BATCH_1_REPORT.md"
REPORT_BATCH_2 = ROOT / "PHASE10K8ZFH_SAFE_MIGRATION_BATCH_2_BOUNDARY_GUARDS_REPORT.md"
EVIDENCE_REPORT = ROOT / "PHASE10K8ZFE_DUPLICATE_CODE_EVIDENCE_SCAN.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains_all(text: str, items: list[str], label: str) -> None:
    for item in items:
        assert item in text, f"Missing {label} string: {item}"


def test_phase10k8zfi_automation_scheduler_decomposition_plan() -> None:
    assert REPORT.exists()
    assert CANONICAL_REPORT.exists()
    assert REPORT_BATCH_1.exists()
    assert REPORT_BATCH_2.exists()
    assert EVIDENCE_REPORT.exists()
    assert DAILY_HYGIENE_SCRIPT.exists()
    assert RUNNER.exists()

    report = read_text(REPORT)
    readme = read_text(README)
    streamlit_text = read_text(STREAMLIT_APP)
    dashboard_text = read_text(DASHBOARD_DATA)
    hygiene_text = read_text(DAILY_HYGIENE_SCRIPT)
    canonical_report = read_text(CANONICAL_REPORT)
    batch1_report = read_text(REPORT_BATCH_1)
    batch2_report = read_text(REPORT_BATCH_2)
    evidence_report = read_text(EVIDENCE_REPORT)

    required_sections = [
        "Executive Summary",
        "Current HEAD",
        "Purpose",
        "Scope",
        "Non-Goals",
        "Relationship to 10K8ZFF",
        "Relationship to 10K8ZFG",
        "Relationship to 10K8ZFH",
        "Decomposition Method",
        "automation_scheduler Inventory",
        "Responsibility Lanes",
        "Orchestration / Scheduler Lane",
        "Dashboard Data Lane",
        "Risk / Gating Lane",
        "Providers / Normalization Lane",
        "Metrics / Reporting Lane",
        "Signals / Features Lane",
        "Backtest / Historical Replay Lane",
        "Storage / Ledgers Lane",
        "Daily / Ops Utilities Lane",
        "Deprecated / Manual Review Candidates",
        "Future Owner Map",
        "Migration Waves",
        "Must-Not-Delete-Yet Compliance",
        "Unsafe Actions",
        "Acceptance Results",
        "Next Phase Recommendation",
    ]
    for section in required_sections:
        assert f"## {section}" in report

    assert_contains_all(
        report,
        [
            "10K8ZFI",
            "automation_scheduler Decomposition Plan",
            "decomposition plan only",
            "no files deleted",
            "no files moved",
            "no source-function migration",
            "no public functions removed",
            "behavior unchanged",
            "automation_scheduler should become orchestration-only",
            "canonical owner",
            "canonical ownership map",
            "migration direction",
            "must_not_delete_yet",
            "future owner map",
            "Orchestration / Scheduler",
            "Dashboard Data",
            "Risk / Gating",
            "Providers / Normalization",
            "Metrics / Reporting",
            "Signals / Features",
            "Backtest / Historical Replay",
            "Storage / Ledgers",
            "Daily / Ops Utilities",
            "Deprecated / Manual Review Candidates",
            "Wave 0",
            "Wave 1",
            "Wave 2",
            "Wave 3",
            "Wave 4",
            "Wave 5",
            "Wave 6",
            "Wave 7",
            "Wave 8",
            "Wave 9",
            "daily data hygiene scheduler remains operational",
            "dry-run by default",
            "agent is advisory only",
            "agent does not directly delete files",
            "risk preset controls sizing",
            "scenario mode controls missing-data handling",
            "no AI integration",
            "no ML training",
            "no backtest runner",
            "no controlled data loader",
            "no broker execution",
            "no real trade execution",
            "no scraper actions",
            "This phase does not authorize deletion.",
            "Proceed to 10K8ZFJ Provider / live_market_intelligence Decomposition Plan",
        ],
        "report",
    )

    assert "This phase does not authorize deletion." in report
    assert "no files deleted" in report
    assert "no files moved" in report
    assert "no source-function migration" in report
    assert "no public functions removed" in report
    assert "behavior unchanged" in report
    assert "automation_scheduler should become orchestration-only" in report
    assert "future owner map" in report
    assert "must_not_delete_yet" in report

    assert "Aggressive paper only" not in streamlit_text
    assert "Aggressive" in dashboard_text
    assert "Baseline / Imputed" in dashboard_text
    assert "Strict / Complete Cases Only" in dashboard_text
    assert "Stress / Adverse Missing-Data Fill" in dashboard_text
    assert "risk preset controls sizing" in dashboard_text.lower()
    assert "scenario mode controls missing-data handling" in dashboard_text.lower()

    assert "dry-run by default" in hygiene_text
    assert "execute requires explicit flag" in hygiene_text
    assert "agent is advisory only" in hygiene_text
    assert "from automation_scheduler.streamlit_dashboard_data import" in streamlit_text

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
    assert re.search(r"AKIA[0-9A-Z]{16}", batch2_report) is None
    assert re.search(r"ASIA[0-9A-Z]{16}", batch2_report) is None
    assert "your_real_secret" not in batch2_report
    assert re.search(r"AKIA[0-9A-Z]{16}", evidence_report) is None
    assert re.search(r"ASIA[0-9A-Z]{16}", evidence_report) is None
    assert "your_real_secret" not in evidence_report

    assert not any(ROOT.glob("pages/*.py"))
    assert not any(ROOT.glob("app/pages/*.py"))
    assert not any(ROOT.glob("frontend/*.py"))
    assert not any(ROOT.glob("frontend/pages/*.py"))


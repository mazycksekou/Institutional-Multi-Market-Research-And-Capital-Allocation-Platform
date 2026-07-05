from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8ZFF_CANONICAL_OWNER_DECISION_REPORT.md"
README = ROOT / "README.md"
SOURCE_FILES = [
    ROOT / "main.py",
    ROOT / "streamlit_app.py",
    ROOT / "src" / "services" / "streamlit_dashboard_data.py",
    ROOT / "scripts" / "daily_data_hygiene.py",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains_all(text: str, items: list[str], label: str) -> None:
    for item in items:
        assert item in text, f"Missing {label} string: {item}"


def test_phase10k8zff_canonical_owner_decision_report() -> None:
    assert REPORT.exists()

    report = read_text(REPORT)
    readme = read_text(README)
    source_texts = [read_text(path) for path in SOURCE_FILES if path.exists()]

    required_sections = [
        "Executive Summary",
        "Current HEAD",
        "Purpose",
        "Scope",
        "Non-Goals",
        "Relationship to 10K8ZFE",
        "Relationship to 10K8ZFE1",
        "Relationship to 10K8ZFE2",
        "Decision Method",
        "Target Architecture",
        "Canonical Owner Summary Table",
        "Math / Core Calculation Decision",
        "Metrics / Performance Decision",
        "Signals / Features Decision",
        "Risk Decision",
        "Providers / Data Adapter Decision",
        "Backtest Decision",
        "Storage / Ledger / Archive Decision",
        "API Route Decision",
        "Dashboard Data Decision",
        "Orchestration / Scheduler Decision",
        "Must-Not-Delete-Yet List",
        "Future Deprecation Candidates",
        "Migration Order",
        "Safe Next Actions",
        "Unsafe Actions",
        "Acceptance Results",
        "Next Phase Recommendation",
    ]
    for section in required_sections:
        assert f"## {section}" in report

    assert_contains_all(
        report,
        [
            "10K8ZFF",
            "Canonical Owner Decision Report",
            "canonical owner",
            "canonical future owner",
            "migration direction",
            "must_not_delete_yet",
            "future deprecation candidate",
            "This phase does not authorize deletion.",
            "no files deleted",
            "no files moved",
            "no code migrated",
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
            "daily data hygiene scheduler remains operational",
            "agent is advisory only",
            "risk preset controls sizing",
            "scenario mode controls missing-data handling",
            "math / core calculation",
            "metrics / performance",
            "signals / features",
            "risk",
            "providers / data adapter",
            "backtest",
            "storage / ledger / archive",
            "API route",
            "dashboard data",
            "orchestration / scheduler",
            "Proceed to 10K8ZFG Safe Migration Batch 1",
        ],
        "report",
    )

    for domain in [
        "Math / Core Calculation Decision",
        "Metrics / Performance Decision",
        "Signals / Features Decision",
        "Risk Decision",
        "Providers / Data Adapter Decision",
        "Backtest Decision",
        "Storage / Ledger / Archive Decision",
        "API Route Decision",
        "Dashboard Data Decision",
        "Orchestration / Scheduler Decision",
    ]:
        assert domain in report

    assert "This phase does not authorize deletion." in report
    assert "no files deleted" in report
    assert "no files moved" in report
    assert "no code migrated" in report
    assert "canonical owner" in report
    assert "canonical future owner" in report
    assert "migration direction" in report
    assert "must_not_delete_yet" in report
    assert "future deprecation candidate" in report
    assert "daily data hygiene scheduler remains operational" in report
    assert "agent is advisory only" in report
    assert "risk preset controls sizing" in report
    assert "scenario mode controls missing-data handling" in report

    assert re.search(r"AKIA[0-9A-Z]{16}", report) is None
    assert re.search(r"ASIA[0-9A-Z]{16}", report) is None
    assert "your_real_secret" not in report

    assert_contains_all(
        readme,
        [
            "10K8ZF7 R2 Archive Pipeline",
            "cleanup mode is explicit and gated",
        ],
        "README",
    )
    assert re.search(r"AKIA[0-9A-Z]{16}", readme) is None
    assert re.search(r"ASIA[0-9A-Z]{16}", readme) is None
    assert "your_real_secret" not in readme

    for text in source_texts:
        assert re.search(r"AKIA[0-9A-Z]{16}", text) is None
        assert re.search(r"ASIA[0-9A-Z]{16}", text) is None
        assert "your_real_secret" not in text

    assert not any(ROOT.glob("pages/*.py"))
    assert not any(ROOT.glob("app/pages/*.py"))
    assert not any(ROOT.glob("frontend/*.py"))
    assert not any(ROOT.glob("frontend/pages/*.py"))




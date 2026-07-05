from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8ZFE_DUPLICATE_CODE_EVIDENCE_SCAN.md"
README = ROOT / "README.md"
SOURCE_FILES = [
    ROOT / "main.py",
    ROOT / "streamlit_app.py",
    ROOT / "src" / "services" / "streamlit_dashboard_data.py",
    ROOT / "src" / "core" / "math_utils.py",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains_all(text: str, items: list[str], label: str) -> None:
    for item in items:
        assert item in text, f"Missing {label} string: {item}"


def test_phase10k8zfe_duplicate_code_evidence_scan_report() -> None:
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
        "Relationship to 10K8ZF9D",
        "Repo Inventory",
        "Method",
        "Duplicate-Risk Summary",
        "Math / Core Calculation Evidence",
        "Metrics / Performance Evidence",
        "Signals / Features Evidence",
        "Risk Evidence",
        "Providers / Data Adapter Evidence",
        "Backtest Evidence",
        "Storage / Ledger / Archive Evidence",
        "API Route Evidence",
        "Dashboard Data Evidence",
        "Orchestration / Scheduler Evidence",
        "Must-Not-Delete-Yet List",
        "Likely Canonical Owner Candidates",
        "High-Risk Duplicate Groups",
        "Medium-Risk Duplicate Groups",
        "Low-Risk Duplicate Groups",
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
            "10K8ZFE",
            "Duplicate Code / Math / Metrics / Signal Evidence Scan",
            "evidence-only phase",
            "no files deleted",
            "no files moved",
            "no code migrated",
            "no AI optimizer implementation",
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
            "data raw JSON/JSONL/CSV cleanup remained complete",
            "duplicate-risk",
            "canonical future owner",
            "must_not_delete_yet",
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
            "Proceed to 10K8ZFF Canonical Owner Decision Report",
            "This phase does not authorize deletion.",
        ],
        "report",
    )

    assert_contains_all(
        report,
        [
            "JSON: 57",
            "JSONL: 0",
            "CSV: 0",
            "Markdown: 38",
            "DB: 2",
        ],
        "inventory",
    )

    assert re.search(r"AKIA[0-9A-Z]{16}", report) is None
    assert re.search(r"ASIA[0-9A-Z]{16}", report) is None
    assert "your_real_secret" not in report

    assert_contains_all(
        readme,
        [
            "10K8ZF7 R2 Archive Pipeline",
            "cleanup mode is explicit and gated",
            "verified local raw/generated files are deleted only when --cleanup and --allow-delete-local-raw are explicitly passed",
        ],
        "README",
    )

    for text in source_texts:
        assert re.search(r"AKIA[0-9A-Z]{16}", text) is None
        assert re.search(r"ASIA[0-9A-Z]{16}", text) is None
        assert "your_real_secret" not in text

    assert not any(ROOT.glob("pages/*.py"))
    assert not any(ROOT.glob("app/pages/*.py"))
    assert not any(ROOT.glob("frontend/*.py"))
    assert not any(ROOT.glob("frontend/pages/*.py"))



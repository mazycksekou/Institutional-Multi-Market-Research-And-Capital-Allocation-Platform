from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8ZFK_TEST_SUITE_CLEANUP_PLAN.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _assert_contains_all(text: str, required: list[str]) -> None:
    missing = [item for item in required if item not in text]
    assert not missing, f"Missing required strings: {missing}"


def test_test_suite_cleanup_plan_report_is_complete() -> None:
    assert REPORT.exists(), "Expected test-suite cleanup plan report to exist"
    text = _read(REPORT)

    required_sections = [
        "Executive Summary",
        "Current HEAD",
        "Purpose",
        "Scope",
        "Non-Goals",
        "Relationship to 10K8ZFF",
        "Relationship to 10K8ZFI",
        "Relationship to 10K8ZFJ",
        "Test Inventory",
        "Test Classification Method",
        "Phase-Report Tests",
        "Storage / R2 / Archive Tests",
        "Streamlit / Dashboard-Data Tests",
        "API Route Tests",
        "Provider Tests",
        "automation_scheduler Tests",
        "Model / Backtest Tests",
        "Risk / Metrics / Math Tests",
        "Smoke / Test Wrapper Coverage",
        "Stale / Duplicate / Manual-Review Tests",
        "Critical Gates To Preserve",
        "Cleanup Waves",
        "No-Network Test Policy",
        "Must-Not-Delete-Yet Test List",
        "Unsafe Actions",
        "Acceptance Results",
        "Next Phase Recommendation",
    ]
    _assert_contains_all(text, required_sections)

    required_strings = [
        "10K8ZFK",
        "Test Suite Cleanup Plan",
        "planning/report phase only",
        "no tests deleted",
        "no tests moved",
        "no tests rewritten",
        "no coverage removed",
        "no xfail or skip added to hide failures",
        "behavior unchanged",
        "current gates preserved",
        "phase-report tests",
        "storage / R2 / archive tests",
        "Streamlit / dashboard-data tests",
        "API route tests",
        "provider tests",
        "automation_scheduler tests",
        "model / backtest tests",
        "risk / metrics / math tests",
        "smoke / test wrapper coverage",
        "stale / duplicate / manual-review tests",
        "no-network test policy",
        "fake clients only",
        "no external API calls",
        "no live connectors",
        "no credentials committed",
        "no secrets printed",
        "daily data hygiene scheduler remains operational",
        "dry-run by default",
        "agent is advisory only",
        "agent does not directly delete files",
        "no AI integration",
        "no ML training",
        "no backtest runner",
        "no controlled data loader",
        "no broker execution",
        "no real trade execution",
        "no scraper actions",
        "This phase does not authorize deletion.",
        "Proceed to 10K8ZFL Pre-AI Integration Repo Freeze",
    ]
    _assert_contains_all(text, required_strings)

    inventory_strings = [
        "total test files: 353",
        "total test functions: 693",
        "phase-report tests: 73",
        "storage / R2 / archive tests: 6",
        "Streamlit / dashboard-data tests: 5",
        "API route tests: 5",
        "provider tests: 23",
        "automation_scheduler tests: 7",
        "model / backtest tests: 67",
        "risk / metrics / math tests: 18",
        "smoke / test wrapper coverage: 4",
        "tests importing streamlit: 2",
        "tests importing pandas: 5",
        "tests importing pyarrow: 0",
        "tests that may use network primitives: 17",
        "tests referencing `.env` or credential-like names: 46",
        "Top 20 Largest Test Files",
    ]
    _assert_contains_all(text, inventory_strings)

    for wave in range(9):
        assert f"Test Wave {wave}" in text

    assert "This phase does not authorize deletion." in text
    assert "no tests deleted" in text
    assert "no tests moved" in text
    assert "no tests rewritten" in text
    assert "no coverage removed" in text
    assert "behavior unchanged" in text


def test_test_suite_cleanup_plan_has_no_obvious_secrets_or_frontend_pages() -> None:
    secret_patterns = [
        re.compile(r"AKIA[0-9A-Z]{16}"),
        re.compile(r"ASIA[0-9A-Z]{16}"),
        re.compile(r"your_real_secret"),
    ]

    text_sources: list[Path] = []
    text_sources.extend(path for path in ROOT.glob("README*") if path.is_file())
    text_sources.extend(path for path in ROOT.glob("PHASE*.md") if path.is_file())
    text_sources.extend(
        path
        for path in [
            ROOT / "main.py",
            ROOT / "streamlit_app.py",
            ROOT / "screenshot_intake.py",
            ROOT / "src" / "api" / "provider_status_routes.py",
            ROOT / "src" / "services" / "enrichment_service.py",
            ROOT / "src" / "automation_scheduler_legacy" / "streamlit_dashboard_data.py",
            ROOT / "betting_providers" / "provider_router.py",
            ROOT / "providers" / "odds_provider_router.py",
        ]
        if path.exists()
    )

    for path in text_sources:
        text = _read(path)
        for pattern in secret_patterns:
            assert pattern.search(text) is None, f"Found suspicious secret-like text in {path}"

    frontend_patterns = [
        "pages/*.py",
        "app/pages/*.py",
        "frontend/*.py",
        "frontend/pages/*.py",
    ]
    for pattern in frontend_patterns:
        assert not list(ROOT.glob(pattern)), f"Unexpected frontend page files matched {pattern}"

from __future__ import annotations

from pathlib import Path


REPORT_PATH = Path("PHASE10K7B_TEST_GUARDRAIL_STABILIZATION.md")
PHASE10K6K_TEST_PATH = Path("tests/test_phase10k6k_controlled_dashboard_shell_review.py")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k7b_report_exists_and_contains_required_strings() -> None:
    assert REPORT_PATH.exists(), "10K7B report is missing"

    report = read_text(REPORT_PATH)

    required_strings = [
        "Test Guardrail Stabilization",
        "brittle git-status assertion",
        "global untracked files",
        "source-text guardrail",
        "no subprocess git checks",
        "no temporary git shim",
        "no separate frontend page files",
        "pages/*.py",
        "app/pages/*.py",
        "frontend/*.py",
        "frontend/pages/*.py",
        "connector guardrails remain active",
        "no prediction testing",
        "no live connectors",
        "no API calls",
        "no database writes",
        "implementation reviewed in 10K7B",
    ]

    for item in required_strings:
        assert item in report, f"Missing required report string: {item}"


def test_phase10k6k_guardrail_test_no_longer_uses_git_status_checks() -> None:
    text = read_text(PHASE10K6K_TEST_PATH)

    forbidden_strings = [
        "subprocess",
        "git ls-files",
        "git status",
        "git shim",
    ]

    for item in forbidden_strings:
        assert item not in text, f"Forbidden string still present: {item}"


def test_phase10k6k_guardrail_test_keeps_required_shell_and_boundary_strings() -> None:
    text = read_text(PHASE10K6K_TEST_PATH)

    required_strings = [
        "Controlled Dashboard Shell Review",
        "streamlit_app.py",
        "automation_scheduler/streamlit_dashboard_data.py",
        "Controlled Navigation Shell",
        "readiness display preview",
        "build_readiness_display_payload",
        "build_readiness_display_rows",
        "READINESS_DISPLAY_FIELDS",
        "build_readiness_display_contract",
        "Connect Real Vendor API",
        "Run Real Line Movement Scraper",
        "Connect Synthetic Vendor API",
        "Run Synthetic Scraper",
        "pages",
        "app/pages",
        "frontend",
        "frontend/pages",
    ]

    for item in required_strings:
        assert item in text, f"Missing required guardrail string: {item}"


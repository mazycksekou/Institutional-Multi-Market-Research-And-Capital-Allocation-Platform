from __future__ import annotations

import re
from pathlib import Path

from automation_scheduler.streamlit_dashboard_data import (
    build_zero_dte_validation_readiness_payload,
    build_zero_dte_validation_readiness_rows,
)
from automation_scheduler.zero_dte_fixture_template import (
    build_zero_dte_fixture_template_row,
    validate_zero_dte_fixture_rows,
)


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8R_DEDICATED_0DTE_VALIDATION_READINESS_UI.md"
STREAMLIT_APP = ROOT / "streamlit_app.py"
LEGACY_PHASE_TEST = ROOT / "tests" / "test_phase10k6k_controlled_dashboard_shell_review.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k8r_dedicated_0dte_validation_readiness_ui() -> None:
    assert REPORT.is_file(), "Expected the 10K8R review report to exist."
    assert STREAMLIT_APP.is_file(), "Expected streamlit_app.py to exist."
    assert LEGACY_PHASE_TEST.is_file(), "Expected the prior dashboard shell review test to remain."

    report_text = read_text(REPORT)
    streamlit_text = read_text(STREAMLIT_APP)

    row = build_zero_dte_fixture_template_row()
    validation_result = validate_zero_dte_fixture_rows([row])
    payload = build_zero_dte_validation_readiness_payload(validation_result)
    readiness_rows = build_zero_dte_validation_readiness_rows(payload)

    assert payload["rows_tested"] == 1
    assert payload["rows_valid"] >= 0
    assert isinstance(readiness_rows, list)
    assert readiness_rows
    assert all(set(item.keys()) == {"label", "value", "status", "detail"} for item in readiness_rows)

    required_row_labels = {
        "rows_tested",
        "rows_valid",
        "rows_invalid",
        "rows_warning",
        "backend_gate",
        "threshold_mode",
        "quality_label",
    }
    assert required_row_labels.issubset({item["label"] for item in readiness_rows})

    required_report_strings = [
        "Dedicated 0DTE Validation Readiness UI",
        "streamlit_app.py",
        "automation_scheduler/zero_dte_fixture_template.py",
        "automation_scheduler/streamlit_dashboard_data.py",
        "show_zero_dte_validation_readiness_preview",
        "local fixture-backed testing",
        "paper-only",
        "readiness only",
        "no live connectors",
        "no API calls",
        "no database writes",
        "no broker execution",
        "no real trade execution",
        "implementation reviewed in 10K8R",
    ]
    for needle in required_report_strings:
        assert needle in report_text, f"Missing report string: {needle}"

    required_streamlit_strings = [
        "Dedicated 0DTE validation readiness UI",
        "show_zero_dte_validation_readiness_preview",
        "build_zero_dte_fixture_template_row",
        "validate_zero_dte_fixture_rows",
        "build_zero_dte_validation_readiness_payload",
        "build_zero_dte_validation_readiness_rows",
        "rows_tested",
        "rows_valid",
        "rows_invalid",
        "rows_warning",
        "backend_gate",
        "threshold_mode",
        "quality_label",
        "validity_check_only",
        "user_threshold_review_only",
        "not_automatically_labeled",
        "local fixture-backed testing",
        "paper-only",
        "readiness only",
        "no broker execution",
        "no real trade execution",
        "no live connectors",
        "no API calls",
        "no database writes",
        "One 0DTE Options Trade",
        "0DTE is the primary active trading lane",
    ]
    for needle in required_streamlit_strings:
        assert needle in streamlit_text, f"Missing streamlit_app.py string: {needle}"

    call_site = "\n            show_zero_dte_validation_readiness_preview()"
    assert streamlit_text.count(call_site) == 1
    branch_index = streamlit_text.index('elif mode == "One 0DTE Options Trade":')
    call_index = streamlit_text.index(call_site)
    assert branch_index < call_index

    assert "st.file_uploader" not in streamlit_text
    assert "pd.read_csv" not in streamlit_text
    assert "pandas.read_csv" not in streamlit_text

    forbidden_streamlit_strings = [
        "Connect Real Vendor API",
        "Run Real Line Movement Scraper",
        "Connect Synthetic Vendor API",
        "Run Synthetic Scraper",
        "Execute Real Trade",
        "Send Broker Order",
        "Place Live Order",
    ]
    for needle in forbidden_streamlit_strings:
        assert needle not in streamlit_text, f"Forbidden string unexpectedly present: {needle}"

    page_candidates = [
        *Path(".").glob("pages/*.py"),
        *Path(".").glob("app/pages/*.py"),
        *Path(".").glob("frontend/*.py"),
        *Path(".").glob("frontend/pages/*.py"),
    ]
    assert not page_candidates, f"Unexpected separate frontend page files found: {page_candidates}"

    legacy_text = read_text(LEGACY_PHASE_TEST)
    for needle in ["subprocess", "git ls-files", "git status", "git shim"]:
        assert needle not in legacy_text

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_HELPER = ROOT / "automation_scheduler" / "streamlit_dashboard_data.py"
REPORT = ROOT / "PHASE10K6F_READINESS_DISPLAY_PAYLOAD_BUILDER.md"
STREAMLIT_APP = ROOT / "streamlit_app.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k6f_report_exists_and_contains_required_strings() -> None:
    text = read_text(REPORT)

    required_strings = [
        "Readiness Display Payload Builder",
        "automation_scheduler/streamlit_dashboard_data.py",
        "build_readiness_display_payload",
        "READINESS_DISPLAY_FIELDS",
        "build_readiness_display_contract",
        "threshold_review_only",
        "validity_is_backend_gate",
        "low_sample_size_does_not_hide_valid_results",
        "quality_not_automatically_labeled",
        "low backend gate",
        "validity check only",
        "user threshold review-only",
        "row counts",
        "rows tested",
        "rows valid",
        "rows invalid",
        "missing field reasons",
        "warning reasons",
        "do not label quality automatically",
        "do not hide valid results because sample size is low",
        "no prediction testing",
        "no live connectors",
        "no frontend pages added",
        "streamlit_app.py unchanged",
        "implementation deferred beyond 10K6F",
    ]

    for needle in required_strings:
        assert needle in text


def test_readiness_display_payload_builder_is_present_in_dashboard_data_module() -> None:
    text = read_text(DATA_HELPER)

    required_fields = [
        "market_name",
        "data_source_name",
        "validation_status",
        "row_counts",
        "rows_tested",
        "rows_valid",
        "rows_invalid",
        "missing_field_reasons",
        "warning_reasons",
        "user_threshold_value",
        "user_threshold_met",
        "threshold_review_only",
        "validity_is_backend_gate",
        "low_sample_size_does_not_hide_valid_results",
        "quality_not_automatically_labeled",
    ]

    required_strings = [
        "build_readiness_display_payload",
        "READINESS_DISPLAY_FIELDS",
        "build_readiness_display_contract",
        "threshold_review_only",
        "validity_is_backend_gate",
        "low_sample_size_does_not_hide_valid_results",
        "quality_not_automatically_labeled",
        '"threshold_review_only": True',
        '"validity_is_backend_gate": True',
        '"low_sample_size_does_not_hide_valid_results": True',
        '"quality_not_automatically_labeled": True',
    ]

    for needle in required_fields:
        assert needle in text

    for needle in required_strings:
        assert needle in text


def test_streamlit_app_main_menu_strings_are_preserved_and_forbidden_strings_absent() -> None:
    text = read_text(STREAMLIT_APP)

    for needle in ["Feature Ablation Lab", "Bankroll Settings", "Instructions"]:
        assert needle in text

    forbidden = [
        "Connect Real Vendor API",
        "Run Real Line Movement Scraper",
        "Connect Synthetic Vendor API",
        "Run Synthetic Scraper",
    ]

    for needle in forbidden:
        assert needle not in text

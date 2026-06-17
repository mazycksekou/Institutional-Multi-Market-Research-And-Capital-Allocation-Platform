from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_HELPER = ROOT / "automation_scheduler" / "streamlit_dashboard_data.py"
REPORT = ROOT / "PHASE10K6G_READINESS_DISPLAY_RENDERER_CONTRACT.md"
STREAMLIT_APP = ROOT / "streamlit_app.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k6g_report_exists_and_contains_required_strings() -> None:
    text = read_text(REPORT)

    required_strings = [
        "Readiness Display Renderer Contract",
        "automation_scheduler/streamlit_dashboard_data.py",
        "READINESS_DISPLAY_FIELDS",
        "build_readiness_display_contract",
        "build_readiness_display_payload",
        "future renderer only",
        "implementation deferred beyond 10K6G",
        "low backend gate",
        "validity check only",
        "user threshold review-only",
        "row counts",
        "rows tested",
        "rows valid",
        "rows invalid",
        "missing field reasons",
        "warning reasons",
        "threshold_review_only",
        "validity_is_backend_gate",
        "low_sample_size_does_not_hide_valid_results",
        "quality_not_automatically_labeled",
        "do not label quality automatically",
        "do not hide valid results because sample size is low",
        "Sports",
        "0DTE Options",
        "Prediction Markets",
        "Data Warehouse",
        "Backtest Lab",
        "Model Diagnostics",
        "Arbitrage Lab",
        "no prediction testing",
        "no live connectors",
        "no frontend pages added",
        "streamlit_app.py unchanged",
    ]

    for needle in required_strings:
        assert needle in text


def test_renderer_contract_references_existing_payload_helpers_in_dashboard_data_module() -> None:
    text = read_text(DATA_HELPER)

    required_strings = [
        "READINESS_DISPLAY_FIELDS",
        "build_readiness_display_contract",
        "build_readiness_display_payload",
    ]

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

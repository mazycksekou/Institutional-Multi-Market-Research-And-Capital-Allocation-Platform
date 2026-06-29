from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_phase10k6h_report_and_helper_text_guards():
    report = read_text("PHASE10K6H_READINESS_DISPLAY_RENDERER_HELPER.md")
    helper = read_text('src/automation_scheduler_legacy/streamlit_dashboard_data.py')
    streamlit_app = read_text("streamlit_app.py")

    required_report_strings = [
        "Readiness Display Renderer Helper",
        "automation_scheduler/streamlit_dashboard_data.py",
        "build_readiness_display_rows",
        "build_readiness_display_payload",
        "READINESS_DISPLAY_FIELDS",
        "build_readiness_display_contract",
        "label",
        "value",
        "policy_note",
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
        "implementation deferred beyond 10K6H",
    ]
    for text in required_report_strings:
        assert text in report

    required_helper_strings = [
        "build_readiness_display_rows",
        "build_readiness_display_payload",
        "READINESS_DISPLAY_FIELDS",
        "build_readiness_display_contract",
        "label",
        "value",
        "policy_note",
        "user threshold review-only",
        "validity check only",
        "do not hide valid results because sample size is low",
        "do not label quality automatically",
    ]
    for text in required_helper_strings:
        assert text in helper

    assert "Feature Ablation Lab" in streamlit_app
    assert "Bankroll Settings" in streamlit_app
    assert "Instructions" in streamlit_app

    forbidden_strings = [
        "Connect Real Vendor API",
        "Run Real Line Movement Scraper",
        "Connect Synthetic Vendor API",
        "Run Synthetic Scraper",
    ]
    for text in forbidden_strings:
        assert text not in streamlit_app


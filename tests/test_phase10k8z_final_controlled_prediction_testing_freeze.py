from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = [
    ROOT / "PHASE10K8M_STRICT_MODEL_FIELD_BASELINE_BY_MARKET_AND_SPORT.md",
    ROOT / "PHASE10K8N_CONTROLLED_FIELD_CATALOG_UI_REVIEW.md",
    ROOT / "PHASE10K8O_DEDICATED_0DTE_PAPER_FIXTURE_TEMPLATE.md",
    ROOT / "PHASE10K8P_DEDICATED_0DTE_FIXTURE_VALIDATION_ADAPTER.md",
    ROOT / "PHASE10K8Q_DEDICATED_0DTE_VALIDATION_READINESS_PAYLOAD.md",
    ROOT / "PHASE10K8R_DEDICATED_0DTE_VALIDATION_READINESS_UI.md",
    ROOT / "PHASE10K8S_DEDICATED_0DTE_PAPER_EVALUATION_ADAPTER.md",
    ROOT / "PHASE10K8T_DEDICATED_0DTE_EVALUATION_READINESS_PAYLOAD.md",
    ROOT / "PHASE10K8U_DEDICATED_0DTE_EVALUATION_UI.md",
    ROOT / "PHASE10K8V_FULL_0DTE_PAPER_PIPELINE_ADAPTER.md",
    ROOT / "PHASE10K8W_FULL_0DTE_PAPER_PIPELINE_UI.md",
    ROOT / "PHASE10K8X_CONTROLLED_0DTE_PAPER_RUN_SMOKE_REVIEW.md",
    ROOT / "PHASE10K8Y_0DTE_PREDICTION_TESTING_READINESS_REVIEW.md",
    ROOT / "PHASE10K8Z_FINAL_CONTROLLED_PREDICTION_TESTING_FREEZE.md",
]
APP = ROOT / "streamlit_app.py"
LEGACY_PHASE_TEST = ROOT / "tests" / "test_phase10k6k_controlled_dashboard_shell_review.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k8z_final_controlled_prediction_testing_freeze() -> None:
    for report in REPORTS:
        assert report.is_file(), f"Expected report to exist: {report.name}"

    app_text = read_text(APP)
    legacy_test_text = read_text(LEGACY_PHASE_TEST)
    freeze_report_text = read_text(REPORTS[-1])

    assert "controlled prediction testing ready" in freeze_report_text
    assert "not ready for live trading" in freeze_report_text
    assert "cleanup begins next" in freeze_report_text
    assert "implementation reviewed in 10K8Z" in freeze_report_text

    forbidden_connector_strings = [
        "Connect Real Vendor API",
        "Run Real Line Movement Scraper",
        "Connect Synthetic Vendor API",
        "Run Synthetic Scraper",
        "Execute Real Trade",
        "Send Broker Order",
        "Place Live Order",
        "guaranteed profit",
        "assured profit",
    ]
    for needle in forbidden_connector_strings:
        assert needle not in app_text

    assert "temporary git shim" not in legacy_test_text
    assert "subprocess" not in legacy_test_text
    assert "git ls-files" not in legacy_test_text
    assert "git status" not in legacy_test_text

    assert not any(ROOT.glob("pages/*.py")), "Unexpected frontend page files were added."

from __future__ import annotations

from pathlib import Path
import re

from src.automation_scheduler_legacy.streamlit_dashboard_data import build_zero_dte_evaluation_readiness_payload, build_zero_dte_evaluation_readiness_rows
from src.services.streamlit_dashboard_facade import TECHNICAL_SIGNAL_FIELDS, TECHNICAL_SIGNAL_FIELDS_BY_MARKET
from src.automation_scheduler_legacy.zero_dte_fixture_template import build_zero_dte_fixture_template_row, evaluate_zero_dte_paper_fixture_rows


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8U_DEDICATED_0DTE_EVALUATION_UI.md"
APP = ROOT / "streamlit_app.py"
LEGACY_PHASE_TEST = ROOT / "tests" / "test_phase10k6k_controlled_dashboard_shell_review.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_phase10k8u_dedicated_0dte_evaluation_ui() -> None:
    assert REPORT.is_file(), "Expected the 10K8U review report to exist."
    assert APP.is_file(), "Expected streamlit_app.py to remain present."
    assert LEGACY_PHASE_TEST.is_file(), "Expected the prior dashboard shell review test to remain."

    app_text = read_text(APP)
    report_text = read_text(REPORT)

    assert "Dedicated 0DTE evaluation readiness UI" in app_text
    assert "show_zero_dte_paper_evaluation_preview" in app_text
    assert "build_zero_dte_research_backtest_evaluation_result" in app_text
    assert "build_zero_dte_evaluation_readiness_payload" in app_text
    assert "build_zero_dte_evaluation_readiness_rows" in app_text
    assert "research_backtest_edge" in app_text
    assert "research_backtest_ev" in app_text
    assert "research_backtest_stake_units" in app_text
    assert "research_backtest_result" in app_text
    assert "research_backtest_arbitrage_percentage" in app_text
    assert "total_research_backtest_ev" in app_text
    assert "total_research_backtest_stake_units" in app_text
    assert "total_research_backtest_arbitrage_percentage" in app_text
    assert "average_research_backtest_arbitrage_percentage" in app_text
    assert "research_backtest_evaluation_review_only" in app_text
    assert "local fixture-backed testing" in app_text
    assert "paper-only" in app_text
    assert "readiness only" in app_text
    assert "no broker execution" in app_text
    assert "no real trade execution" in app_text
    assert "no live connectors" in app_text
    assert "no API calls" in app_text
    assert "no database writes" in app_text
    assert "One 0DTE Options Trade" in app_text
    assert "0DTE is the primary active trading lane" in app_text

    branch_match = re.search(r"elif mode == \"One 0DTE Options Trade\":(.*?)(?:\n        elif |\n        else:)", app_text, re.S)
    assert branch_match, "Expected a dedicated One 0DTE Options Trade branch in streamlit_app.py."
    branch_text = branch_match.group(1)
    assert "show_zero_dte_paper_evaluation_preview()" in branch_text

    assert "st.file_uploader" not in app_text
    assert "pd.read_csv" not in app_text
    assert "pandas.read_csv" not in app_text

    forbidden_connector_strings = [
        "Connect Real Vendor API",
        "Run Real Line Movement Scraper",
        "Connect Synthetic Vendor API",
        "Run Synthetic Scraper",
        "Execute Real Trade",
        "Send Broker Order",
        "Place Live Order",
    ]
    for needle in forbidden_connector_strings:
        assert needle not in app_text

    template_row = build_zero_dte_fixture_template_row()
    template_row.update(
        {
            "outcome_known": False,
            "result_label": "pending",
            "model_probability": 0.0,
            "market_odds_american": 0,
            "premium": 0.0,
            "spread_percent": 0.0,
        }
    )
    evaluation_result = evaluate_zero_dte_paper_fixture_rows([template_row])
    payload = build_zero_dte_evaluation_readiness_payload(evaluation_result)
    rows = build_zero_dte_evaluation_readiness_rows(payload)

    assert evaluation_result["rows_invalid"] == 0
    assert evaluation_result["rows_evaluated"] == 1
    assert evaluation_result["paper_result_counts"].get("paper_pending", 0) >= 1
    assert payload["backend_gate"] == "paper_evaluation_review_only"
    assert payload["threshold_mode"] == "user_threshold_review_only"
    assert payload["quality_label"] == "not_automatically_labeled"
    assert rows and all(set(item.keys()) == {"label", "value", "status", "detail"} for item in rows)

    win_row = dict(template_row, outcome_known=True, result_label="win")
    loss_row = dict(template_row, outcome_known=True, result_label="loss")
    push_row = dict(template_row, outcome_known=True, result_label="push")
    observed_row = dict(template_row, outcome_known=True, result_label="unknown")
    win_eval = evaluate_zero_dte_paper_fixture_rows([win_row])["evaluation_rows"][0]["paper_result"]
    loss_eval = evaluate_zero_dte_paper_fixture_rows([loss_row])["evaluation_rows"][0]["paper_result"]
    push_eval = evaluate_zero_dte_paper_fixture_rows([push_row])["evaluation_rows"][0]["paper_result"]
    observed_eval = evaluate_zero_dte_paper_fixture_rows([observed_row])["evaluation_rows"][0]["paper_result"]
    assert win_eval == "paper_win"
    assert loss_eval == "paper_loss"
    assert push_eval == "paper_push"
    assert observed_eval == "paper_observed"

    bad_row = dict(template_row)
    bad_row.pop("fixture_id", None)
    bad_payload = build_zero_dte_evaluation_readiness_payload(
        evaluate_zero_dte_paper_fixture_rows([bad_row])
    )
    bad_rows = build_zero_dte_evaluation_readiness_rows(bad_payload)
    assert any(item["label"] == "rows_invalid" and item["status"] == "blocked" for item in bad_rows)

    assert "paper_arbitrage_percentage" not in TECHNICAL_SIGNAL_FIELDS
    prohibited_terms = {
        "ev",
        "expected_value",
        "edge",
        "arbitrage",
        "kelly",
        "fair_odds",
        "implied_probability",
        "bankroll",
        "confidence",
        "no_bet",
        "no-bet",
        "paper_arbitrage_percentage",
    }
    assert prohibited_terms.isdisjoint(set(TECHNICAL_SIGNAL_FIELDS))
    for market_fields in TECHNICAL_SIGNAL_FIELDS_BY_MARKET.values():
        assert prohibited_terms.isdisjoint(set(market_fields))

    required_report_strings = [
        "Dedicated 0DTE Evaluation UI",
        "streamlit_app.py",
        "automation_scheduler/zero_dte_fixture_template.py",
        "automation_scheduler/streamlit_dashboard_data.py",
        "quant_engine.py",
        "paper_evaluation_review_only",
        "local fixture-backed testing",
        "paper-only",
        "readiness only",
        "review-only evaluation",
        "no live connectors",
        "no API calls",
        "no database writes",
        "no broker execution",
        "no real trade execution",
        "implementation reviewed in 10K8U",
    ]
    for needle in required_report_strings:
        assert needle in report_text, f"Missing report string: {needle}"

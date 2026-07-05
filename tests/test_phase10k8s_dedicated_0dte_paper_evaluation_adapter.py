from __future__ import annotations

from pathlib import Path

from src.services.streamlit_dashboard_facade import TECHNICAL_SIGNAL_FIELDS, TECHNICAL_SIGNAL_FIELDS_BY_MARKET
from src.data.zero_dte_fixture_template import build_zero_dte_fixture_template_row, evaluate_zero_dte_paper_fixture_rows


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8S_DEDICATED_0DTE_PAPER_EVALUATION_ADAPTER.md"
LEGACY_PHASE_TEST = ROOT / "tests" / "test_phase10k6k_controlled_dashboard_shell_review.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def flatten_market_fields() -> set[str]:
    flattened: set[str] = set()
    for market_spec in TECHNICAL_SIGNAL_FIELDS_BY_MARKET.values():
        flattened.update(market_spec.get("required", []))
        flattened.update(market_spec.get("optional", []))
    return flattened


def test_phase10k8s_dedicated_0dte_paper_evaluation_adapter() -> None:
    assert REPORT.is_file(), "Expected the 10K8S review report to exist."
    assert LEGACY_PHASE_TEST.is_file(), "Expected the prior dashboard shell review test to remain."

    report_text = read_text(REPORT)

    template_row = build_zero_dte_fixture_template_row()
    pending_result = evaluate_zero_dte_paper_fixture_rows([template_row])
    assert pending_result["rows_tested"] == 1
    assert pending_result["rows_evaluated"] == 1
    assert pending_result["rows_invalid"] == 0
    assert pending_result["rows_pending"] == 1
    assert pending_result["review_only"] is True
    assert pending_result["paper_only"] is True
    assert pending_result["user_threshold_review_only"] is True
    assert pending_result["quality_not_automatically_labeled"] is True
    assert pending_result["low_sample_size_does_not_hide_valid_results"] is True
    assert pending_result["prediction_testing_started"] is False
    assert pending_result["live_connectors_enabled"] is False
    assert pending_result["api_calls_enabled"] is False
    assert pending_result["database_writes_enabled"] is False
    assert pending_result["broker_execution_enabled"] is False
    assert pending_result["real_trade_execution_enabled"] is False
    assert pending_result["total_paper_ev"] == 0.0
    assert pending_result["total_paper_stake_units"] == 0.0
    assert "paper_pending" in pending_result["paper_result_counts"]
    evaluation_row = pending_result["evaluation_rows"][0]
    for key in [
        "row_index",
        "validation_status",
        "selection",
        "underlying_symbol",
        "strike",
        "call_put",
        "expiration_date",
        "result_label",
        "outcome_known",
        "model_probability",
        "market_odds_american",
        "premium",
        "spread_percent",
        "paper_result",
        "paper_edge",
        "paper_ev",
        "paper_stake_units",
        "paper_arbitrage_percentage",
    ]:
        assert key in evaluation_row
    assert evaluation_row["paper_result"] == "paper_pending"

    win_row = build_zero_dte_fixture_template_row().copy()
    win_row["outcome_known"] = True
    win_row["result_label"] = "won"
    loss_row = build_zero_dte_fixture_template_row().copy()
    loss_row["outcome_known"] = True
    loss_row["result_label"] = "lost"
    push_row = build_zero_dte_fixture_template_row().copy()
    push_row["outcome_known"] = True
    push_row["result_label"] = "tie"
    mapped_result = evaluate_zero_dte_paper_fixture_rows([win_row, loss_row, push_row])
    mapped_results = [item["paper_result"] for item in mapped_result["evaluation_rows"]]
    assert mapped_results == ["paper_win", "paper_loss", "paper_push"]
    assert mapped_result["rows_invalid"] == 0
    assert mapped_result["rows_pending"] == 0
    assert set(mapped_result["paper_result_counts"].keys()) == {"paper_win", "paper_loss", "paper_push"}

    invalid_row = build_zero_dte_fixture_template_row().copy()
    invalid_row.pop("fixture_id", None)
    mixed_result = evaluate_zero_dte_paper_fixture_rows([build_zero_dte_fixture_template_row(), invalid_row])
    assert mixed_result["rows_invalid"] == 1
    assert mixed_result["validation_result"]["rows_invalid"] == 1
    assert len(mixed_result["evaluation_rows"]) == 2
    assert any(item["validation_status"] == "invalid" for item in mixed_result["evaluation_rows"])

    assert "paper_arbitrage_percentage" not in TECHNICAL_SIGNAL_FIELDS
    required_signal_fields = {
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
    assert not required_signal_fields.intersection(TECHNICAL_SIGNAL_FIELDS)
    assert not required_signal_fields.intersection(flatten_market_fields())

    required_report_strings = [
        "Dedicated 0DTE Paper Evaluation Adapter",
        "automation_scheduler/zero_dte_fixture_template.py",
        "evaluate_zero_dte_paper_fixture_rows",
        "paper_arbitrage_percentage",
        "review-only evaluation",
        "no broker execution",
        "no real trade execution",
        "implementation reviewed in 10K8S",
    ]
    for needle in required_report_strings:
        assert needle in report_text, f"Missing report string: {needle}"

    forbidden_strings = [
        "Connect Real Vendor API",
        "Run Real Line Movement Scraper",
        "Connect Synthetic Vendor API",
        "Run Synthetic Scraper",
        "Execute Real Trade",
        "Send Broker Order",
        "Place Live Order",
    ]
    for needle in forbidden_strings:
        assert needle not in report_text


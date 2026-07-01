from __future__ import annotations

from pathlib import Path

from src.data.model_data_field_catalog import CORE_BACKTEST_VALIDATION_METRICS, PREDICTION_MARKET_OUTPUT_METRICS, SPORTS_BETTING_OUTPUT_METRICS, ZERO_DTE_OUTPUT_METRICS, output_metrics_for_product_lane
from src.services.streamlit_dashboard_data import build_market_metric_display_payload
from src.services.streamlit_dashboard_facade import TECHNICAL_SIGNAL_FIELDS, TECHNICAL_SIGNAL_FIELDS_BY_MARKET


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8ZE_INSTITUTIONAL_MARKET_METRIC_CATALOG.md"
APP = ROOT / "streamlit_app.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def assert_contains_all(text: str, needles: list[str]) -> None:
    for needle in needles:
        assert needle in text, f"Missing string: {needle}"


def test_phase10k8ze_institutional_market_metric_catalog() -> None:
    assert REPORT.is_file(), "Expected the 10K8ZE report to exist."
    assert APP.is_file(), "Expected streamlit_app.py to remain present."

    report_text = read_text(REPORT)
    app_text = read_text(APP)

    assert_contains_all(
        report_text,
        [
            "Institutional Market Metric Catalog",
            "SPORTS_BETTING_OUTPUT_METRICS",
            "ZERO_DTE_OUTPUT_METRICS",
            "PREDICTION_MARKET_OUTPUT_METRICS",
            "CORE_BACKTEST_VALIDATION_METRICS",
            "output_metrics_for_product_lane",
            "build_market_metric_display_payload",
            "Sports",
            "Stocks / 0DTE",
            "Predictions",
            "Expected Value / EV",
            "CLV",
            "arbitrage",
            "Kelly Growth Rate",
            "Risk of Ruin",
            "Brier Score",
            "Log Loss",
            "Execution Cost Ratio",
            "Fill Probability",
            "Adverse Selection Rate",
            "Variance Risk Premium",
            "Deflated Sharpe Ratio",
            "Probability of Backtest Overfitting",
            "Walk-Forward Stability",
            "Capacity Analysis",
            "Cost Sensitivity Analysis",
            "do not label quality automatically",
            "do not hide valid results because sample size is low",
            "implementation reviewed in 10K8ZE",
        ],
    )

    sports_metrics = output_metrics_for_product_lane("Sports")
    zero_dte_metrics = output_metrics_for_product_lane("Stocks / 0DTE")
    prediction_metrics = output_metrics_for_product_lane("Predictions")

    assert set(SPORTS_BETTING_OUTPUT_METRICS).issubset(set(sports_metrics["market_output_metrics"]))
    assert set(ZERO_DTE_OUTPUT_METRICS).issubset(set(zero_dte_metrics["market_output_metrics"]))
    assert set(PREDICTION_MARKET_OUTPUT_METRICS).issubset(set(prediction_metrics["market_output_metrics"]))
    assert set(CORE_BACKTEST_VALIDATION_METRICS).issubset(set(sports_metrics["core_backtest_validation_metrics"]))
    assert set(CORE_BACKTEST_VALIDATION_METRICS).issubset(set(zero_dte_metrics["core_backtest_validation_metrics"]))
    assert set(CORE_BACKTEST_VALIDATION_METRICS).issubset(set(prediction_metrics["core_backtest_validation_metrics"]))

    sports_payload = build_market_metric_display_payload("Sports")
    zero_dte_payload = build_market_metric_display_payload("Stocks / 0DTE")
    prediction_payload = build_market_metric_display_payload("Predictions")

    for payload, lane in [
        (sports_payload, "Sports"),
        (zero_dte_payload, "Stocks / 0DTE"),
        (prediction_payload, "Predictions"),
    ]:
        assert payload["product_lane"] == lane
        assert payload["paper_only"] is True
        assert payload["readiness_only"] is True
        assert payload["review_only"] is True
        assert payload["live_connectors_enabled"] is False
        assert payload["api_calls_enabled"] is False
        assert payload["database_writes_enabled"] is False
        assert payload["broker_execution_enabled"] is False
        assert payload["real_trade_execution_enabled"] is False
        assert payload["quality_not_automatically_labeled"] is True
        assert payload["low_sample_size_does_not_hide_valid_results"] is True
        assert set(payload["core_backtest_validation_metrics"]).issubset(set(CORE_BACKTEST_VALIDATION_METRICS))
        assert "market_output_metrics" in payload["metric_groups"]
        assert "core_backtest_validation_metrics" in payload["metric_groups"]
        assert "all_output_metrics" in payload["metric_groups"]

    assert "PRODUCT_MARKET_LANES" in app_text
    assert "Sports metric groups" in app_text
    assert "Stocks / 0DTE metric groups" in app_text
    assert "Predictions metric groups" in app_text
    assert "Core backtest validation metrics" in app_text
    assert "Expected Value / EV" in app_text
    assert "CLV" in app_text
    assert "arbitrage" in app_text
    assert "Kelly Growth Rate" in app_text
    assert "Risk of Ruin" in app_text
    assert "Brier Score" in app_text
    assert "Log Loss" in app_text
    assert "Execution Cost Ratio" in app_text
    assert "Fill Probability" in app_text
    assert "Adverse Selection Rate" in app_text
    assert "Variance Risk Premium" in app_text
    assert "Deflated Sharpe Ratio" in app_text
    assert "Probability of Backtest Overfitting" in app_text
    assert "Walk-Forward Stability" in app_text
    assert "Capacity Analysis" in app_text
    assert "Cost Sensitivity Analysis" in app_text
    assert "build_market_metric_display_payload" in app_text
    assert "output_metrics_for_product_lane" not in TECHNICAL_SIGNAL_FIELDS

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

    forbidden_signal_fields = {
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
    assert forbidden_signal_fields.isdisjoint(set(TECHNICAL_SIGNAL_FIELDS))
    for market_fields in TECHNICAL_SIGNAL_FIELDS_BY_MARKET.values():
        assert forbidden_signal_fields.isdisjoint(set(market_fields.get("required", [])))
        assert forbidden_signal_fields.isdisjoint(set(market_fields.get("optional", [])))

    assert not any(ROOT.glob("pages/*.py")), "Unexpected frontend page files were added."
    assert not any(ROOT.glob("app/pages/*.py")), "Unexpected app/pages/*.py files were added."
    assert not any(ROOT.glob("frontend/*.py")), "Unexpected frontend/*.py files were added."
    assert not any(ROOT.glob("frontend/pages/*.py")), "Unexpected frontend/pages/*.py files were added."

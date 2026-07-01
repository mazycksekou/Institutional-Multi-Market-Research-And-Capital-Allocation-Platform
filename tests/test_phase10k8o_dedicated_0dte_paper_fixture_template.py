from __future__ import annotations

import re
from pathlib import Path

from src.services.streamlit_dashboard_facade import TECHNICAL_SIGNAL_FIELDS, TECHNICAL_SIGNAL_FIELDS_BY_MARKET, technical_fields_for_market
from src.data.zero_dte_fixture_template import ZERO_DTE_MODE_KEY, ZERO_DTE_PAPER_FIXTURE_OPTIONAL_FIELDS, ZERO_DTE_PAPER_FIXTURE_REQUIRED_FIELDS, ZERO_DTE_PAPER_REVIEW_OUTPUT_FIELDS, ZERO_DTE_PAPER_TEMPLATE_FIELD_GROUPS, ZERO_DTE_PAPER_TEMPLATE_GUARDRAILS, build_zero_dte_fixture_template_row, describe_zero_dte_fixture_template, zero_dte_fixture_field_groups, zero_dte_fixture_fields


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8O_DEDICATED_0DTE_PAPER_FIXTURE_TEMPLATE.md"
STREAMLIT_APP = ROOT / "streamlit_app.py"
LEGACY_PHASE_TEST = ROOT / "tests" / "test_phase10k6k_controlled_dashboard_shell_review.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def flatten_market_fields() -> set[str]:
    flattened: set[str] = set()
    for market_spec in TECHNICAL_SIGNAL_FIELDS_BY_MARKET.values():
        flattened.update(market_spec.get("required", []))
        flattened.update(market_spec.get("optional", []))
    return flattened


def test_phase10k8o_dedicated_0dte_paper_fixture_template() -> None:
    assert REPORT.is_file(), "Expected the 10K8O review report to exist."
    assert STREAMLIT_APP.is_file(), "Expected streamlit_app.py to exist."
    assert LEGACY_PHASE_TEST.is_file(), "Expected the prior dashboard shell review test to remain."

    report_text = read_text(REPORT)
    streamlit_text = read_text(STREAMLIT_APP)

    required_report_strings = [
        "Dedicated 0DTE Paper Fixture Template",
        "automation_scheduler/zero_dte_fixture_template.py",
        "automation_scheduler/model_data_field_catalog.py",
        "streamlit_app.py",
        "quant_engine.py",
        "existing owner rule",
        "One 0DTE Options Trade",
        "0DTE is the primary active trading lane",
        "ZERO_DTE_PAPER_FIXTURE_REQUIRED_FIELDS",
        "ZERO_DTE_PAPER_FIXTURE_OPTIONAL_FIELDS",
        "ZERO_DTE_PAPER_REVIEW_OUTPUT_FIELDS",
        "ZERO_DTE_PAPER_TEMPLATE_FIELD_GROUPS",
        "zero_dte_fixture_field_groups",
        "zero_dte_fixture_fields",
        "build_zero_dte_fixture_template_row",
        "describe_zero_dte_fixture_template",
        "underlying_symbol",
        "underlying_price",
        "expiration_date",
        "minutes_to_expiration",
        "strike",
        "option_type",
        "call_put",
        "bid",
        "ask",
        "mid",
        "implied_volatility",
        "delta",
        "gamma",
        "theta",
        "vega",
        "spread_percent",
        "premium",
        "paper_arbitrage_percentage",
        "paper arbitrage percentage within tested timeframe",
        "paper_arbitrage_window",
        "paper_arbitrage_timeframe",
        "paper_arbitrage_best_percentage",
        "paper_arbitrage_liquidity_adjusted_percentage",
        "paper_arbitrage_after_spread_percentage",
        "paper_arbitrage_after_fees_percentage",
        "EV stays in quant_engine.py",
        "edge stays in quant_engine.py",
        "Kelly stays in quant_engine.py",
        "arbitrage stays out of TECHNICAL_SIGNAL_FIELDS",
        "paper arbitrage outputs are review-only",
        "technical signals are not universal math outputs",
        "paper-only prediction testing",
        "local fixture-backed testing",
        "readiness only",
        "no live connectors",
        "no API calls",
        "no database writes",
        "no broker execution",
        "no real trade execution",
        "no duplicate owner created",
        "no temporary git shim",
        "do not label quality automatically",
        "do not hide valid results because sample size is low",
        "user threshold review-only",
        "validity check only",
        "implementation reviewed in 10K8O",
    ]
    for needle in required_report_strings:
        assert needle in report_text, f"Missing report string: {needle}"

    required_streamlit_strings = [
        "Dedicated 0DTE research backtest fixture template",
        "0DTE is the primary active trading lane",
        "local fixture-backed testing",
        "paper-only",
        "readiness only",
        "no broker execution",
        "no real trade execution",
        "no live connectors",
        "no API calls",
        "no database writes",
        "research_backtest_arbitrage_percentage",
        "research_backtest_arbitrage_percentage within tested timeframe",
    ]
    for needle in required_streamlit_strings:
        assert needle in streamlit_text, f"Missing streamlit_app.py string: {needle}"

    assert ZERO_DTE_MODE_KEY == "one_0dte_options_trade"

    required_expected = {
        "fixture_id",
        "sport_or_market",
        "event_id",
        "prediction_target",
        "selection",
        "source_type",
        "execution_mode",
        "underlying_symbol",
        "underlying_price",
        "trade_date",
        "timestamp",
        "expiration_date",
        "minutes_to_expiration",
        "strike",
        "option_type",
        "call_put",
        "bid",
        "ask",
        "mid",
        "volume",
        "open_interest",
        "implied_volatility",
        "delta",
        "gamma",
        "theta",
        "vega",
        "moneyness",
        "spread",
        "spread_percent",
        "premium",
        "model_probability",
        "market_odds_american",
        "result_label",
        "outcome_known",
    }
    optional_expected = {
        "days_to_expiration",
        "mark",
        "last_price",
        "rho",
        "intrinsic_value",
        "extrinsic_value",
        "underlying_open",
        "underlying_high",
        "underlying_low",
        "underlying_close",
        "underlying_volume",
        "vwap",
        "ema_12",
        "ema_26",
        "macd",
        "macd_signal_line",
        "macd_histogram",
        "macd_divergence",
        "rsi",
        "adx",
        "support_level",
        "resistance_level",
        "opening_price",
        "current_price",
        "closing_price",
        "price_gap",
        "trend_line",
        "breakout_level",
        "breakdown_level",
        "earnings_context",
        "macro_context",
        "fed_event_context",
        "news_context",
        "market_regime",
        "risk_free_rate",
        "paper_arbitrage_window",
        "paper_arbitrage_timeframe",
        "paper_arbitrage_basis",
    }
    review_expected = {
        "implied_probability",
        "fair_odds",
        "edge",
        "expected_value",
        "ev",
        "kelly_fraction",
        "kelly_stake",
        "bankroll_cap",
        "confidence",
        "no_bet_flags",
        "risk_flags",
        "paper_edge",
        "paper_ev",
        "paper_stake_units",
        "paper_result",
        "paper_arbitrage_percentage",
        "paper_arbitrage_window",
        "paper_arbitrage_timeframe",
        "paper_arbitrage_start_time",
        "paper_arbitrage_end_time",
        "paper_arbitrage_basis",
        "paper_arbitrage_opportunity_count",
        "paper_arbitrage_best_percentage",
        "paper_arbitrage_average_percentage",
        "paper_arbitrage_liquidity_adjusted_percentage",
        "paper_arbitrage_after_spread_percentage",
        "paper_arbitrage_after_fees_percentage",
        "paper_arbitrage_review_note",
    }

    assert required_expected.issubset(set(ZERO_DTE_PAPER_FIXTURE_REQUIRED_FIELDS))
    assert optional_expected.issubset(set(ZERO_DTE_PAPER_FIXTURE_OPTIONAL_FIELDS))
    assert review_expected.issubset(set(ZERO_DTE_PAPER_REVIEW_OUTPUT_FIELDS))
    assert "paper_arbitrage_percentage" not in TECHNICAL_SIGNAL_FIELDS

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
    assert not forbidden_signal_fields.intersection(TECHNICAL_SIGNAL_FIELDS)
    assert not forbidden_signal_fields.intersection(flatten_market_fields())
    for market in TECHNICAL_SIGNAL_FIELDS_BY_MARKET:
        assert not forbidden_signal_fields.intersection(set(technical_fields_for_market(market))), market

    groups = zero_dte_fixture_field_groups()
    assert set(groups.keys()) == {
        "required_input_fields",
        "optional_input_fields",
        "technical_signal_fields",
        "paper_fixture_fields",
        "review_output_fields",
        "paper_arbitrage_output_fields",
        "guardrail_fields",
    }

    for key in [
        "required_input_fields",
        "optional_input_fields",
        "technical_signal_fields",
        "paper_fixture_fields",
        "review_output_fields",
        "paper_arbitrage_output_fields",
        "guardrail_fields",
    ]:
        assert groups[key], f"Expected non-empty field group: {key}"

    flat_fields = zero_dte_fixture_fields()
    assert len(flat_fields) == len(dict.fromkeys(flat_fields))
    assert set(required_expected).issubset(set(flat_fields))
    assert set(review_expected).issubset(set(flat_fields))

    row = build_zero_dte_fixture_template_row()
    assert isinstance(row, dict)
    for field in ZERO_DTE_PAPER_FIXTURE_REQUIRED_FIELDS:
        assert field in row

    summary = describe_zero_dte_fixture_template()
    assert summary["mode_key"] == ZERO_DTE_MODE_KEY
    assert summary["required_count"] == len(ZERO_DTE_PAPER_FIXTURE_REQUIRED_FIELDS)
    assert summary["optional_count"] == len(ZERO_DTE_PAPER_FIXTURE_OPTIONAL_FIELDS)
    assert summary["review_output_count"] == len(ZERO_DTE_PAPER_REVIEW_OUTPUT_FIELDS)
    assert summary["guardrails"] == list(ZERO_DTE_PAPER_TEMPLATE_GUARDRAILS)
    assert summary["field_groups"] == groups

    assert ZERO_DTE_PAPER_TEMPLATE_FIELD_GROUPS == groups
    assert list(ZERO_DTE_PAPER_TEMPLATE_GUARDRAILS)

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

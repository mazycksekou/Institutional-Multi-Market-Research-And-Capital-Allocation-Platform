from __future__ import annotations

from pathlib import Path

from automation_scheduler.model_data_field_catalog import fields_for_model_mode
from automation_scheduler.technical_signal_fields import (
    TECHNICAL_SIGNAL_FIELDS,
    TECHNICAL_SIGNAL_FIELDS_BY_MARKET,
)
from automation_scheduler.zero_dte_fixture_template import (
    ZERO_DTE_PAPER_FIXTURE_OPTIONAL_FIELDS,
    ZERO_DTE_PAPER_FIXTURE_REQUIRED_FIELDS,
    ZERO_DTE_PAPER_REVIEW_OUTPUT_FIELDS,
    build_zero_dte_fixture_template_row,
    build_zero_dte_paper_pipeline_result,
    evaluate_zero_dte_paper_fixture_rows,
    validate_zero_dte_fixture_rows,
)


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8ZA_0DTE_DATA_FIELD_FORMULA_COVERAGE_AUDIT.md"
APP = ROOT / "streamlit_app.py"
LEGACY_PHASE_TEST = ROOT / "tests" / "test_phase10k6k_controlled_dashboard_shell_review.py"
FINAL_FREEZE_REPORT = ROOT / "PHASE10K8Z_FINAL_CONTROLLED_PREDICTION_TESTING_FREEZE.md"
TEMPLATE_SOURCE = ROOT / "automation_scheduler" / "zero_dte_fixture_template.py"
QUANT_ENGINE = ROOT / "quant_engine.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def flatten_market_signal_fields() -> set[str]:
    combined: set[str] = set()
    for spec in TECHNICAL_SIGNAL_FIELDS_BY_MARKET.values():
        combined.update(spec.get("required", []))
        combined.update(spec.get("optional", []))
    return combined


def test_phase10k8za_0dte_data_field_formula_coverage_audit() -> None:
    assert REPORT.is_file(), "Expected the 10K8ZA audit report to exist."
    assert FINAL_FREEZE_REPORT.is_file(), "Expected the 10K8Z freeze report to remain present."
    assert APP.is_file(), "Expected streamlit_app.py to remain present."
    assert LEGACY_PHASE_TEST.is_file(), "Expected the prior dashboard shell review test to remain."

    report_text = read_text(REPORT)
    app_text = read_text(APP)
    legacy_test_text = read_text(LEGACY_PHASE_TEST)
    template_source_text = read_text(TEMPLATE_SOURCE)
    quant_source_text = read_text(QUANT_ENGINE)

    required_report_strings = [
        "0DTE Data Field + Formula Coverage Audit",
        "10K8ZA",
        "0DTE is the primary active trading lane",
        "controlled paper-only prediction testing",
        "local fixture-backed testing",
        "readiness only",
        "review-only",
        "no broker execution",
        "no real trade execution",
        "no live connectors",
        "no API calls",
        "no database writes",
        "no file upload",
        "no CSV parsing",
        "no frontend page files",
        "no guaranteed profit language",
        "no assured profit language",
        "unsupported 8-figure certainty claims excluded",
        "market-maker trapped language softened",
        "pinning is not guaranteed",
        "bid",
        "ask",
        "mid",
        "mark",
        "last_price",
        "implied_volatility",
        "delta",
        "gamma",
        "theta",
        "vega",
        "volume",
        "open_interest",
        "volume_open_interest_ratio",
        "bid_size",
        "ask_size",
        "quoted_depth",
        "liquidity_score",
        "slippage_estimate",
        "net_gex",
        "strike_gex",
        "call_gex",
        "put_gex",
        "gamma_flip_level",
        "gex_regime",
        "0DTE volume profile",
        "strike_volume_profile",
        "volume_profile_peak_strike",
        "strategy_type",
        "iron_condor",
        "iron_butterfly",
        "vertical_credit_spread",
        "long_straddle",
        "long_strangle",
        "single_call_put_scalp",
        "max_profit",
        "max_loss",
        "breakeven_low",
        "breakeven_high",
        "risk_reward_ratio",
        "cpi_day",
        "fomc_day",
        "jobs_day",
        "fed_speaker_day",
        "spread = ask - bid",
        "mid = (bid + ask) / 2",
        "spread_percent = spread / mid",
        "volume_open_interest_ratio = volume / open_interest",
        "implied_probability_from_american_odds",
        "paper_edge = model_probability - implied_probability",
        "paper_ev = paper_edge * premium",
        "moneyness",
        "moneyness_percent",
        "estimated_slippage",
        "implementation reviewed in 10K8ZA",
    ]
    for needle in required_report_strings:
        assert needle in report_text, f"Missing report string: {needle}"

    template_row = build_zero_dte_fixture_template_row()
    template_keys = set(template_row)
    model_fields = set(fields_for_model_mode("one_0dte_options_trade"))
    evaluation_result = evaluate_zero_dte_paper_fixture_rows([template_row])
    pipeline_result = build_zero_dte_paper_pipeline_result([template_row])

    core_fields = [
        "bid",
        "ask",
        "mid",
        "last_price",
        "implied_volatility",
        "delta",
        "gamma",
        "theta",
        "vega",
        "volume",
        "open_interest",
        "underlying_symbol",
        "underlying_price",
        "trade_date",
        "timestamp",
        "expiration_date",
        "minutes_to_expiration",
        "strike",
        "option_type",
        "call_put",
        "moneyness",
        "spread",
        "spread_percent",
        "premium",
    ]
    assert set(core_fields).issubset(template_keys | model_fields)

    intraday_context_fields = [
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
        "rsi",
        "adx",
        "support_level",
        "resistance_level",
        "trend_line",
        "breakout_level",
        "breakdown_level",
    ]
    assert set(intraday_context_fields).issubset(template_keys | model_fields)

    assert "paper_edge" in evaluation_result["evaluation_rows"][0]
    assert "paper_ev" in evaluation_result["evaluation_rows"][0]
    assert "paper_stake_units" in evaluation_result["evaluation_rows"][0]
    assert "paper_result" in evaluation_result["evaluation_rows"][0]
    assert "paper_arbitrage_percentage" in evaluation_result["evaluation_rows"][0]
    assert "total_paper_ev" in evaluation_result
    assert "total_paper_stake_units" in evaluation_result
    assert "total_paper_arbitrage_percentage" in evaluation_result
    assert "average_paper_arbitrage_percentage" in evaluation_result
    assert "total_paper_ev" in pipeline_result
    assert "total_paper_stake_units" in pipeline_result
    assert "total_paper_arbitrage_percentage" in pipeline_result
    assert "average_paper_arbitrage_percentage" in pipeline_result

    advanced_fields = [
        "volume_open_interest_ratio",
        "bid_size",
        "ask_size",
        "quoted_depth",
        "liquidity_score",
        "slippage_estimate",
        "net_gex",
        "strike_gex",
        "call_gex",
        "put_gex",
        "gamma_flip_level",
        "gex_regime",
        "strike_volume_profile",
        "volume_profile_peak_strike",
        "strategy_type",
        "iron_condor",
        "iron_butterfly",
        "vertical_credit_spread",
        "long_straddle",
        "long_strangle",
        "single_call_put_scalp",
        "max_profit",
        "max_loss",
        "breakeven_low",
        "breakeven_high",
        "risk_reward_ratio",
        "cpi_day",
        "fomc_day",
        "jobs_day",
        "fed_speaker_day",
    ]
    missing_candidates = [
        field
        for field in advanced_fields
        if field not in template_keys and field not in model_fields
    ]
    assert missing_candidates, "Expected material 0DTE field gaps for the audit."
    for needle in missing_candidates:
        assert needle in report_text, f"Missing current gap mention: {needle}"

    for needle in advanced_fields:
        assert needle in report_text, f"Missing advanced field mention: {needle}"

    assert "implied_probability_from_american_odds" in template_source_text
    assert "paper_edge" in template_source_text or "paper_edge" in report_text
    assert "paper_ev" in template_source_text or "paper_ev" in report_text
    assert "spread = ask - bid" in report_text
    assert "volume_open_interest_ratio = volume / open_interest" in report_text
    assert "estimated_slippage" in report_text

    assert "ev" not in TECHNICAL_SIGNAL_FIELDS
    assert "expected_value" not in TECHNICAL_SIGNAL_FIELDS
    assert "edge" not in TECHNICAL_SIGNAL_FIELDS
    assert "arbitrage" not in TECHNICAL_SIGNAL_FIELDS
    assert "kelly" not in TECHNICAL_SIGNAL_FIELDS
    assert "fair_odds" not in TECHNICAL_SIGNAL_FIELDS
    assert "implied_probability" not in TECHNICAL_SIGNAL_FIELDS
    assert "bankroll" not in TECHNICAL_SIGNAL_FIELDS
    assert "confidence" not in TECHNICAL_SIGNAL_FIELDS
    assert "no_bet" not in TECHNICAL_SIGNAL_FIELDS
    assert "no-bet" not in TECHNICAL_SIGNAL_FIELDS
    assert "paper_arbitrage_percentage" not in TECHNICAL_SIGNAL_FIELDS

    flattened_market_fields = flatten_market_signal_fields()
    banned_terms = {
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
    assert banned_terms.isdisjoint(set(TECHNICAL_SIGNAL_FIELDS))
    assert banned_terms.isdisjoint(flattened_market_fields)

    assert "Connect Real Vendor API" not in app_text
    assert "Run Real Line Movement Scraper" not in app_text
    assert "Connect Synthetic Vendor API" not in app_text
    assert "Run Synthetic Scraper" not in app_text
    assert "Execute Real Trade" not in app_text
    assert "Send Broker Order" not in app_text
    assert "Place Live Order" not in app_text
    assert "guaranteed profit" not in app_text
    assert "assured profit" not in app_text

    for pattern in [
        "pages/*.py",
        "app/pages/*.py",
        "frontend/*.py",
        "frontend/pages/*.py",
    ]:
        assert not list(Path(".").glob(pattern)), f"Unexpected frontend page files found for pattern: {pattern}"

    assert "subprocess" not in legacy_test_text
    assert "git ls-files" not in legacy_test_text
    assert "git status" not in legacy_test_text
    assert "git shim" not in legacy_test_text


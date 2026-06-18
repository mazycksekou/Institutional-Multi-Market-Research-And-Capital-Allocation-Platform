from __future__ import annotations

from pathlib import Path

from automation_scheduler.model_data_field_catalog import (
    ZERO_DTE_GEX_FIELDS,
    ZERO_DTE_LIQUIDITY_EXECUTION_FIELDS,
    ZERO_DTE_MACRO_EVENT_FIELDS,
    ZERO_DTE_STRATEGY_FIELDS,
    ZERO_DTE_VOLUME_PROFILE_FIELDS,
    fields_for_model_mode,
)
from automation_scheduler.technical_signal_fields import (
    TECHNICAL_SIGNAL_FIELDS,
    TECHNICAL_SIGNAL_FIELDS_BY_MARKET,
)
from automation_scheduler.zero_dte_fixture_template import (
    ZERO_DTE_PAPER_FIXTURE_OPTIONAL_FIELDS,
    build_zero_dte_fixture_template_row,
    build_zero_dte_formula_snapshot,
    build_zero_dte_paper_pipeline_result,
    calculate_zero_dte_estimated_slippage,
    calculate_zero_dte_mid_price,
    calculate_zero_dte_moneyness,
    calculate_zero_dte_moneyness_percent,
    calculate_zero_dte_spread,
    calculate_zero_dte_spread_percent,
    calculate_zero_dte_volume_open_interest_ratio,
)


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8ZB_0DTE_FIELD_FORMULA_GAP_PATCH.md"
APP = ROOT / "streamlit_app.py"
LEGACY_PHASE_TEST = ROOT / "tests" / "test_phase10k6k_controlled_dashboard_shell_review.py"
FINAL_FREEZE_REPORT = ROOT / "PHASE10K8Z_FINAL_CONTROLLED_PREDICTION_TESTING_FREEZE.md"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def flattened_market_signal_fields() -> set[str]:
    combined: set[str] = set()
    for spec in TECHNICAL_SIGNAL_FIELDS_BY_MARKET.values():
        combined.update(spec.get("required", []))
        combined.update(spec.get("optional", []))
    return combined


def test_phase10k8zb_0dte_field_formula_gap_patch() -> None:
    assert REPORT.is_file(), "Expected the 10K8ZB audit report to exist."
    assert FINAL_FREEZE_REPORT.is_file(), "Expected the 10K8Z freeze report to remain present."
    assert APP.is_file(), "Expected streamlit_app.py to remain present."
    assert LEGACY_PHASE_TEST.is_file(), "Expected the prior dashboard shell review test to remain."

    report_text = read_text(REPORT)
    app_text = read_text(APP)
    legacy_test_text = read_text(LEGACY_PHASE_TEST)

    required_report_strings = [
        "0DTE Field + Formula Gap Patch",
        "10K8ZB",
        "PHASE10K8ZA_0DTE_DATA_FIELD_FORMULA_COVERAGE_AUDIT.md",
        "0DTE is the primary active trading lane",
        "controlled paper-only prediction testing",
        "local fixture-backed testing",
        "readiness only",
        "review-only formulas",
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
        "automation_scheduler/zero_dte_fixture_template.py",
        "automation_scheduler/model_data_field_catalog.py",
        "automation_scheduler/technical_signal_fields.py",
        "streamlit_app.py",
        "ZERO_DTE_LIQUIDITY_EXECUTION_FIELDS",
        "ZERO_DTE_GEX_FIELDS",
        "ZERO_DTE_VOLUME_PROFILE_FIELDS",
        "ZERO_DTE_STRATEGY_FIELDS",
        "ZERO_DTE_MACRO_EVENT_FIELDS",
        "build_zero_dte_formula_snapshot",
        "calculate_zero_dte_mid_price",
        "calculate_zero_dte_spread",
        "calculate_zero_dte_spread_percent",
        "calculate_zero_dte_volume_open_interest_ratio",
        "calculate_zero_dte_moneyness",
        "calculate_zero_dte_moneyness_percent",
        "calculate_zero_dte_estimated_slippage",
        "spread = ask - bid",
        "mid = (bid + ask) / 2",
        "spread_percent = spread / mid",
        "volume_open_interest_ratio = volume / open_interest",
        "moneyness_percent",
        "estimated_slippage",
        "formula_snapshots",
        "average_spread_percent",
        "average_volume_open_interest_ratio",
        "average_estimated_slippage_midpoint",
        "paper_arbitrage_percentage remains review-only",
        "implementation reviewed in 10K8ZB",
    ]
    for needle in required_report_strings:
        assert needle in report_text, f"Missing report string: {needle}"

    advanced_fields = [
        "volume_open_interest_ratio",
        "bid_size",
        "ask_size",
        "quoted_depth",
        "liquidity_score",
        "slippage_estimate",
        "estimated_slippage",
        "max_contracts_at_top_of_book",
        "execution_capacity_warning",
        "net_gex",
        "strike_gex",
        "call_gex",
        "put_gex",
        "gamma_flip_level",
        "gex_regime",
        "strike_volume_profile",
        "volume_profile_peak_strike",
        "call_volume_by_strike",
        "put_volume_by_strike",
        "total_volume_by_strike",
        "volume_profile_skew",
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

    assert set(advanced_fields).issubset(set(ZERO_DTE_PAPER_FIXTURE_OPTIONAL_FIELDS))
    assert set(advanced_fields).issubset(set(build_zero_dte_fixture_template_row().keys()))
    assert set(advanced_fields).issubset(set(fields_for_model_mode("one_0dte_options_trade")))

    assert set(ZERO_DTE_LIQUIDITY_EXECUTION_FIELDS).issubset(set(fields_for_model_mode("one_0dte_options_trade")))
    assert set(ZERO_DTE_GEX_FIELDS).issubset(set(fields_for_model_mode("one_0dte_options_trade")))
    assert set(ZERO_DTE_VOLUME_PROFILE_FIELDS).issubset(set(fields_for_model_mode("one_0dte_options_trade")))
    assert set(ZERO_DTE_STRATEGY_FIELDS).issubset(set(fields_for_model_mode("one_0dte_options_trade")))
    assert set(ZERO_DTE_MACRO_EVENT_FIELDS).issubset(set(fields_for_model_mode("one_0dte_options_trade")))

    assert calculate_zero_dte_mid_price(10, 12) == 11
    assert calculate_zero_dte_mid_price(None, 12) is None
    assert calculate_zero_dte_spread(10, 12) == 2
    assert calculate_zero_dte_spread(12, 10) is None
    assert calculate_zero_dte_spread_percent(10, 12) == 2 / 11
    assert calculate_zero_dte_volume_open_interest_ratio(200, 100) == 2
    assert calculate_zero_dte_volume_open_interest_ratio(200, 0) is None
    assert calculate_zero_dte_moneyness(5000, 4990, "call") == 10
    assert calculate_zero_dte_moneyness(5000, 5010, "put") == 10
    assert calculate_zero_dte_moneyness_percent(5000, 5010) == 10 / 5000
    assert calculate_zero_dte_estimated_slippage(10, 12, "midpoint") == 1
    assert calculate_zero_dte_estimated_slippage(10, 12, "marketable") == 2
    assert calculate_zero_dte_estimated_slippage(12, 10, "midpoint") is None

    row = build_zero_dte_fixture_template_row()
    row.update(
        {
            "bid": 10,
            "ask": 12,
            "volume": 200,
            "open_interest": 100,
            "underlying_price": 5000,
            "strike": 4990,
            "call_put": "call",
        }
    )
    formula_snapshot = build_zero_dte_formula_snapshot(row)
    assert formula_snapshot["mid"] == 11
    assert formula_snapshot["spread"] == 2
    assert formula_snapshot["spread_percent"] == 2 / 11
    assert formula_snapshot["volume_open_interest_ratio"] == 2
    assert formula_snapshot["moneyness"] == 10
    assert formula_snapshot["moneyness_percent"] == 10 / 5000
    assert formula_snapshot["estimated_slippage_midpoint"] == 1
    assert formula_snapshot["estimated_slippage_marketable"] == 2
    assert formula_snapshot["formula_owner"] == "automation_scheduler/zero_dte_fixture_template.py"
    assert formula_snapshot["formula_mode"] == "local_fixture_readiness_only"
    assert formula_snapshot["prediction_testing_started"] is False
    assert formula_snapshot["live_connectors_enabled"] is False
    assert formula_snapshot["api_calls_enabled"] is False
    assert formula_snapshot["database_writes_enabled"] is False
    assert formula_snapshot["broker_execution_enabled"] is False
    assert formula_snapshot["real_trade_execution_enabled"] is False

    pipeline_result = build_zero_dte_paper_pipeline_result([row])
    assert pipeline_result["formula_snapshots"]
    assert pipeline_result["formula_snapshot_count"] == 1
    assert pipeline_result["average_spread_percent"] == 2 / 11
    assert pipeline_result["average_volume_open_interest_ratio"] == 2
    assert pipeline_result["average_estimated_slippage_midpoint"] == 1
    assert pipeline_result["formula_guardrails"]
    assert pipeline_result["pipeline_ready_for_review"] is True
    assert pipeline_result["low_sample_size_does_not_hide_valid_results"] is True
    assert pipeline_result["quality_not_automatically_labeled"] is True
    assert pipeline_result["user_threshold_review_only"] is True

    assert "0DTE field and formula gap patch" in app_text
    assert "build_zero_dte_formula_snapshot" in app_text
    assert "calculate_zero_dte_mid_price" in app_text
    assert "calculate_zero_dte_spread" in app_text
    assert "calculate_zero_dte_spread_percent" in app_text
    assert "calculate_zero_dte_volume_open_interest_ratio" in app_text
    assert "calculate_zero_dte_moneyness" in app_text
    assert "calculate_zero_dte_moneyness_percent" in app_text
    assert "calculate_zero_dte_estimated_slippage" in app_text
    assert "formula_snapshots" in app_text
    assert "average_spread_percent" in app_text
    assert "average_volume_open_interest_ratio" in app_text
    assert "average_estimated_slippage_midpoint" in app_text
    assert "paper-only" in app_text
    assert "readiness only" in app_text
    assert "review-only formulas" in app_text
    assert "local fixture-backed testing" in app_text
    assert "no broker execution" in app_text
    assert "no real trade execution" in app_text
    assert "no live connectors" in app_text
    assert "no API calls" in app_text
    assert "no database writes" in app_text

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

    flattened_market_fields = flattened_market_signal_fields()
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


from __future__ import annotations

import re
from pathlib import Path

from automation_scheduler.model_data_field_catalog import (
    MODEL_DATA_FIELD_GROUPS_BY_MODE,
    PAPER_ARBITRAGE_OUTPUT_FIELDS,
    SPORTS_MODEL_INPUT_FIELD_GROUPS_BY_SPORT,
    field_groups_for_model_mode,
    fields_for_model_mode,
    fields_for_sport,
)
from automation_scheduler.technical_signal_fields import (
    TECHNICAL_SIGNAL_FIELDS,
    TECHNICAL_SIGNAL_FIELDS_BY_MARKET,
    technical_fields_for_market,
)


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "PHASE10K8N_CONTROLLED_FIELD_CATALOG_UI_REVIEW.md"
STREAMLIT_APP = ROOT / "streamlit_app.py"
LEGACY_PHASE_TEST = ROOT / "tests" / "test_phase10k6k_controlled_dashboard_shell_review.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def flatten_technical_market_fields() -> set[str]:
    flattened: set[str] = set()
    for market_spec in TECHNICAL_SIGNAL_FIELDS_BY_MARKET.values():
        flattened.update(market_spec.get("required", []))
        flattened.update(market_spec.get("optional", []))
    return flattened


def test_phase10k8n_controlled_field_catalog_ui_review() -> None:
    assert REPORT.is_file(), "Expected the 10K8N review report to exist."
    assert STREAMLIT_APP.is_file(), "Expected streamlit_app.py to exist."
    assert LEGACY_PHASE_TEST.is_file(), "Expected the prior dashboard shell review test to remain."

    report_text = read_text(REPORT)
    streamlit_text = read_text(STREAMLIT_APP)
    mode_catalog = MODEL_DATA_FIELD_GROUPS_BY_MODE
    sport_catalog = SPORTS_MODEL_INPUT_FIELD_GROUPS_BY_SPORT

    required_report_strings = [
        "Controlled Field Catalog UI Review",
        "streamlit_app.py",
        "automation_scheduler/model_data_field_catalog.py",
        "automation_scheduler/technical_signal_fields.py",
        "quant_engine.py",
        "existing owner rule",
        "Controlled model field catalog",
        "strict model field baseline by market and sport",
        "One Sport",
        "One Stock Market",
        "One Crypto Market",
        "One Prediction Market",
        "One 0DTE Options Trade",
        "Dedicated 0DTE Options Trade mode",
        "0DTE is the primary active trading lane",
        "All Ready removed as redundant",
        "basketball_nba",
        "basketball_wnba",
        "basketball_ncaab",
        "basketball_ncaaw",
        "americanfootball_nfl",
        "americanfootball_ncaaf",
        "baseball_mlb",
        "icehockey_nhl",
        "soccer",
        "tennis",
        "ufc_mma",
        "boxing",
        "golf",
        "underlying_identity_fields",
        "underlying_quote_fields",
        "underlying_line_data_fields",
        "underlying_price_action_fields",
        "options_contract_fields",
        "options_quote_fields",
        "greeks_fields",
        "expiration_fields",
        "volatility_fields",
        "liquidity_spread_fields",
        "risk_fields",
        "macro_event_fields",
        "earnings_event_fields",
        "intraday_context_fields",
        "paper_arbitrage_percentage",
        "paper arbitrage percentage within tested timeframe",
        "paper_arbitrage_output_fields",
        "backtest_clv_output_fields",
        "universal_math_output_fields",
        "technical_signal_fields",
        "paper_fixture_fields",
        "readiness_output_fields",
        "evaluation_output_fields",
        "pipeline_output_fields",
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
        "implementation reviewed in 10K8N",
    ]
    for needle in required_report_strings:
        assert needle in report_text, f"Missing report string: {needle}"

    required_streamlit_strings = [
        "Controlled model field catalog",
        "strict model field baseline by market and sport",
        "Dedicated 0DTE Options Trade mode",
        "0DTE is the primary active trading lane",
        "All Ready removed as redundant",
        "paper_arbitrage_percentage",
        "paper arbitrage percentage within tested timeframe",
        "paper_arbitrage_output_fields",
        "backtest_clv_output_fields",
        "universal_math_output_fields",
        "technical_signal_fields",
        "paper_fixture_fields",
        "readiness_output_fields",
        "evaluation_output_fields",
        "pipeline_output_fields",
        "paper-only",
        "readiness only",
        "no live connectors",
        "no API calls",
        "no database writes",
        "no broker execution",
        "no real trade execution",
        "user threshold review-only",
        "validity check only",
        "do not label quality automatically",
        "do not hide valid results because sample size is low",
        "Feature Ablation Lab",
        "Bankroll Settings",
        "Instructions",
        "Sports",
        "0DTE Options",
        "Prediction Markets",
        "Data Warehouse",
        "Backtest Lab",
        "Model Diagnostics",
        "Arbitrage Lab",
        "Controlled Navigation Shell",
        "readiness display preview",
    ]
    for needle in required_streamlit_strings:
        assert needle in streamlit_text, f"Missing streamlit_app.py string: {needle}"

    mode_match = re.search(
        r"mode = st\.radio\(\s*\"Mode\",\s*\[(.*?)\],\s*key=\"fal_mode\",",
        streamlit_text,
        flags=re.S,
    )
    assert mode_match, "Expected the active mode selector to be present."
    mode_body = mode_match.group(1)
    mode_labels = re.findall(r"\"([^\"]+)\"", mode_body)
    assert mode_labels == [
        "One Sport",
        "One Stock Market",
        "One Crypto Market",
        "One Prediction Market",
        "One 0DTE Options Trade",
    ], f"Unexpected active mode labels: {mode_labels}"
    assert "All Ready" not in mode_body, "All Ready must not be selectable."

    assert set(mode_catalog.keys()) == {
        "one_sport",
        "one_stock_market",
        "one_crypto_market",
        "one_prediction_market",
        "one_0dte_options_trade",
    }
    assert "all_ready" not in mode_catalog

    zero_dte_groups = field_groups_for_model_mode("one_0dte_options_trade")
    for group_name in [
        "underlying_identity_fields",
        "underlying_quote_fields",
        "underlying_line_data_fields",
        "underlying_price_action_fields",
        "options_contract_fields",
        "options_quote_fields",
        "greeks_fields",
        "expiration_fields",
        "volatility_fields",
        "liquidity_spread_fields",
        "risk_fields",
        "macro_event_fields",
        "earnings_event_fields",
        "intraday_context_fields",
        "technical_signal_fields",
        "paper_fixture_fields",
    ]:
        assert group_name in zero_dte_groups, f"Missing 0DTE field group: {group_name}"

    assert fields_for_model_mode("one_0dte_options_trade"), "Expected flattened 0DTE fields."
    assert fields_for_sport("basketball_nba"), "Expected sport-specific flattening."

    expected_sports = {
        "basketball_nba",
        "basketball_wnba",
        "basketball_ncaab",
        "basketball_ncaaw",
        "americanfootball_nfl",
        "americanfootball_ncaaf",
        "baseball_mlb",
        "icehockey_nhl",
        "soccer",
        "tennis",
        "ufc_mma",
        "boxing",
        "golf",
    }
    assert expected_sports.issubset(sport_catalog.keys())

    required_paper_arbitrage_fields = {
        "paper_arbitrage_percentage",
        "paper_arbitrage_window",
        "paper_arbitrage_timeframe",
        "paper_arbitrage_best_percentage",
        "paper_arbitrage_liquidity_adjusted_percentage",
        "paper_arbitrage_after_spread_percentage",
        "paper_arbitrage_after_fees_percentage",
    }
    assert required_paper_arbitrage_fields.issubset(PAPER_ARBITRAGE_OUTPUT_FIELDS)
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
    flattened_technical_market_fields = flatten_technical_market_fields()
    assert not forbidden_signal_fields.intersection(TECHNICAL_SIGNAL_FIELDS)
    assert not forbidden_signal_fields.intersection(flattened_technical_market_fields)

    for market in TECHNICAL_SIGNAL_FIELDS_BY_MARKET:
        market_fields = set(technical_fields_for_market(market))
        assert not forbidden_signal_fields.intersection(market_fields), market

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

from __future__ import annotations

from pathlib import Path

from automation_scheduler.model_data_field_catalog import (
    MODEL_DATA_FIELD_GROUPS_BY_MODE,
    PAPER_ARBITRAGE_OUTPUT_FIELDS,
    SPORTS_MODEL_INPUT_FIELD_GROUPS_BY_SPORT,
    TECHNICAL_SIGNAL_EXCLUDED_UNIVERSAL_MATH_FIELDS,
    UNIVERSAL_MATH_OUTPUT_FIELDS,
    field_groups_for_model_mode,
    fields_for_model_mode,
    fields_for_sport,
)
from automation_scheduler.technical_signal_fields import (
    TECHNICAL_SIGNAL_FIELDS,
    TECHNICAL_SIGNAL_FIELDS_BY_MARKET,
    technical_fields_for_market,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
STREAMLIT_APP = REPO_ROOT / "streamlit_app.py"
DATA_SOURCE_REGISTRY = REPO_ROOT / "automation_scheduler" / "data_source_registry.py"
TECHNICAL_SIGNAL_FIELDS_FILE = REPO_ROOT / "automation_scheduler" / "technical_signal_fields.py"
MODEL_DATA_FIELD_CATALOG_FILE = REPO_ROOT / "automation_scheduler" / "model_data_field_catalog.py"
REPORT_FILE = REPO_ROOT / "PHASE10K8M_STRICT_MODEL_FIELD_BASELINE_BY_MARKET_AND_SPORT.md"
LEGACY_GUARDRAIL_TEST = (
    REPO_ROOT / "tests" / "test_phase10k6k_controlled_dashboard_shell_review.py"
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_mode_keys_are_strict_and_all_ready_is_removed() -> None:
    assert set(MODEL_DATA_FIELD_GROUPS_BY_MODE) == {
        "one_sport",
        "one_stock_market",
        "one_crypto_market",
        "one_prediction_market",
        "one_0dte_options_trade",
    }
    assert "all_ready" not in MODEL_DATA_FIELD_GROUPS_BY_MODE


def test_field_catalog_helpers_include_required_fields() -> None:
    stock_fields = fields_for_model_mode("one_stock_market")
    crypto_fields = fields_for_model_mode("one_crypto_market")
    prediction_fields = fields_for_model_mode("one_prediction_market")
    dte_fields = fields_for_model_mode("one_0dte_options_trade")

    for field in [
        "ETF_market_data",
        "earnings_call_text",
        "insider_transactions",
        "institutional_ownership",
        "options_context",
        "revenue",
        "eps",
        "pe_ratio",
        "price_target",
        "put_call_ratio",
        "term_structure",
    ]:
        assert field in stock_fields

    for field in [
        "order_book_depth",
        "funding_rates",
        "dex_liquidity",
        "gas_fees",
        "stablecoin_flows",
        "whale_activity_proxy",
        "active_addresses",
        "exchange_inflows",
        "fear_greed_index",
    ]:
        assert field in crypto_fields

    for field in [
        "contract_id",
        "market_id",
        "market_title",
        "contract_title",
        "settlement_rules",
        "resolution_criteria",
        "yes_price",
        "no_price",
        "orderbook_depth",
        "equivalent_contract",
        "arbitrage_gap",
        "settlement_risk",
    ]:
        assert field in prediction_fields

    for field in [
        "underlying_symbol",
        "underlying_price",
        "trade_date",
        "expiration_date",
        "days_to_expiration",
        "minutes_to_expiration",
        "strike",
        "option_type",
        "call_put",
        "bid",
        "ask",
        "mid",
        "mark",
        "last_price",
        "volume",
        "open_interest",
        "implied_volatility",
        "delta",
        "gamma",
        "theta",
        "vega",
        "rho",
        "moneyness",
        "intrinsic_value",
        "extrinsic_value",
        "spread",
        "spread_percent",
        "premium",
        "risk_free_rate",
    ]:
        assert field in dte_fields

    assert "technical_signal_fields" in field_groups_for_model_mode("one_0dte_options_trade")
    assert "paper_fixture_fields" in field_groups_for_model_mode("one_0dte_options_trade")


def test_sport_field_catalogs_include_required_fields() -> None:
    assert set(SPORTS_MODEL_INPUT_FIELD_GROUPS_BY_SPORT) == {
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

    assert all(
        field in fields_for_sport("basketball_nba")
        for field in [
            "minutes_projection",
            "usage_rate",
            "pace",
            "offensive_rating",
            "defensive_rating",
            "rebound_rate",
            "assist_rate",
            "three_point_rate",
        ]
    )
    assert all(
        field in fields_for_sport("americanfootball_nfl")
        for field in [
            "quarterback_status",
            "offensive_line_status",
            "skill_player_availability",
            "explosive_play_rate",
            "red_zone_rate",
        ]
    )
    assert all(
        field in fields_for_sport("baseball_mlb")
        for field in [
            "starting_pitcher",
            "bullpen_usage",
            "lineup_confirmed",
            "park_factor",
            "umpire_context",
        ]
    )
    assert all(
        field in fields_for_sport("icehockey_nhl")
        for field in [
            "starting_goalie",
            "goalie_confirmed",
            "expected_goals_for",
            "expected_goals_against",
            "line_combinations",
        ]
    )
    assert all(
        field in fields_for_sport("soccer")
        for field in [
            "draw_line",
            "double_chance",
            "draw_no_bet",
            "expected_goals",
            "expected_lineup",
        ]
    )
    assert all(
        field in fields_for_sport("tennis")
        for field in [
            "game_spread",
            "set_spread",
            "total_games",
            "serve_hold_rate",
            "break_rate",
        ]
    )
    assert all(
        field in fields_for_sport("ufc_mma")
        for field in [
            "fighter_a",
            "fighter_b",
            "method_prop",
            "round_prop",
            "takedown_defense",
            "weight_cut_context",
        ]
    )
    assert all(
        field in fields_for_sport("boxing")
        for field in [
            "fighter_a",
            "fighter_b",
            "method_prop",
            "round_prop",
            "reach",
            "weight_cut_context",
        ]
    )
    assert all(
        field in fields_for_sport("golf")
        for field in [
            "tournament",
            "course",
            "outright_price",
            "strokes_gained_approach",
            "course_fit",
        ]
    )


def test_technical_signal_fields_are_strict() -> None:
    for forbidden in [
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
    ]:
        assert forbidden not in TECHNICAL_SIGNAL_FIELDS
        for market_fields in TECHNICAL_SIGNAL_FIELDS_BY_MARKET.values():
            assert forbidden not in market_fields.get("required", [])
            assert forbidden not in market_fields.get("optional", [])
        assert forbidden in TECHNICAL_SIGNAL_EXCLUDED_UNIVERSAL_MATH_FIELDS

    required_0dte_fields = technical_fields_for_market("0dte_options")
    for field in [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "ema_12",
        "ema_26",
        "macd",
        "macd_signal_line",
        "macd_histogram",
        "macd_divergence",
        "vwap",
        "rsi",
        "adx",
    ]:
        assert field in required_0dte_fields

    assert "paper_arbitrage_percentage" not in TECHNICAL_SIGNAL_FIELDS


def test_report_and_source_texts_cover_the_new_baseline() -> None:
    streamlit_text = read_text(STREAMLIT_APP)
    data_source_registry_text = read_text(DATA_SOURCE_REGISTRY)
    technical_signal_text = read_text(TECHNICAL_SIGNAL_FIELDS_FILE)
    catalog_text = read_text(MODEL_DATA_FIELD_CATALOG_FILE)
    report_text = read_text(REPORT_FILE)
    legacy_guardrail_text = read_text(LEGACY_GUARDRAIL_TEST)

    selector_start = streamlit_text.index('st.radio(\n            "Mode",')
    selector_end = streamlit_text.index('key="fal_mode"', selector_start)
    selector_block = streamlit_text[selector_start:selector_end]
    assert "All Ready" not in selector_block

    for required in [
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
        "research_backtest_arbitrage_percentage",
        "research_backtest_arbitrage_percentage within tested timeframe",
        "research_backtest_arbitrage_window",
        "research_backtest_arbitrage_timeframe",
        "research_backtest_arbitrage_best_percentage",
        "research_backtest_arbitrage_liquidity_adjusted_percentage",
        "research_backtest_arbitrage_after_spread_percentage",
        "research_backtest_arbitrage_after_fees_percentage",
        "underlying_identity_fields",
        "options_contract_fields",
        "greeks_fields",
        "expiration_fields",
        "liquidity_spread_fields",
        "intraday_context_fields",
        "technical_signal_fields",
        "paper_fixture_fields",
        "readiness_output_fields",
        "evaluation_output_fields",
        "pipeline_output_fields",
        "universal_math_output_fields",
        "paper_arbitrage_output_fields",
        "backtest_clv_output_fields",
        "paper-only",
        "readiness only",
        "no live connectors",
        "no API calls",
        "no database writes",
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
    ]:
        assert required in streamlit_text

    for required in [
        "from .technical_signal_fields import technical_fields_for_market",
        "institutional_stock_pro_analyst",
        "cryptocurrency_edge_lab",
        "prediction_market",
        "odds",
        'technical_fields_for_market("stocks")',
        'technical_fields_for_market("crypto")',
        'technical_fields_for_market("prediction_markets")',
        'technical_fields_for_market("sports_odds")',
        'technical_fields_for_market("0dte_options")',
    ]:
        assert required in data_source_registry_text

    for required in [
        "TECHNICAL_SIGNAL_FIELDS",
        "TECHNICAL_SIGNAL_FIELDS_BY_MARKET",
        "technical_fields_for_market",
        "SPORTS_MODEL_INPUT_FIELD_GROUPS_BY_SPORT",
        "MODEL_DATA_FIELD_GROUPS_BY_MODE",
        "fields_for_model_mode",
        "field_groups_for_model_mode",
        "fields_for_sport",
        "Strict Model Field Baseline by Market and Sport",
        "EV stays in quant_engine.py",
        "edge stays in quant_engine.py",
        "Kelly stays in quant_engine.py",
        "arbitrage stays out of TECHNICAL_SIGNAL_FIELDS",
        "implied probability stays in quant_engine.py",
        "fair odds stays in quant_engine.py",
        "0DTE is the primary active trading lane",
        "paper arbitrage percentage within tested timeframe",
        "All Ready removed as redundant",
        "no live connectors",
        "no API calls",
        "no database writes",
        "no broker execution",
        "no real trade execution",
        "no duplicate owner created",
        "no temporary git shim",
        "implementation reviewed in 10K8M",
    ]:
        assert required in report_text

    for required in [
        "TECHNICAL_SIGNAL_FIELDS",
        "TECHNICAL_SIGNAL_FIELDS_BY_MARKET",
        "technical_fields_for_market",
    ]:
        assert required in technical_signal_text

    for required in [
        "SPORTS_MODEL_INPUT_FIELD_GROUPS_BY_SPORT",
        "MODEL_DATA_FIELD_GROUPS_BY_MODE",
        "fields_for_model_mode",
        "field_groups_for_model_mode",
        "fields_for_sport",
        "PAPER_ARBITRAGE_OUTPUT_FIELDS",
        "UNIVERSAL_MATH_OUTPUT_FIELDS",
        "TECHNICAL_SIGNAL_EXCLUDED_UNIVERSAL_MATH_FIELDS",
    ]:
        assert required in catalog_text

    assert "subprocess" not in legacy_guardrail_text
    assert "git ls-files" not in legacy_guardrail_text
    assert "git status" not in legacy_guardrail_text
    assert "git shim" not in legacy_guardrail_text


def test_no_separate_frontend_pages_exist() -> None:
    frontend_page_globs = [
        "pages/*.py",
        "app/pages/*.py",
        "frontend/*.py",
        "frontend/pages/*.py",
    ]
    for pattern in frontend_page_globs:
        assert not list(REPO_ROOT.glob(pattern))


def test_streamlit_ui_forbidden_connector_strings_are_absent() -> None:
    streamlit_text = read_text(STREAMLIT_APP)
    for forbidden in [
        "Connect Real Vendor API",
        "Run Real Line Movement Scraper",
        "Connect Synthetic Vendor API",
        "Run Synthetic Scraper",
    ]:
        assert forbidden not in streamlit_text

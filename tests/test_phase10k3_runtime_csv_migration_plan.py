"""Phase 10K3 runtime/CSV migration planning guard tests."""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "PHASE10K3_RUNTIME_CSV_MIGRATION_PLAN.md"


def _read_report() -> str:
    return REPORT_PATH.read_text(encoding="utf-8")


def test_phase10k3_report_exists_and_contains_required_strings() -> None:
    text = _read_report()
    required_strings = [
        "Runtime/CSV Migration Plan",
        "Storage Owner Validation",
        "market_research.db",
        "bets.csv",
        "get_runtime_data_path",
        "Existing sports SQLite flow was not replaced",
        "No runtime files were deleted",
        "No CSV paths were deleted",
        "No migration was executed in this phase",
        "Duplicate storage owners are tracked, not deleted",
        "Staged Migration Plan",
        "Mirror writes before switching reads",
        "Compare old vs warehouse rows",
        "Candidate for deletion after migration tests",
        "Do not add vendor connectors",
        "Do not start prediction testing",
        "Do not alter Streamlit main menu",
        "Asset-grade cleanup happens later",
    ]
    for expected in required_strings:
        assert expected in text


def test_phase10k3_report_contains_required_sections() -> None:
    text = _read_report()
    required_sections = [
        "## A. Executive Summary",
        "## B. Storage Owner Validation",
        "## C. Runtime/CSV Inventory",
        "## D. Warehouse Target Map",
        "## E. Existing Sports SQLite Preservation",
        "## F. Duplicate Storage Owner Register",
        "## G. Staged Migration Plan",
        "## H. No-Deletion Rule",
        "## I. Test Plan",
        "## J. Next Phase Impact",
    ]
    for section in required_sections:
        assert section in text


def test_streamlit_main_menu_remains_exactly_protected() -> None:
    content = (REPO_ROOT / "streamlit_app.py").read_text(encoding="utf-8")
    protected_menu = (
        'menu = st.sidebar.radio(\n'
        '    "Main Menu",\n'
        "    [\n"
        '        "Feature Ablation Lab",\n'
        '        "Bankroll Settings",\n'
        '        "Instructions",\n'
        "    ],\n"
        ")\n"
    )
    assert protected_menu in content


def test_runtime_and_bets_csv_owners_are_source_backed_and_documented() -> None:
    report = _read_report()
    data_paths = (REPO_ROOT / "automation_scheduler" / "data_paths.py").read_text(encoding="utf-8")
    csv_service = (REPO_ROOT / "src" / "services" / "bet_csv_service.py").read_text(encoding="utf-8")
    csv_routes = (REPO_ROOT / "src" / "api" / "bet_csv_routes.py").read_text(encoding="utf-8")
    bet_log = (REPO_ROOT / "bet_log.py").read_text(encoding="utf-8")

    assert "def get_runtime_data_path" in data_paths
    assert "AUTOMATION_DATA_DIR" in data_paths
    assert 'BETS_FILE = DATA_DIR / "bets.csv"' in csv_service
    assert "def append_bet(" in csv_service
    assert "def summarize_bets(" in csv_service
    assert "pd.read_csv(BETS_FILE)" in csv_routes
    assert 'BET_LOG_PATH = Path("data") / "bet_log.jsonl"' in bet_log

    for owner in (
        "automation_scheduler.data_paths",
        "src.services.bet_csv_service",
        "src.api.bet_csv_routes",
        "bet_log.py",
    ):
        assert owner in report


def test_market_research_db_targets_are_existing_schema_tables(tmp_path: Path) -> None:
    from research.market_research_schema import get_all_table_names
    from research.market_research_store import (
        initialize_market_research_db,
        list_market_research_tables,
    )

    db_path = tmp_path / "market_research.db"
    initialize_market_research_db(db_path)

    expected_targets = {
        "raw_sports_odds",
        "raw_equity_prices",
        "raw_option_chains",
        "raw_option_quotes",
        "raw_prediction_markets",
        "features_sports",
        "features_equities",
        "features_0dte_options",
        "features_prediction_markets",
        "model_predictions",
        "backtest_runs",
        "backtest_trades",
        "option_backtest_trades",
        "arbitrage_opportunities",
        "settlements",
        "performance_metrics",
    }
    schema_tables = set(get_all_table_names())
    created_tables = set(list_market_research_tables(db_path))
    assert expected_targets <= schema_tables
    assert expected_targets <= created_tables

    report = _read_report()
    for table_name in sorted(expected_targets):
        assert table_name in report


def test_existing_sports_sqlite_flow_is_preserved_by_source_and_report() -> None:
    report = _read_report()
    sqlite_owner = (REPO_ROOT / "automation_scheduler" / "historical_odds_sqlite.py").read_text(encoding="utf-8")
    line_owner = (REPO_ROOT / "automation_scheduler" / "historical_line_movement.py").read_text(encoding="utf-8")
    dashboard_data = (REPO_ROOT / "automation_scheduler" / "streamlit_dashboard_data.py").read_text(encoding="utf-8")

    for token in ("source_imports", "historical_events", "historical_odds", "historical_results"):
        assert token in sqlite_owner
    assert "historical_line_snapshots" in line_owner
    assert 'DEFAULT_HISTORICAL_SQLITE_PATH = Path("data/historical/historical_odds.db")' in dashboard_data
    assert "connect_historical_odds_db" in dashboard_data
    assert "Existing sports SQLite flow was not replaced" in report
    assert "data/historical/historical_odds.db" in report


def test_duplicate_storage_owners_are_reported_not_deleted() -> None:
    text = _read_report()
    required_owner_mentions = [
        "data/bets.csv",
        "data/bet_log.jsonl",
        "data/paper_ledger/paper_ledger.json",
        "data/paper_ledger/latest.json",
        "data/review_queue/latest.json",
        "data/outcomes/latest.json",
        "data/collector_scheduler",
        "experiment_history_runs",
        "historical_line_snapshots",
        "Duplicate storage owners are tracked, not deleted",
        "Candidate for deletion after migration tests",
    ]
    for expected in required_owner_mentions:
        assert expected in text


def test_phase10k3_report_does_not_claim_forbidden_overreach() -> None:
    text = _read_report()

    # Positive overreach claims are forbidden. Negative guardrail statements such
    # as "No CSV paths were deleted" are required and should remain allowed.
    forbidden_positive_claims = [
        "Migration was executed in this phase",
        "Vendor connectors were added",
        "Prediction testing was started",
        "Streamlit main menu was altered",
        "0DTE model was implemented",
    ]
    for forbidden in forbidden_positive_claims:
        assert forbidden not in text

    required_negative_guardrails = [
        "No runtime files were deleted",
        "No CSV paths were deleted",
        "Existing sports SQLite flow was not replaced",
    ]
    for required in required_negative_guardrails:
        assert required in text

"""Phase 10K2 sports odds snapshot pipeline foundation tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPO_ROOT / "PHASE10K2_SPORTS_ODDS_SNAPSHOT_PIPELINE_MAP.md"


def _read_report() -> str:
    return REPORT_PATH.read_text(encoding="utf-8")


def test_phase10k2_report_exists_and_contains_required_strings() -> None:
    text = _read_report()
    required_strings = [
        "Sports Odds Snapshot Pipeline Map",
        "Cross-Sport Line Movement Foundation",
        "not NFL-only",
        "append-only timestamped snapshots",
        "no overwriting line history",
        "decision_line = latest snapshot at or before simulated decision time",
        "closing_line is evaluation-only unless decision time is closing time",
        "no future odds leakage",
        "Existing Owner Validation",
        "Do not assume existing owners work correctly",
        "Raw Snapshot Field Contract",
        "Line Movement Path Features",
        "Cross-Sport Coverage",
        "American sports",
        "soccer",
        "tennis",
        "top liquidity sports",
        "Main markets first",
        "moneyline",
        "spread",
        "total",
        "Props later",
        "book_consensus",
        "best_available_line",
        "best_available_price",
        "movement_count",
        "largest_swing",
        "Do not add vendor connectors",
        "Do not start prediction testing",
    ]
    for expected in required_strings:
        assert expected in text


def test_phase10k2_report_contains_required_sections() -> None:
    text = _read_report()
    required_sections = [
        "## A. Executive Summary",
        "## B. Existing Owner Validation",
        "## C. Cross-Sport Coverage",
        "## D. Raw Snapshot Field Contract",
        "## E. Append-Only Storage Rule",
        "## F. Line Movement Path Features",
        "## G. Decision-Time Leakage Protection",
        "## H. Main Markets First / Props Later",
        "## I. Warehouse Compatibility",
        "## J. No-Duplicate Decisions",
        "## K. Testing Plan",
        "## L. Next Phase Impact",
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


def test_existing_asof_owner_excludes_future_snapshots() -> None:
    from src.automation_scheduler_legacy.asof_line_movement_query import select_latest_asof_snapshots

    snapshots = [
        {
            "snapshot_id": "before",
            "event_id": "event-1",
            "bookmaker": "BookA",
            "market_family": "spread",
            "market": "spread",
            "selection": "home",
            "line_value": -2.5,
            "snapshot_time": "2026-01-01T10:00:00Z",
        },
        {
            "snapshot_id": "after",
            "event_id": "event-1",
            "bookmaker": "BookA",
            "market_family": "spread",
            "market": "spread",
            "selection": "home",
            "line_value": -4.5,
            "snapshot_time": "2026-01-01T12:01:00Z",
        },
    ]

    result = select_latest_asof_snapshots(
        snapshots,
        hypothetical_bet_time="2026-01-01T12:00:00Z",
        event_id="event-1",
    )

    assert result["ok"] is True
    assert result["available_snapshots"] == 1
    assert result["excluded_counts"]["future_filtered"] == 1
    assert result["latest_snapshots"][0]["snapshot_id"] == "before"


def test_backend_snapshot_modules_have_no_streamlit_or_live_connector_imports() -> None:
    module_paths = [
        REPO_ROOT / "src" / "research" / "storage.py",
        REPO_ROOT / "src" / "research" / "__init__.py",
        REPO_ROOT / "src" / "automation_scheduler_legacy" / "historical_line_movement.py",
        REPO_ROOT / "src" / "automation_scheduler_legacy" / "line_movement_import_contract.py",
        REPO_ROOT / "src" / "automation_scheduler_legacy" / "asof_line_movement_query.py",
    ]
    forbidden_tokens = [
        "import streamlit",
        "from streamlit",
        "requests.",
        "import requests",
        "httpx.",
        "import httpx",
        "selenium",
        "BeautifulSoup",
    ]
    for path in module_paths:
        content = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in content, f"{token!r} found in {path}"


def test_raw_sports_odds_schema_alignment_gap_is_documented(tmp_path: Path) -> None:
    from src.research.storage import initialize_market_research_db

    db_path = tmp_path / "market_research.db"
    initialize_market_research_db(db_path)

    conn = sqlite3.connect(str(db_path))
    try:
        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(raw_sports_odds)").fetchall()
        }
    finally:
        conn.close()

    timestamped_snapshot_basics = {
        "sport",
        "league",
        "event_id",
        "market",
        "selection",
        "odds_american",
        "implied_probability",
        "observed_at",
        "source_key",
        "source_name",
        "source_file",
        "inserted_at",
    }
    for field in timestamped_snapshot_basics:
        assert field in columns

    deferred_contract_fields = {"market_id", "book", "side", "line"}
    assert deferred_contract_fields - columns == deferred_contract_fields

    report = _read_report()
    assert "Schema expansion deferred" in report
    for field in sorted(deferred_contract_fields):
        assert field in report


def test_no_forbidden_phase10k2_overreach_text_in_report() -> None:
    text = _read_report()
    forbidden_claims = [
        "live odds ingestion was added",
        "player prop importer was added",
        "prediction testing was started",
        "0DTE model was implemented",
        "Streamlit main menu was changed",
    ]
    for forbidden in forbidden_claims:
        assert forbidden not in text


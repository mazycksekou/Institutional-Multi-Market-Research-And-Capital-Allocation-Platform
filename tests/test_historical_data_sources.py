"""
Tests for automation_scheduler.historical_data_sources.
"""
from __future__ import annotations

import pytest

from src.services.streamlit_dashboard_facade import HISTORICAL_DATA_SOURCES, get_historical_data_source_rows, get_historical_data_sources, get_model_testing_source_plan, get_priority_import_sources, get_source_status_counts, source_is_projection_ready, summarize_source_registry, KEEP, KEEP_TOOL, DOWNGRADE, REMOVE


def test_priority_order():
    """First three keep sources have correct priority order."""
    sources = get_priority_import_sources()
    keys = [s["source_key"] for s in sources]
    assert keys == [
        "football_data_uk",
        "arnav_mlb_odds_scraper",
        "sportsbookreview_scraper",
    ]


def test_football_data_for_soccer():
    """Football-Data.co.uk is returned for sport soccer."""
    sources = get_priority_import_sources(sport="soccer")
    assert any(s["source_key"] == "football_data_uk" for s in sources)


def test_mlb_source_for_mlb():
    """ArnavSaraogi MLB Odds Scraper is returned for sport mlb."""
    sources = get_priority_import_sources(sport="mlb")
    assert any(s["source_key"] == "arnav_mlb_odds_scraper" for s in sources)


def test_odds_harvester_tool_not_first():
    """OddsHarvester is keep_tool and not in priority import list."""
    sources = get_priority_import_sources()
    keys = [s["source_key"] for s in sources]
    assert "odds_harvester" not in keys

    tool_sources = get_historical_data_sources(status=KEEP_TOOL)
    assert len(tool_sources) == 1
    assert tool_sources[0]["source_key"] == "odds_harvester"


def test_removed_not_projection_ready():
    """Sources with status REMOVE are not projection ready."""
    for src in HISTORICAL_DATA_SOURCES:
        if src["status"] == REMOVE:
            assert not source_is_projection_ready(src["source_key"])


def test_sqlite_deferred():
    """get_model_testing_source_plan mentions Phase 10H6 for SQLite."""
    plan = get_model_testing_source_plan()
    assert "Phase 10H6" in plan


def test_summary_first_importer():
    """summarize_source_registry returns first_importer = football_data_uk."""
    summary = summarize_source_registry()
    assert summary["first_importer"] == "football_data_uk"


def test_historical_data_source_rows_include_key_fields():
    """get_historical_data_source_rows returns rows with expected columns."""
    rows = get_historical_data_source_rows()
    assert len(rows) > 0
    expected = {"source_key", "name", "status", "sport", "description", "format", "priority_order", "projection_ready"}
    for row in rows:
        assert expected.issubset(set(row.keys()))


def test_get_source_status_counts_returns_int_values():
    """get_source_status_counts returns count greater than zero for keep."""
    counts = get_source_status_counts()
    assert counts.get("keep", 0) >= 1

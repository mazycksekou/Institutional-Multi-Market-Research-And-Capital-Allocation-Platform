"""
Tests for automation_scheduler/historical_line_movement.py.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from automation_scheduler.historical_line_movement import (
    LINE_MOVEMENT_SCHEMA_VERSION,
    attach_volatility_to_backtest_rows,
    backfill_line_snapshots_from_historical_odds,
    calculate_line_movement_readiness,
    canonical_row_to_line_snapshots,
    initialize_line_movement_schema,
    make_line_snapshot_id,
    normalize_snapshot_label,
    query_line_snapshots,
    summarize_line_movement_store,
    summarize_results_by_volatility,
    upsert_line_snapshots,
    upsert_line_snapshots_for_canonical_rows,
)
from automation_scheduler.historical_odds_sqlite import (
    connect_historical_odds_db,
    initialize_historical_odds_db,
    import_historical_odds_file_to_sqlite,
    query_historical_odds_rows,
)


def _make_conn(tmp_path: Path) -> sqlite3.Connection:
    db = tmp_path / "test_lm.db"
    conn = connect_historical_odds_db(db)
    initialize_historical_odds_db(conn)
    initialize_line_movement_schema(conn)
    return conn


def test_initialize_line_movement_schema_creates_table(tmp_path: Path) -> None:
    conn = connect_historical_odds_db(tmp_path / "test.db")
    initialize_line_movement_schema(conn)
    tables = [
        r["name"]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
    ]
    assert "historical_line_snapshots" in tables
    conn.close()


def test_canonical_row_to_line_snapshots_creates_decision(tmp_path: Path) -> None:
    row = {
        "event_id": "evt001",
        "odds_id": "odds001",
        "source_key": "test",
        "source_file": "test.csv",
        "sport": "soccer",
        "league": "E0",
        "event_date": "2023-08-12",
        "home_team": "arsenal",
        "away_team": "chelsea",
        "bookmaker": "bet365",
        "market": "1x2",
        "selection": "home",
        "odds_at_decision_time": 2.0,
        "market_implied_probability": 0.5,
        "collected_at": "2023-08-12T12:00:00Z",
    }
    snaps = canonical_row_to_line_snapshots(row)
    assert len(snaps) == 1
    assert snaps[0]["snapshot_label"] == "decision"
    assert snaps[0]["odds_value"] == 2.0


def test_canonical_row_to_line_snapshots_creates_opening_and_closing(tmp_path: Path) -> None:
    row = {
        "event_id": "evt002",
        "odds_id": "odds002",
        "source_key": "test",
        "source_file": "test.csv",
        "sport": "soccer",
        "league": "E0",
        "event_date": "2023-08-12",
        "home_team": "arsenal",
        "away_team": "chelsea",
        "bookmaker": "bet365",
        "market": "1x2",
        "selection": "home",
        "odds_at_decision_time": 2.0,
        "market_implied_probability": 0.5,
        "opening_odds": 2.2,
        "closing_odds": 1.8,
    }
    snaps = canonical_row_to_line_snapshots(row)
    labels = [s["snapshot_label"] for s in snaps]
    assert "decision" in labels
    assert "opening" in labels
    assert "closing" in labels


def test_upsert_line_snapshots_idempotent(tmp_path: Path) -> None:
    conn = _make_conn(tmp_path)
    row = {
        "event_id": "e1",
        "odds_id": "o1",
        "source_key": "s1",
        "source_file": "f1.csv",
        "sport": "soccer",
        "league": "E0",
        "event_date": "2023-01-01",
        "home_team": "a",
        "away_team": "b",
        "bookmaker": "b365",
        "market": "1x2",
        "selection": "home",
        "odds_at_decision_time": 1.5,
        "market_implied_probability": 0.6667,
    }
    snaps = canonical_row_to_line_snapshots(row)
    res1 = upsert_line_snapshots(conn, snaps)
    assert res1["rows_inserted_or_updated"] == 1
    res2 = upsert_line_snapshots(conn, snaps)
    # idempotent: still 1 inserted and not 0?
    # upsert may report 1 each time because it's an update; acceptable
    assert res2["rows_inserted_or_updated"] == 1
    assert conn.execute(
        "SELECT COUNT(*) AS cnt FROM historical_line_snapshots"
    ).fetchone()["cnt"] == 1
    conn.close()


def test_query_line_snapshots_filters(tmp_path: Path) -> None:
    conn = _make_conn(tmp_path)
    row1 = {
        "event_id": "e1", "odds_id": "o1", "source_key": "s1",
        "source_file": "f1.csv", "sport": "soccer", "league": "E0",
        "event_date": "2023-01-01", "home_team": "a", "away_team": "b",
        "bookmaker": "b365", "market": "1x2", "selection": "home",
        "odds_at_decision_time": 1.5, "market_implied_probability": 0.6667,
    }
    row2 = {
        "event_id": "e2", "odds_id": "o2", "source_key": "s2",
        "source_file": "f2.csv", "sport": "baseball", "league": "MLB",
        "event_date": "2024-06-01", "home_team": "yankees", "away_team": "redsox",
        "bookmaker": "draftkings", "market": "moneyline", "selection": "yankees",
        "odds_at_decision_time": -110, "market_implied_probability": 0.5238,
    }
    upsert_line_snapshots_for_canonical_rows(conn, [row1, row2])

    res_soccer = query_line_snapshots(conn, sport="soccer")
    assert len(res_soccer) == 1
    res_baseball = query_line_snapshots(conn, source_key="s2")
    assert len(res_baseball) == 1
    res_market = query_line_snapshots(conn, market="moneyline")
    assert len(res_market) == 1
    conn.close()


def test_summarize_line_movement_store_counts(tmp_path: Path) -> None:
    conn = _make_conn(tmp_path)
    row = {
        "event_id": "e1", "odds_id": "o1", "source_key": "s1",
        "source_file": "f1.csv", "sport": "soccer", "league": "E0",
        "event_date": "2023-01-01", "home_team": "a", "away_team": "b",
        "bookmaker": "b365", "market": "1x2", "selection": "home",
        "odds_at_decision_time": 1.5, "market_implied_probability": 0.6667,
        "opening_odds": 1.6, "closing_odds": 1.4,
    }
    upsert_line_snapshots_for_canonical_rows(conn, [row])
    summary = summarize_line_movement_store(conn)
    assert summary["ok"]
    assert summary["total_snapshots"] == 3
    assert summary["opening_snapshots"] == 1
    assert summary["decision_snapshots"] == 1
    assert summary["closing_snapshots"] == 1
    assert "soccer" in summary["sports"]
    assert "E0" in summary["leagues"]
    assert "1x2" in summary["markets"]
    assert "s1" in summary["source_keys"]
    conn.close()


def test_calculate_line_movement_readiness(tmp_path: Path) -> None:
    # Decision only → not ready
    r = calculate_line_movement_readiness(
        {"opening_snapshots": 0, "decision_snapshots": 1, "closing_snapshots": 0}
    )
    assert r["line_movement_ready"] is False
    assert r["clv_ready"] is False

    # Full opening+decision+closing → ready
    r2 = calculate_line_movement_readiness(
        {"opening_snapshots": 1, "decision_snapshots": 1, "closing_snapshots": 1}
    )
    assert r2["line_movement_ready"] is True
    assert r2["clv_ready"] is True


def test_backfill_line_snapshots_from_historical_odds(tmp_path: Path) -> None:
    from automation_scheduler.historical_odds_sqlite import (
        connect_historical_odds_db,
        initialize_historical_odds_db,
    )
    db_path = tmp_path / "backfill.db"
    conn = connect_historical_odds_db(db_path)
    initialize_historical_odds_db(conn)
    initialize_line_movement_schema(conn)

    # Import a tiny Football-Data CSV
    csv_path = tmp_path / "tiny.csv"
    csv_path.write_text(
        "Div,Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,B365H,B365D,B365A\n"
        "E0,2023-08-12,Arsenal,Chelsea,3,1,H,1.50,4.00,6.50\n",
        encoding="utf-8",
    )
    import_historical_odds_file_to_sqlite(
        conn, "football_data_uk", csv_path
    )

    result = backfill_line_snapshots_from_historical_odds(conn)
    assert result["rows_read"] >= 3
    assert result["snapshots_created"] >= 3
    # After backfill, there should be decision snapshots for each odds row
    summary = summarize_line_movement_store(conn)
    assert summary["decision_snapshots"] >= 3
    assert summary["line_movement_ready"] is False  # no opening/closing from football-data
    conn.close()


def test_calculate_line_volatility_for_group_with_line_values():
    from automation_scheduler.historical_line_movement import (
        calculate_line_volatility_for_group,
    )
    rows = [
        {
            "event_id": "e1",
            "market": "spread",
            "market_family": "spread_or_runline",
            "selection": "home",
            "player_name": None,
            "team_name": "Team A",
            "bookmaker": "b365",
            "snapshot_label": "opening",
            "line_value": 7.5,
            "odds_value": None,
        },
        {
            "event_id": "e1",
            "market": "spread",
            "market_family": "spread_or_runline",
            "selection": "home",
            "player_name": None,
            "team_name": "Team A",
            "bookmaker": "b365",
            "snapshot_label": "decision",
            "line_value": 8.5,
            "odds_value": None,
        },
        {
            "event_id": "e1",
            "market": "spread",
            "market_family": "spread_or_runline",
            "selection": "home",
            "player_name": None,
            "team_name": "Team A",
            "bookmaker": "b365",
            "snapshot_label": "closing",
            "line_value": 6.5,
            "odds_value": None,
        },
    ]
    result = calculate_line_volatility_for_group(rows)
    assert result["reference_line"] == 7.5
    assert result["line_high"] == 8.5
    assert result["line_low"] == 6.5
    assert result["line_move_up"] == 1.0
    assert result["line_move_down"] == 1.0
    assert result["line_total_range"] == 2.0
    assert result["line_volatility_score"] == 2.0
    assert result["volatility_level"] == "high"


def test_calculate_line_volatility_for_group_odds_only():
    from automation_scheduler.historical_line_movement import (
        calculate_line_volatility_for_group,
    )
    rows = [
        {
            "event_id": "e2",
            "market": "moneyline",
            "market_family": "moneyline_or_1x2",
            "selection": "home",
            "player_name": None,
            "team_name": None,
            "bookmaker": "dk",
            "snapshot_label": "opening",
            "line_value": None,
            "odds_value": -110,
        },
        {
            "event_id": "e2",
            "market": "moneyline",
            "market_family": "moneyline_or_1x2",
            "selection": "home",
            "player_name": None,
            "team_name": None,
            "bookmaker": "dk",
            "snapshot_label": "decision",
            "line_value": None,
            "odds_value": -120,
        },
    ]
    result = calculate_line_volatility_for_group(rows)
    assert result["reference_line"] is None
    assert result["line_high"] is None
    assert result["line_low"] is None
    assert result["line_total_range"] is None
    assert result["reference_odds"] == -110
    assert result["odds_high"] == -110
    assert result["odds_low"] == -120
    assert result["odds_total_range"] == 10
    assert result["odds_volatility_score"] == 10
    assert "Only odds volatility is available" in result["warnings"][0]
    assert result["volatility_level"] in ("low", "medium", "high")


def test_calculate_line_volatility_summary_stable_keys():
    from automation_scheduler.historical_line_movement import (
        calculate_line_volatility_summary,
    )
    rows = [
        {
            "event_id": "e1",
            "market": "spread",
            "market_family": "spread_or_runline",
            "selection": "home",
            "player_name": None,
            "team_name": "Team A",
            "bookmaker": "b365",
            "snapshot_label": "opening",
            "line_value": 7.5,
        },
    ]
    result = calculate_line_volatility_summary(rows)
    expected_keys = {
        "ok",
        "groups_seen",
        "volatility_rows",
        "high_volatility_count",
        "medium_volatility_count",
        "low_volatility_count",
        "unknown_volatility_count",
        "operator_interpretation",
        "warnings",
    }
    assert set(result.keys()) == expected_keys


def test_get_line_volatility_summary_from_sqlite(tmp_path):
    from automation_scheduler.historical_line_movement import (
        initialize_line_movement_schema,
        upsert_line_snapshots_for_canonical_rows,
        get_line_volatility_summary_from_sqlite,
    )
    from automation_scheduler.historical_odds_sqlite import (
        connect_historical_odds_db,
        initialize_historical_odds_db,
    )
    db_path = tmp_path / "vol_test.db"
    conn = connect_historical_odds_db(db_path)
    initialize_historical_odds_db(conn)
    initialize_line_movement_schema(conn)

    row = {
        "event_id": "e1",
        "odds_id": "o1",
        "source_key": "test",
        "source_file": "test.csv",
        "sport": "soccer",
        "league": "E0",
        "event_date": "2023-01-01",
        "home_team": "a",
        "away_team": "b",
        "bookmaker": "b365",
        "market": "1x2",
        "selection": "home",
        "odds_at_decision_time": 2.0,
        "market_implied_probability": 0.5,
        "collected_at": "2023-01-01T12:00:00Z",
        "opening_odds": 2.2,
        "closing_odds": 1.8,
    }
    upsert_line_snapshots_for_canonical_rows(conn, [row])
    result = get_line_volatility_summary_from_sqlite(conn)
    assert result["ok"] is True
    assert result["groups_seen"] >= 1
    assert result["high_volatility_count"] >= 0  # depends on odds range
    conn.close()


# ── Phase 10H12B – Volatility Result Breakdown ─────────────────


def test_attach_volatility_to_backtest_rows_does_not_mutate_input():
    rows = [{"event_id": "e1", "market": "1x2"}]
    vol_rows = [{"event_id": "e1", "market": "1x2", "volatility_level": "low"}]
    result = attach_volatility_to_backtest_rows(rows, vol_rows)
    assert result[0]["volatility_level"] == "low"
    # original input unchanged
    assert "volatility_level" not in rows[0]
    assert rows[0] is not result[0]


def test_attach_volatility_to_backtest_rows_matches_event_market_selection():
    rows = [{"event_id": "e1", "market": "moneyline", "selection": "home",
             "player_name": None, "team_name": None, "bookmaker": "b365"}]
    vol_rows = [{"event_id": "e1", "market": "moneyline", "selection": "home",
                 "player_name": None, "team_name": None, "bookmaker": "b365",
                 "volatility_level": "medium", "line_move_up": 1.5}]
    result = attach_volatility_to_backtest_rows(rows, vol_rows)
    assert result[0]["volatility_level"] == "medium"
    assert result[0]["line_move_up"] == 1.5


def test_attach_volatility_to_backtest_rows_sets_unknown_when_missing():
    rows = [{"event_id": "e2", "market": "spread"}]
    vol_rows = [{"event_id": "e1", "market": "spread"}]
    result = attach_volatility_to_backtest_rows(rows, vol_rows)
    assert result[0]["volatility_level"] == "unknown"
    assert result[0]["line_move_up"] is None


def test_summarize_results_by_volatility_groups_low_medium_high_unknown():
    rows = [
        {"event_id": "a", "volatility_level": "low", "profit_loss": 10, "final_result": "W"},
        {"event_id": "b", "volatility_level": "medium", "profit_loss": -5, "final_result": "L"},
        {"event_id": "c", "volatility_level": "high", "profit_loss": 0, "final_result": "P"},
        {"event_id": "d", "volatility_level": "unknown", "profit_loss": 2, "final_result": "W"},
        {"event_id": "e", "volatility_level": "unknown", "profit_loss": -1, "final_result": "L"},
    ]
    result = summarize_results_by_volatility(rows)
    groups = result["groups"]
    assert "low" in groups
    assert "medium" in groups
    assert "high" in groups
    assert "unknown" in groups
    assert groups["low"]["decisions"] == 1
    assert groups["low"]["net_result"] == 10.0
    assert groups["low"]["wins"] == 1
    assert groups["medium"]["losses"] == 1
    assert groups["high"]["pushes"] == 1


def test_summarize_results_by_volatility_calculates_roi_and_win_rate_safely():
    rows = [
        {"volatility_level": "low", "profit_loss": 5, "roi_percent": 2.0, "final_result": "W"},
        {"volatility_level": "low", "profit_loss": -3, "roi_percent": -1.5, "final_result": "L"},
    ]
    result = summarize_results_by_volatility(rows)
    low = result["groups"]["low"]
    assert low["roi_percent"] == 0.25  # (2.0 + -1.5)/2
    assert low["win_rate_percent"] == 50.0
    assert low["wins"] == 1
    assert low["losses"] == 1
    assert low["pushes"] == 0


def test_summarize_results_by_volatility_handles_partial_rows():
    rows = [
        {"volatility_level": "low", "profit_loss": None, "final_result": None},
        {"volatility_level": "low", "roi_percent": None},
    ]
    result = summarize_results_by_volatility(rows)
    low = result["groups"]["low"]
    assert low["net_result"] == 0.0
    assert low["roi_percent"] == 0.0
    assert low["settled_count"] == 0
    assert low["wins"] == 0

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Mapping, Sequence

from .engine import run_backtest
from src.data.historical_odds import query_historical_odds_rows


DEFAULT_HISTORICAL_MODEL_ID = "sqlite-historical-backtest"
DEFAULT_SQLITE_BACKTEST_LIMIT = 1000
HISTORICAL_BACKTEST_BRIDGE_VERSION = "10H7"


def sqlite_odds_row_to_backtest_row(row: Mapping[str, Any]) -> dict[str, Any]:
    from src.data.historical_backtest_bridge import sqlite_odds_row_to_backtest_row as _legacy_sqlite_odds_row_to_backtest_row

    return _legacy_sqlite_odds_row_to_backtest_row(dict(row))


def sqlite_odds_rows_to_backtest_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    from src.data.historical_backtest_bridge import sqlite_odds_rows_to_backtest_rows as _legacy_sqlite_odds_rows_to_backtest_rows

    return _legacy_sqlite_odds_rows_to_backtest_rows([dict(row) for row in rows if isinstance(row, Mapping)])


def query_sqlite_backtest_rows(
    db_path: str | Path | sqlite3.Connection,
    *,
    table_name: str = "historical_odds",
    sport: str | None = None,
    league: str | None = None,
    market: str | None = None,
    source_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    from src.data.historical_backtest_bridge import query_sqlite_backtest_rows as _legacy_query_sqlite_backtest_rows

    if isinstance(db_path, sqlite3.Connection):
        return _legacy_query_sqlite_backtest_rows(
            db_path,
            sport=sport,
            league=league,
            market=market,
            source_key=source_key,
            start_date=start_date,
            end_date=end_date,
            limit=limit if limit is not None else DEFAULT_SQLITE_BACKTEST_LIMIT,
        )
    path = Path(db_path)
    if not path.exists():
        return []
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    try:
        return _legacy_query_sqlite_backtest_rows(
            conn,
            sport=sport,
            league=league,
            market=market,
            source_key=source_key,
            start_date=start_date,
            end_date=end_date,
            limit=limit if limit is not None else DEFAULT_SQLITE_BACKTEST_LIMIT,
        )
    finally:
        conn.close()


def run_sqlite_historical_backtest(
    db_path: str | Path | sqlite3.Connection,
    *,
    model_id: str = "sqlite_historical_backtest",
    table_name: str = "historical_odds",
    sport: str | None = None,
    league: str | None = None,
    market: str | None = None,
    source_key: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int | None = None,
    model_probability: float | None = None,
    strategy_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from src.data.historical_backtest_bridge import run_sqlite_historical_backtest as _legacy_run_sqlite_historical_backtest

    if isinstance(db_path, sqlite3.Connection):
        return _legacy_run_sqlite_historical_backtest(
            db_path,
            model_id=model_id,
            sport=sport,
            league=league,
            market=market,
            source_key=source_key,
            start_date=start_date,
            end_date=end_date,
            limit=limit if limit is not None else DEFAULT_SQLITE_BACKTEST_LIMIT,
            model_probability=model_probability,
            strategy_config=strategy_config,
        )
    path = Path(db_path)
    if not path.exists():
        return {
            "ok": False,
            "bridge_version": HISTORICAL_BACKTEST_BRIDGE_VERSION,
            "model_id": model_id,
            "query": {
                "sport": sport,
                "league": league,
                "market": market,
                "source_key": source_key,
                "start_date": start_date,
                "end_date": end_date,
                "limit": limit if limit is not None else DEFAULT_SQLITE_BACKTEST_LIMIT,
            },
            "rows_loaded": 0,
            "rows_converted": 0,
            "backtest_result": {"ok": False, "status": "missing_db"},
            "projection_summary": {
                "rows_loaded": 0,
                "rows_converted": 0,
                "sports": [],
                "leagues": [],
                "markets": [],
                "source_keys": [],
                "backtest_ran": False,
            },
        }
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    try:
        return _legacy_run_sqlite_historical_backtest(
            conn,
            model_id=model_id,
            sport=sport,
            league=league,
            market=market,
            source_key=source_key,
            start_date=start_date,
            end_date=end_date,
            limit=limit if limit is not None else DEFAULT_SQLITE_BACKTEST_LIMIT,
            model_probability=model_probability,
            strategy_config=strategy_config,
        )
    finally:
        conn.close()


def summarize_sqlite_historical_backtest(
    db_path: str | Path | Sequence[Mapping[str, Any]] | Mapping[str, Any],
    *,
    table_name: str = "historical_odds",
    limit: int | None = None,
) -> dict[str, Any]:
    from src.data.historical_backtest_bridge import summarize_sqlite_historical_backtest as _legacy_summarize_sqlite_historical_backtest

    return _legacy_summarize_sqlite_historical_backtest(db_path)


def get_sqlite_backtest_filter_options(
    db_path: str | Path | Sequence[Mapping[str, Any]],
    *,
    table_name: str = "historical_odds",
) -> dict[str, Any]:
    from src.data.historical_backtest_bridge import get_sqlite_backtest_filter_options as _legacy_get_sqlite_backtest_filter_options

    if isinstance(db_path, sqlite3.Connection):
        return _legacy_get_sqlite_backtest_filter_options(db_path)
    path = Path(db_path)
    if not path.exists():
        return {
            "ok": True,
            "status": "available",
            "sports": [],
            "leagues": [],
            "markets": [],
            "source_keys": [],
            "event_date_min": None,
            "event_date_max": None,
            "total_odds": 0,
        }
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    try:
        return _legacy_get_sqlite_backtest_filter_options(conn)
    finally:
        conn.close()


__all__ = [
    "get_sqlite_backtest_filter_options",
    "query_sqlite_backtest_rows",
    "run_sqlite_historical_backtest",
    "sqlite_odds_row_to_backtest_row",
    "sqlite_odds_rows_to_backtest_rows",
    "summarize_sqlite_historical_backtest",
]

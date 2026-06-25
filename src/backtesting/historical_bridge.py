from __future__ import annotations

from importlib import import_module
from typing import Any


def _legacy() -> Any:
    return import_module("automation_scheduler.historical_backtest_bridge")


def sqlite_odds_row_to_backtest_row(*args: Any, **kwargs: Any) -> Any:
    return _legacy().sqlite_odds_row_to_backtest_row(*args, **kwargs)


def sqlite_odds_rows_to_backtest_rows(*args: Any, **kwargs: Any) -> Any:
    return _legacy().sqlite_odds_rows_to_backtest_rows(*args, **kwargs)


def query_sqlite_backtest_rows(*args: Any, **kwargs: Any) -> Any:
    return _legacy().query_sqlite_backtest_rows(*args, **kwargs)


def run_sqlite_historical_backtest(*args: Any, **kwargs: Any) -> Any:
    return _legacy().run_sqlite_historical_backtest(*args, **kwargs)


def summarize_sqlite_historical_backtest(*args: Any, **kwargs: Any) -> Any:
    return _legacy().summarize_sqlite_historical_backtest(*args, **kwargs)


def get_sqlite_backtest_filter_options(*args: Any, **kwargs: Any) -> Any:
    return _legacy().get_sqlite_backtest_filter_options(*args, **kwargs)


__all__ = [
    "get_sqlite_backtest_filter_options",
    "query_sqlite_backtest_rows",
    "run_sqlite_historical_backtest",
    "sqlite_odds_row_to_backtest_row",
    "sqlite_odds_rows_to_backtest_rows",
    "summarize_sqlite_historical_backtest",
]


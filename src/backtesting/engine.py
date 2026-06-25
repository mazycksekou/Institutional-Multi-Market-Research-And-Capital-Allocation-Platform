from __future__ import annotations

from importlib import import_module
from typing import Any


def _legacy() -> Any:
    return import_module("automation_scheduler.backtesting_engine")


def run_backtesting_scaffold(*args: Any, **kwargs: Any) -> Any:
    return _legacy().run_backtesting_scaffold(*args, **kwargs)


def load_historical_rows(*args: Any, **kwargs: Any) -> Any:
    return _legacy().load_historical_rows(*args, **kwargs)


def replay_rows(*args: Any, **kwargs: Any) -> Any:
    return _legacy().replay_rows(*args, **kwargs)


def run_backtest(*args: Any, **kwargs: Any) -> Any:
    return _legacy().run_backtest(*args, **kwargs)


__all__ = [
    "load_historical_rows",
    "replay_rows",
    "run_backtest",
    "run_backtesting_scaffold",
]


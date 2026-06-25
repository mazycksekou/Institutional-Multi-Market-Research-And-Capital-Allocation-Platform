from __future__ import annotations

from importlib import import_module
from typing import Any


def _legacy() -> Any:
    return import_module("automation_scheduler.backtest_strategy_profiles")


def normalize_strategy_profile_key(*args: Any, **kwargs: Any) -> Any:
    return _legacy().normalize_strategy_profile_key(*args, **kwargs)


def infer_strategy_profile_key_from_row(*args: Any, **kwargs: Any) -> Any:
    return _legacy().infer_strategy_profile_key_from_row(*args, **kwargs)


def build_strategy_config_for_row(*args: Any, **kwargs: Any) -> Any:
    return _legacy().build_strategy_config_for_row(*args, **kwargs)


def describe_regression_profiles(*args: Any, **kwargs: Any) -> Any:
    return _legacy().describe_regression_profiles(*args, **kwargs)


__all__ = [
    "build_strategy_config_for_row",
    "describe_regression_profiles",
    "infer_strategy_profile_key_from_row",
    "normalize_strategy_profile_key",
]


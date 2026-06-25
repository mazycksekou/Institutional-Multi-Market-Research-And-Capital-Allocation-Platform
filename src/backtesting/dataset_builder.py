from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any, Iterable, Mapping

PAPER_ONLY_FIXTURE_REQUIRED_FIELDS: tuple[str, ...] = (
    "fixture_id",
    "sport_or_market",
    "event_id",
    "prediction_target",
    "selection",
    "model_probability",
    "market_odds_american",
    "implied_probability",
    "expected_value",
    "stake_units",
    "bankroll_snapshot",
    "result_label",
    "outcome_known",
    "source_type",
    "execution_mode",
)

PAPER_ONLY_FIXTURE_OPTIONAL_FIELDS: tuple[str, ...] = (
    "rows_tested",
    "rows_valid",
    "rows_invalid",
    "missing_field_reasons",
    "warning_reasons",
)


def _legacy() -> Any:
    return import_module("automation_scheduler.backtest_dataset_builder")


def validate_paper_only_fixture_rows(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    return _legacy().validate_paper_only_fixture_rows(rows)


def build_canonical_backtest_dataset(*args: Any, **kwargs: Any) -> Any:
    return _legacy().build_canonical_backtest_dataset(*args, **kwargs)


def load_canonical_backtest_dataset(*args: Any, **kwargs: Any) -> Any:
    return _legacy().load_canonical_backtest_dataset(*args, **kwargs)


def summarize_canonical_dataset_report(*args: Any, **kwargs: Any) -> Any:
    return _legacy().summarize_canonical_dataset_report(*args, **kwargs)


__all__ = [
    "PAPER_ONLY_FIXTURE_OPTIONAL_FIELDS",
    "PAPER_ONLY_FIXTURE_REQUIRED_FIELDS",
    "build_canonical_backtest_dataset",
    "load_canonical_backtest_dataset",
    "summarize_canonical_dataset_report",
    "validate_paper_only_fixture_rows",
]

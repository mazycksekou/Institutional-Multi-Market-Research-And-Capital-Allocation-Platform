from __future__ import annotations

import importlib
import inspect
import os

import pytest


MODULE_NAMES = [
    "src.backtesting",
    "src.backtesting.contracts",
    "src.backtesting.datasets",
    "src.backtesting.leakage",
    "src.backtesting.replay",
    "src.backtesting.simulation",
]
FORBIDDEN_IMPORTS = [
    "requests",
    "httpx",
    "yfinance",
    "selenium",
    "playwright",
    "websocket",
    "openai",
    "anthropic",
    "alpaca",
    "robinhood",
    "ib_insync",
    "ccxt",
]


def test_backtesting_foundation_imports_safely(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        os,
        "getenv",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("import-time credential access is forbidden")),
    )

    modules = [importlib.reload(importlib.import_module(name)) for name in MODULE_NAMES]
    backtesting = modules[0]

    for name in [
        "BacktestDatasetContract",
        "ReplayPlanContract",
        "SimulationPlanContract",
        "build_backtest_dataset_contract",
        "validate_backtest_dataset_order",
        "detect_future_timestamps",
        "assert_no_future_timestamps",
        "build_replay_plan",
        "plan_replay_rows",
        "build_simulation_plan",
        "run_simulation_plan",
    ]:
        assert hasattr(backtesting, name), name


def test_backtesting_dataset_order_and_leakage_checks() -> None:
    from datetime import datetime, timedelta, timezone

    from src.backtesting.datasets import build_backtest_dataset_contract, validate_backtest_dataset_order
    from src.backtesting.leakage import assert_no_future_timestamps, detect_future_timestamps

    ordered_rows = [
        {"timestamp": "2026-01-01T00:00:00Z", "source_name": "local"},
        {"timestamp": "2026-01-01T00:05:00Z", "source_name": "local"},
    ]
    contract = build_backtest_dataset_contract(
        ordered_rows,
        dataset_name="sample-dataset",
        source_name="sample-source",
    )
    assert contract.dataset_name == "sample-dataset"
    assert contract.validate()["ok"] is True
    assert validate_backtest_dataset_order(ordered_rows)["ok"] is True

    unordered_rows = list(reversed(ordered_rows))
    unordered = validate_backtest_dataset_order(unordered_rows)
    assert unordered["ok"] is False
    assert "non_chronological_row_1" in unordered["errors"]

    future = datetime.now(timezone.utc) + timedelta(hours=1)
    future_report = detect_future_timestamps(
        [{"timestamp": future.isoformat(), "source_name": "local"}]
    )
    assert future_report["ok"] is False
    assert future_report["future_rows"][0]["timestamp_field"] == "timestamp"

    with pytest.raises(ValueError):
        assert_no_future_timestamps([{"timestamp": future.isoformat(), "source_name": "local"}])


def test_backtesting_replay_and_simulation_plans_are_local_only() -> None:
    from src.backtesting.datasets import build_backtest_dataset_contract
    from src.backtesting.replay import build_replay_plan, plan_replay_rows
    from src.backtesting.simulation import build_simulation_plan, run_simulation_plan

    rows = [
        {"timestamp": "2026-01-01T00:00:00Z", "source_name": "local", "event_id": "e1"},
        {"timestamp": "2026-01-01T00:05:00Z", "source_name": "local", "event_id": "e2"},
    ]
    contract = build_backtest_dataset_contract(rows, dataset_name="sample-dataset", source_name="sample-source")

    replay_plan = build_replay_plan(contract)
    assert replay_plan.local_only is True
    assert replay_plan.execution_enabled is False
    assert replay_plan.row_count == 2
    assert plan_replay_rows(rows, start_index=1) == [rows[1]]

    simulation_plan = build_simulation_plan(contract, strategy_name="preview")
    assert simulation_plan.local_only is True
    assert simulation_plan.execution_enabled is False
    assert simulation_plan.trade_execution_enabled is False
    result = run_simulation_plan(simulation_plan)
    assert result["trades_executed"] == 0
    assert result["execution_enabled"] is False


def test_backtesting_modules_do_not_import_network_or_secret_libraries() -> None:
    for name in MODULE_NAMES:
        module = importlib.import_module(name)
        source = inspect.getsource(module)
        lowered = source.lower()
        for token in FORBIDDEN_IMPORTS:
            assert token not in lowered, f"{token} found in {name}"
        assert "getenv" not in lowered, name

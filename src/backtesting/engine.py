"""Compatibility facade for the canonical backtesting engine.

Legacy test fixtures still refer to ``automation_scheduler.backtesting_engine``
and the old ``src/backtesting/engine.py`` entrypoint.  The executable logic
now lives in :mod:`src.backtesting.backtesting_engine`; this module only
forwards the public API.
"""

from __future__ import annotations

from src.backtesting.backtesting_engine import (
    compare_expected_vs_realized,
    generate_backtest_report,
    load_historical_rows,
    replay_rows,
    run_backtest,
    run_backtesting_scaffold,
    run_paper_summary,
    summarize_replay_result,
    write_replay_result,
)

__all__ = [
    "compare_expected_vs_realized",
    "generate_backtest_report",
    "load_historical_rows",
    "replay_rows",
    "run_backtest",
    "run_backtesting_scaffold",
    "run_paper_summary",
    "summarize_replay_result",
    "write_replay_result",
]

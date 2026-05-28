from __future__ import annotations

from .scheduler_runner import run_scheduler_once
from .system_health import get_system_health
from .review_queue import list_active_review_items
from .scheduler_config import get_default_scheduler_config, ensure_runtime_directories
from .backtesting_engine import generate_backtest_report, run_backtest, run_paper_summary
from .model_performance_report import build_compact_performance_report


def get_scheduler_health(base_data_dir: str | None = None):
    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    return get_system_health(config)


def get_scheduler_review_queue(base_data_dir: str | None = None):
    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    items = list_active_review_items(config)
    return {
        "ok": True,
        "count": len(items),
        "items": items,
        "human_approval_required": True,
        "auto_execution_enabled": False,
    }


def get_performance_health(base_data_dir: str | None = None):
    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    return get_system_health(config)


def run_performance_backtest(model_id: str, historical_rows_path: str | None = None, rows: list[dict] | None = None, base_data_dir: str | None = None):
    return generate_backtest_report(
        model_id=model_id,
        historical_rows_path=historical_rows_path,
        rows=rows,
        base_data_dir=base_data_dir or "data",
    )


def get_performance_report(model_id: str, historical_rows_path: str | None = None, rows: list[dict] | None = None, base_data_dir: str | None = None):
    result = generate_backtest_report(
        model_id=model_id,
        historical_rows_path=historical_rows_path,
        rows=rows,
        base_data_dir=base_data_dir or "data",
    )
    return result["compact_report"]


def get_paper_summary(base_data_dir: str | None = None):
    return run_paper_summary(base_data_dir=base_data_dir or "data")

from __future__ import annotations

import json
from pathlib import Path

from .scheduler_runner import run_scheduler_once
from .system_health import get_system_health
from .review_queue import filter_review_items, list_active_review_items, summarize_review_items
from .scheduler_config import get_default_scheduler_config, ensure_runtime_directories
from .backtesting_engine import generate_backtest_report, run_backtest, run_paper_summary
from .model_performance_report import build_compact_performance_report
from .provider_health import summarize_provider_health
from .provider_registry import get_provider_registry
from .sharp_sportsbook_adapter import SharpSportsbookAdapter
from .kalshi_readonly_adapter import KalshiReadonlyAdapter
from .kalshi_market_provider import (
    get_kalshi_snapshot,
    summarize_kalshi_snapshot,
    validate_kalshi_snapshot,
    write_kalshi_snapshot,
)
from .sportsbook_odds_provider import (
    get_sportsbook_snapshot,
    summarize_sportsbook_snapshot,
    validate_sportsbook_snapshot,
    write_sportsbook_snapshot,
)


def get_scheduler_health(base_data_dir: str | None = None):
    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    return get_system_health(config)


def get_scheduler_review_queue(
    base_data_dir: str | None = None,
    *,
    provider: str = "all",
    market_type: str = "all",
    reason: str | None = None,
    limit: int | None = None,
):
    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    items = list_active_review_items(config)
    filtered = filter_review_items(items, provider=provider, market_type=market_type, reason=reason)
    if isinstance(limit, int) and limit > 0:
        filtered = filtered[:limit]
    rejected_reason_counts: dict[str, int] = {}
    health_path = Path(config["paths"]["system_health"]) / "health.json"
    if health_path.exists():
        try:
            health_payload = json.loads(health_path.read_text(encoding="utf-8"))
            rejected_reason_counts = dict(health_payload.get("kalshi_rejected_reason_counts", {}))
        except Exception:
            rejected_reason_counts = {}
    summary = summarize_review_items(filtered, rejected_reason_counts=rejected_reason_counts)
    return {
        "ok": True,
        "status": "ok",
        "count": len(filtered),
        "items": filtered,
        "summary": summary,
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


def get_provider_health(base_data_dir: str | None = None):
    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    return summarize_provider_health(config["providers"])


def get_provider_registry_snapshot(base_data_dir: str | None = None):
    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    providers = list(get_provider_registry().values())
    blocked_count = sum(
        1
        for item in providers
        if (not bool(item.get("enabled", False))) or (not bool(item.get("live_calls_enabled", False)))
    )
    return {
        "ok": True,
        "status": "ok",
        "timestamp": None,
        "provider_count": len(providers),
        "enabled_provider_count": sum(1 for item in providers if item.get("enabled")),
        "live_calls_enabled_count": sum(1 for item in providers if item.get("live_calls_enabled")),
        "blocked_count": blocked_count,
        "dry_run": True,
        "blockers": ["dry_run_placeholder", "live_calls_disabled"],
        "providers": providers,
    }


def get_sharp_provider_health(base_data_dir: str | None = None):
    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    contract = dict(config["providers"].get("sharp_sportsbook", {}))
    adapter = SharpSportsbookAdapter(contract)
    payload = adapter.health_check()
    return summarize_sportsbook_snapshot(payload)


def run_sharp_provider_snapshot(base_data_dir: str | None = None, write_snapshot: bool = True):
    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    contract = dict(config["providers"].get("sharp_sportsbook", {}))
    adapter = SharpSportsbookAdapter(contract)
    snapshot = get_sportsbook_snapshot(adapter)
    validation = validate_sportsbook_snapshot(snapshot)
    snapshot_path = None
    if write_snapshot and int(snapshot.get("records_received", 0)) > 0:
        snapshot_path = write_sportsbook_snapshot(snapshot, base_data_dir=base_data_dir or "data")
    summary = summarize_sportsbook_snapshot(snapshot, snapshot_path=snapshot_path)
    summary["validation_status"] = validation["status"]
    summary["validation_errors"] = validation["errors"][:10]
    return summary


def get_kalshi_provider_health(base_data_dir: str | None = None):
    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    contract = dict(config["providers"].get("kalshi_prediction_market", {}))
    adapter = KalshiReadonlyAdapter(contract)
    payload = adapter.health_check()
    return summarize_kalshi_snapshot(payload)


def run_kalshi_provider_snapshot(base_data_dir: str | None = None, write_snapshot: bool = True):
    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    contract = dict(config["providers"].get("kalshi_prediction_market", {}))
    adapter = KalshiReadonlyAdapter(contract)
    snapshot = get_kalshi_snapshot(adapter)
    validation = validate_kalshi_snapshot(snapshot)
    snapshot_path = None
    if write_snapshot and int(snapshot.get("records_received", 0)) > 0:
        snapshot_path = write_kalshi_snapshot(snapshot, base_data_dir=base_data_dir or "data")
    summary = summarize_kalshi_snapshot(snapshot, snapshot_path=snapshot_path)
    summary["validation_status"] = validation["status"]
    summary["validation_errors"] = validation["errors"][:10]
    return summary

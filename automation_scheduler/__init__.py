from __future__ import annotations

import json
from pathlib import Path

from .scheduler_runner import run_scheduler_once
from .system_health import get_system_health
from .review_queue import filter_review_items, list_active_review_items, load_review_queue_state, summarize_review_items
from .scheduler_config import get_default_scheduler_config, ensure_runtime_directories
from .backtesting_engine import generate_backtest_report, run_backtest, run_paper_summary
from .calibration import build_calibration_report
from .outcome_store import ingest_outcome_records, load_outcome_state, summarize_outcomes
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
    queue_state = load_review_queue_state(config)
    items = list(queue_state.get("items", []))
    storage_backend = str(queue_state.get("storage_backend") or "unknown")
    if not items:
        active_items = list_active_review_items(config)
        if active_items:
            items = active_items
            storage_backend = "in_memory"
            queue_state = {
                **queue_state,
                "storage_backend": storage_backend,
                "queue_read_ok": True,
                "queue_error_category": queue_state.get("queue_error_category"),
                "items_read_count": len(active_items),
            }
    filtered_all = filter_review_items(items, provider=provider, market_type=market_type, reason=reason)
    filtered = list(filtered_all)
    applied_limit = False
    if isinstance(limit, int) and limit > 0:
        applied_limit = len(filtered) > limit
        filtered = filtered[:limit]
    rejected_reason_counts: dict[str, int] = {}
    health_path = Path(config["paths"]["system_health"]) / "health.json"
    if health_path.exists():
        try:
            health_payload = json.loads(health_path.read_text(encoding="utf-8"))
            rejected_reason_counts = dict(health_payload.get("kalshi_rejected_reason_counts", {}))
        except Exception:
            rejected_reason_counts = {}
    summary = summarize_review_items(filtered_all, rejected_reason_counts=rejected_reason_counts)
    return {
        "ok": True,
        "status": "ok",
        "count": len(filtered),
        "items": filtered,
        "summary": summary,
        "storage_backend": storage_backend,
        "last_updated_at": queue_state.get("last_updated_at"),
        "latest_run_id": queue_state.get("latest_run_id"),
        "queue_read_ok": bool(queue_state.get("queue_read_ok", True)),
        "queue_error_category": queue_state.get("queue_error_category"),
        "queue_read_path": queue_state.get("queue_read_path"),
        "items_read_count": int(queue_state.get("items_read_count", len(items))),
        "compact_filter_applied": bool(applied_limit or str(provider).lower() != "all" or str(market_type).lower() != "all" or bool(reason)),
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


def get_automation_calibration_report(base_data_dir: str | None = None):
    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    return build_calibration_report(base_data_dir=base_data_dir or "data", write_report=True)


def ingest_automation_outcomes(
    records: list[dict],
    *,
    source: str = "local_manual",
    dry_run: bool = True,
    persist: bool = False,
    base_data_dir: str | None = None,
):
    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    return ingest_outcome_records(
        records,
        source=source,
        dry_run=dry_run,
        persist=persist,
        base_data_dir=base_data_dir or "data",
    )


def get_automation_outcomes(base_data_dir: str | None = None, limit: int | None = None):
    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    state = load_outcome_state(base_data_dir or "data")
    records = list(state.get("items", []))
    summary = summarize_outcomes(records)
    cap = limit if isinstance(limit, int) and limit > 0 else len(records)
    return {
        "ok": True,
        "status": "ok",
        "total_count": len(records),
        "records": records[:cap],
        "summary": summary,
        "storage_backend": state.get("storage_backend", "file"),
        "latest_batch_id": state.get("latest_batch_id"),
        "last_updated_at": state.get("last_updated_at"),
        "outcome_read_ok": bool(state.get("outcome_read_ok", True)),
        "outcome_error_category": state.get("outcome_error_category"),
    }


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

from __future__ import annotations

import json
from pathlib import Path

from .data_paths import get_storage_health, resolve_base_data_dir
from .scheduler_runner import run_scheduler_once
from .system_health import get_system_health
from .review_queue import filter_review_items, list_active_review_items, load_review_queue_state, summarize_review_items
from .scheduler_config import get_default_scheduler_config, ensure_runtime_directories
from .backtesting_engine import generate_backtest_report, run_backtest, run_paper_summary
from .calibration import build_calibration_report
from .outcome_store import ingest_outcome_records, load_outcome_state, summarize_outcomes
from .outcome_migration import import_local_settlement_records
from .settlement_discovery import build_outcome_completion_report, write_outcome_completion_candidates
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


def _data_dir(base_data_dir: str | None = None) -> str:
    return str(resolve_base_data_dir(base_data_dir))


def get_scheduler_health(base_data_dir: str | None = None):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
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
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
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
        "storage_health": get_storage_health(),
        "human_approval_required": True,
        "auto_execution_enabled": False,
    }


def get_performance_health(base_data_dir: str | None = None):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    return get_system_health(config)


def run_performance_backtest(model_id: str, historical_rows_path: str | None = None, rows: list[dict] | None = None, base_data_dir: str | None = None):
    base = _data_dir(base_data_dir)
    return generate_backtest_report(
        model_id=model_id,
        historical_rows_path=historical_rows_path,
        rows=rows,
        base_data_dir=base,
    )


def get_performance_report(model_id: str, historical_rows_path: str | None = None, rows: list[dict] | None = None, base_data_dir: str | None = None):
    base = _data_dir(base_data_dir)
    result = generate_backtest_report(
        model_id=model_id,
        historical_rows_path=historical_rows_path,
        rows=rows,
        base_data_dir=base,
    )
    return result["compact_report"]


def get_paper_summary(base_data_dir: str | None = None):
    return run_paper_summary(base_data_dir=_data_dir(base_data_dir))


def get_automation_calibration_report(base_data_dir: str | None = None):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    return build_calibration_report(base_data_dir=base, write_report=True)


def ingest_automation_outcomes(
    records: list[dict],
    *,
    source: str = "local_manual",
    dry_run: bool = True,
    persist: bool = False,
    base_data_dir: str | None = None,
):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    return ingest_outcome_records(
        records,
        source=source,
        dry_run=dry_run,
        persist=persist,
        base_data_dir=base,
    )


def import_local_settlement_outcomes(
    records: list[dict],
    *,
    supporting_paper_decisions: list[dict] | None = None,
    source: str = "local_repo_migration",
    migration_version: str = "kalshi_outcome_migration_v1",
    dry_run: bool = True,
    persist: bool = False,
    base_data_dir: str | None = None,
):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    return import_local_settlement_records(
        records,
        supporting_paper_decisions=supporting_paper_decisions,
        source=source,
        migration_version=migration_version,
        dry_run=dry_run,
        persist=persist,
        base_data_dir=base,
    )


def get_automation_outcomes(base_data_dir: str | None = None, limit: int | None = None):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    state = load_outcome_state(base)
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
        "storage_health": get_storage_health(),
    }


def discover_automation_outcome_completions(
    *,
    pending_rows: list[dict] | None = None,
    imported_rows: list[dict] | None = None,
    use_kalshi_snapshot: bool = True,
    write_local_report: bool = False,
    base_data_dir: str | None = None,
):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    contract = dict(config["providers"].get("kalshi_prediction_market", {}))
    adapter = KalshiReadonlyAdapter(contract) if use_kalshi_snapshot else None
    report = build_outcome_completion_report(
        pending_rows=pending_rows,
        imported_rows=imported_rows,
        adapter=adapter,
        base_data_dir=base,
        use_kalshi_snapshot=use_kalshi_snapshot,
    )
    if write_local_report:
        report.update(write_outcome_completion_candidates(report, base_data_dir=base))
    return report


def run_automation_calibration_collector(
    *,
    dry_run: bool = True,
    persist_outcomes: bool = False,
    max_new_contracts: int | None = None,
    target_daily_new_contracts: int | None = None,
    hard_cap_daily_new_contracts: int | None = None,
    max_markets_scanned: int | None = None,
    include_short_term: bool = True,
    include_medium_term: bool = True,
    include_long_term: bool = True,
    adaptive_throttle: bool | None = None,
    deepseek_review: bool = False,
    base_data_dir: str | None = None,
):
    from .calibration_collector import run_collector_cycle

    base = _data_dir(base_data_dir)
    return run_collector_cycle(
        dry_run=dry_run,
        persist_outcomes=persist_outcomes,
        max_new_contracts=max_new_contracts,
        target_daily_new_contracts=target_daily_new_contracts,
        hard_cap_daily_new_contracts=hard_cap_daily_new_contracts,
        max_markets_scanned=max_markets_scanned,
        include_short_term=include_short_term,
        include_medium_term=include_medium_term,
        include_long_term=include_long_term,
        adaptive_throttle=adaptive_throttle,
        deepseek_review=deepseek_review,
        base_data_dir=base,
    )


def run_automation_calibration_collector_scheduled(payload: dict | None = None, *, base_data_dir: str | None = None):
    from .collector_scheduled_runner import run_scheduled_collector_cycle

    return run_scheduled_collector_cycle(payload, base_data_dir=_data_dir(base_data_dir))


def get_automation_collector_daily_report(base_data_dir: str | None = None):
    from .calibration_collector import write_daily_report

    return write_daily_report(base_data_dir=_data_dir(base_data_dir))


def run_automation_deepseek_review(
    *,
    collector_cycle_report: dict | None = None,
    daily_report: dict | None = None,
    calibration_report: dict | None = None,
    sampled_contracts: list[dict] | None = None,
):
    from .deepseek_reviewer import run_deepseek_review

    return run_deepseek_review(
        collector_cycle_report=collector_cycle_report,
        daily_report=daily_report,
        calibration_report=calibration_report,
        sampled_contracts=sampled_contracts,
    )


def get_provider_health(base_data_dir: str | None = None):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    return summarize_provider_health(config["providers"])


def get_provider_registry_snapshot(base_data_dir: str | None = None):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
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
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    contract = dict(config["providers"].get("sharp_sportsbook", {}))
    adapter = SharpSportsbookAdapter(contract)
    payload = adapter.health_check()
    return summarize_sportsbook_snapshot(payload)


def run_sharp_provider_snapshot(base_data_dir: str | None = None, write_snapshot: bool = True):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    contract = dict(config["providers"].get("sharp_sportsbook", {}))
    adapter = SharpSportsbookAdapter(contract)
    snapshot = get_sportsbook_snapshot(adapter)
    validation = validate_sportsbook_snapshot(snapshot)
    snapshot_path = None
    if write_snapshot and int(snapshot.get("records_received", 0)) > 0:
        snapshot_path = write_sportsbook_snapshot(snapshot, base_data_dir=base)
    summary = summarize_sportsbook_snapshot(snapshot, snapshot_path=snapshot_path)
    summary["validation_status"] = validation["status"]
    summary["validation_errors"] = validation["errors"][:10]
    return summary


def get_kalshi_provider_health(base_data_dir: str | None = None):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    contract = dict(config["providers"].get("kalshi_prediction_market", {}))
    adapter = KalshiReadonlyAdapter(contract)
    payload = adapter.health_check()
    return summarize_kalshi_snapshot(payload)


def run_kalshi_provider_snapshot(base_data_dir: str | None = None, write_snapshot: bool = True):
    base = _data_dir(base_data_dir)
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    contract = dict(config["providers"].get("kalshi_prediction_market", {}))
    adapter = KalshiReadonlyAdapter(contract)
    snapshot = get_kalshi_snapshot(adapter)
    validation = validate_kalshi_snapshot(snapshot)
    snapshot_path = None
    if write_snapshot and int(snapshot.get("records_received", 0)) > 0:
        snapshot_path = write_kalshi_snapshot(snapshot, base_data_dir=base)
    summary = summarize_kalshi_snapshot(snapshot, snapshot_path=snapshot_path)
    summary["validation_status"] = validation["status"]
    summary["validation_errors"] = validation["errors"][:10]
    return summary


def get_institutional_lab_health(base_data_dir: str | None = None):
    from .institutional_cross_asset_lab import get_institutional_lab_health as _health

    return _health(base_data_dir=_data_dir(base_data_dir))


def run_institutional_lab(
    *,
    dry_run: bool = True,
    asset_classes: list[str] | None = None,
    read_existing_outputs_only: bool = True,
    persist_lab_report: bool = True,
    persist_outcomes: bool = False,
    deepseek_review: bool = False,
    execution_simulation: bool = False,
    base_data_dir: str | None = None,
):
    from .institutional_cross_asset_lab import run_institutional_lab as _run

    return _run(
        dry_run=dry_run,
        asset_classes=asset_classes,
        read_existing_outputs_only=read_existing_outputs_only,
        persist_lab_report=persist_lab_report,
        persist_outcomes=persist_outcomes,
        deepseek_review=deepseek_review,
        execution_simulation=execution_simulation,
        base_data_dir=_data_dir(base_data_dir),
    )


def get_institutional_lab_report(base_data_dir: str | None = None):
    from .institutional_cross_asset_lab import get_institutional_lab_report as _report

    return _report(base_data_dir=_data_dir(base_data_dir))


def get_institutional_lab_daily_report(base_data_dir: str | None = None, report_date: str | None = None):
    from .institutional_cross_asset_lab import get_institutional_lab_daily_report as _daily

    return _daily(base_data_dir=_data_dir(base_data_dir), report_date=report_date)


def run_institutional_deepseek_review(*, report: dict | None = None, enabled: bool | None = None, base_data_dir: str | None = None):
    from .institutional_deepseek_review import run_deepseek_sidecar_review

    return run_deepseek_sidecar_review(report=report or {}, enabled=enabled, base_data_dir=_data_dir(base_data_dir))


def simulate_institutional_execution(payload: dict, *, base_data_dir: str | None = None):
    from .institutional_execution_desk import simulate_execution

    return simulate_execution(payload, base_data_dir=_data_dir(base_data_dir))


def get_institutional_lab_audit(base_data_dir: str | None = None, limit: int = 100):
    from .institutional_cross_asset_lab import get_institutional_lab_audit as _audit

    return _audit(base_data_dir=_data_dir(base_data_dir), limit=limit)


def get_data_source_registry_snapshot(*, module: str | None = None, base_data_dir: str | None = None):
    from .data_source_registry import build_registry_report

    return build_registry_report(module=module)


def get_data_source_coverage_snapshot(*, module: str | None = None, base_data_dir: str | None = None):
    from .data_source_registry import build_registry
    from .model_input_coverage import build_coverage_report

    registry = build_registry(module=module)
    return build_coverage_report(registry=registry)


def get_data_source_research_lanes_snapshot(*, module: str | None = None, base_data_dir: str | None = None):
    from .data_source_registry import build_registry
    from .data_source_research_lanes import build_research_tasks

    registry = build_registry(module=module)
    return build_research_tasks(registry.get("lanes", []))


def get_data_source_env_var_registry(*, module: str | None = None, base_data_dir: str | None = None):
    from .data_source_registry import build_env_var_registry

    return build_env_var_registry(module=module)


def get_data_source_priorities_snapshot(*, module: str | None = None, limit: int = 50, base_data_dir: str | None = None):
    from .data_source_registry import build_source_priorities

    return build_source_priorities(module=module, limit=limit)


def get_public_apis_expansion_report(*, module: str | None = None, persist_report: bool = False, base_data_dir: str | None = None):
    from .data_source_registry import build_public_apis_expansion_report, write_public_apis_expansion_report

    report = build_public_apis_expansion_report(module=module)
    if persist_report:
        report.update(write_public_apis_expansion_report(report, base_data_dir=_data_dir(base_data_dir)))
    return report


def get_data_source_registry_health(base_data_dir: str | None = None):
    from .data_source_registry import build_registry_report, summarize_registry

    report = build_registry_report()
    summary = summarize_registry(report)
    return {
        "ok": True,
        "status": "ok",
        "schema_version": report.get("schema_version"),
        "total_lanes": summary["total_lanes"],
        "total_sources": summary["total_sources"],
        "enabled_source_count": summary.get("enabled_source_count", 0),
        "source_counts_by_category": summary.get("source_counts_by_category", {}),
        "key_required_source_count": summary.get("key_required_source_count", 0),
        "oauth_required_source_count": summary.get("oauth_required_source_count", 0),
        "provider_write_enabled_count": summary.get("provider_write_enabled_count", 0),
        "execution_allowed_count": summary.get("execution_allowed_count", 0),
        "lanes_with_candidate_sources": summary["lanes_with_candidate_sources"],
        "lanes_needing_external_research": summary["lanes_needing_external_research"],
        "needs_terms_review_count": summary["needs_terms_review_count"],
        "future_source_candidate_count": summary["future_source_candidate_count"],
        "storage_health": get_storage_health(),
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "crypto_trade_execution_enabled": False,
        "stock_trade_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "actual_crypto_swaps_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def verify_data_source_registry(*, module: str | None = None, persist_report: bool = True, base_data_dir: str | None = None):
    from .data_source_registry import verify_registry

    return verify_registry(module=module, persist_report=persist_report, base_data_dir=_data_dir(base_data_dir))


def verify_ncaaf_cfbd_adapter(
    *,
    dry_run: bool = True,
    season: int | None = None,
    week: int | None = None,
    max_records: int = 5,
    fetch_live_sample: bool = False,
    base_data_dir: str | None = None,
):
    from .ncaaf_collegefootballdata_adapter import verify_ncaaf_cfbd_adapter as _verify

    return _verify(
        dry_run=dry_run,
        season=season,
        week=week,
        max_records=max_records,
        fetch_live_sample=fetch_live_sample,
        base_data_dir=_data_dir(base_data_dir),
    )

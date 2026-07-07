from __future__ import annotations

"""Import-safe compatibility facade for scheduler symbols."""

import json
from importlib import import_module
from pathlib import Path
from typing import Any

from src.analytics.review_queue import (
    filter_review_items,
    list_active_review_items,
    load_review_queue_state,
    summarize_review_items,
)
from src.data.data_paths import get_storage_health, resolve_base_data_dir
from src.services.runtime_shared import get_automation_data_dir, get_runtime_data_path
from src.services.scheduler_config import ensure_runtime_directories, get_default_scheduler_config


_CANONICAL_MODULES: tuple[str, ...] = (
    "src.analytics",
    "src.backtesting.dataset_builder",
    "src.backtesting.engine",
    "src.backtesting.historical_bridge",
    "src.backtesting.strategy_profiles",
    "src.brokerage.readiness_support",
    "src.data.historical_odds",
    "src.data.historical_research_database",
    "src.data.historical_sources",
    "src.data.line_movement",
    "src.data.source_event_links",
    "src.market_intelligence.feature_packs",
    "src.market_intelligence.impact",
    "src.market_intelligence.manifold",
    "src.market_intelligence.options",
    "src.market_intelligence.response_compactor",
    "src.market_intelligence.sports",
    "src.providers",
    "src.providers.health",
    "src.security.ai_provider_security",
    "src.security.hard_gate_policy",
    "src.security.owner_approval_gate",
    "src.security.policy",
    "src.security.risk_limit_guard",
    "src.security.secret_safety",
    "src.providers.policy",
    "src.research.feature_control",
    "src.research.history",
    "src.services.runtime_shared",
    "src.services.security_readiness",
)

_LEGACY_MODULES: tuple[str, ...] = (
    "src.security.ai_provider_security",
    "src.research.causal_scaffold",
    "src.market_intelligence.candlestick_manifold_detector",
    "src.market_intelligence.cross_asset_intelligence_router",
    "src.market_intelligence.cross_asset_manifold_router",
    "src.market_intelligence.data_intelligence_registry",
    "src.data.data_paths",
    "src.research.feature_ablation_lab",
    "src.analytics.field_scorecard",
    "src.market_intelligence.graph_relationship_mapper",
    "src.security.hard_gate_policy",
    "src.data.historical_backtest_bridge",
    "src.data.historical_line_movement",
    "src.data.historical_odds_importers",
    "src.data.historical_odds_sqlite",
    "src.data.historical_data_sources",
    "src.data.line_movement_data_quality_dashboard",
    "src.market_intelligence.manifold_cluster_registry",
    "src.market_intelligence.market_state_manifold",
    "src.data.model_data_field_catalog",
    "src.research.representation_feature_builder",
    "src.market_intelligence.response_compactor",
    "src.services.security_readiness",
    "src.analytics.strategy_readiness_report",
    "src.core.strategy_router",
    "src.core.strategy_maturity",
    "src.data.source_event_link_resolver",
    "src.services.scheduler_config",
    "src.services.streamlit_dashboard_data",
    "src.data.zero_dte_fixture_template",
)


def _resolve_symbol(name: str) -> Any:
    for module_name in _CANONICAL_MODULES:
        module = import_module(module_name)
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    for module_name in _LEGACY_MODULES:
        try:
            module = import_module(module_name)
        except ModuleNotFoundError:
            continue
        if hasattr(module, name):
            value = getattr(module, name)
            globals()[name] = value
            return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __getattr__(name: str) -> Any:
    return _resolve_symbol(name)


def __dir__() -> list[str]:
    names = set(globals())
    for module_name in _CANONICAL_MODULES + _LEGACY_MODULES:
        try:
            module = import_module(module_name)
        except Exception:
            continue
        names.update(attr for attr in dir(module) if not attr.startswith("_"))
    return sorted(names)


def get_scheduler_review_queue(
    base_data_dir: str | None = None,
    *,
    provider: str = "all",
    market_type: str = "all",
    reason: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    base = str(resolve_base_data_dir(base_data_dir))
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


def get_provider_health(base_data_dir: str | None = None) -> dict[str, Any]:
    base = str(resolve_base_data_dir(base_data_dir))
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    from src.providers.health import summarize_provider_health

    return summarize_provider_health(config["providers"])


def get_provider_registry_snapshot(base_data_dir: str | None = None) -> dict[str, Any]:
    base = str(resolve_base_data_dir(base_data_dir))
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    from src.providers.registry import get_provider_registry

    providers = list(get_provider_registry(include_legacy_aliases=True).values())
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


def get_sharp_provider_health(base_data_dir: str | None = None) -> dict[str, Any]:
    base = str(resolve_base_data_dir(base_data_dir))
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    contract = dict(config["providers"].get("sharp_sportsbook", {}))
    from src.services.odds_runtime_bridge import SharpSportsbookAdapter, summarize_sportsbook_snapshot

    adapter = SharpSportsbookAdapter(contract)
    payload = adapter.health_check()
    return summarize_sportsbook_snapshot(payload)


def run_sharp_provider_snapshot(base_data_dir: str | None = None, write_snapshot: bool = True) -> dict[str, Any]:
    base = str(resolve_base_data_dir(base_data_dir))
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    contract = dict(config["providers"].get("sharp_sportsbook", {}))
    from src.services.odds_runtime_bridge import (
        SharpSportsbookAdapter,
        get_sportsbook_snapshot,
        summarize_sportsbook_snapshot,
        validate_sportsbook_snapshot,
        write_sportsbook_snapshot,
    )

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


def get_kalshi_provider_health(base_data_dir: str | None = None) -> dict[str, Any]:
    base = str(resolve_base_data_dir(base_data_dir))
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    contract = dict(config["providers"].get("kalshi_prediction_market", {}))
    from src.services.prediction_market_runtime_bridge import KalshiReadonlyAdapter, summarize_kalshi_snapshot

    adapter = KalshiReadonlyAdapter(contract)
    payload = adapter.health_check()
    return summarize_kalshi_snapshot(payload)


def run_kalshi_provider_snapshot(base_data_dir: str | None = None, write_snapshot: bool = True) -> dict[str, Any]:
    base = str(resolve_base_data_dir(base_data_dir))
    config = get_default_scheduler_config(base_data_dir=base)
    ensure_runtime_directories(config)
    contract = dict(config["providers"].get("kalshi_prediction_market", {}))
    from src.services.prediction_market_runtime_bridge import (
        KalshiReadonlyAdapter,
        get_kalshi_snapshot,
        summarize_kalshi_snapshot,
        validate_kalshi_snapshot,
        write_kalshi_snapshot,
    )

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


def get_data_source_registry_snapshot(module: str | None = None) -> dict[str, Any]:
    from src.data.data_source_registry import build_registry_report

    return build_registry_report(module=module)


def get_data_source_coverage_snapshot(module: str | None = None) -> dict[str, Any]:
    from src.data.data_source_registry import build_registry
    from src.market_intelligence.model_input_coverage import build_coverage_report

    registry = build_registry(module=module)
    return build_coverage_report(registry=registry)


def get_data_source_research_lanes_snapshot(module: str | None = None) -> dict[str, Any]:
    from src.data.data_source_registry import build_registry
    from src.data.data_source_research_lanes import build_research_tasks

    registry = build_registry(module=module)
    tasks = build_research_tasks(list(registry.get("lanes") or []))
    return {
        **registry,
        **tasks,
        "module_filter": module,
        "schema_version": registry.get("schema_version"),
    }


def get_data_source_env_var_registry(module: str | None = None) -> dict[str, Any]:
    from src.data.data_source_registry import build_env_var_registry

    return build_env_var_registry(module=module)


def get_data_source_priorities_snapshot(module: str | None = None, limit: int = 50) -> dict[str, Any]:
    from src.data.data_source_registry import build_source_priorities

    return build_source_priorities(module=module, limit=limit)


def get_public_apis_expansion_report(
    module: str | None = None,
    *,
    persist_report: bool = False,
    base_data_dir: str | None = None,
) -> dict[str, Any]:
    from src.data.data_source_registry import build_public_apis_expansion_report, write_public_apis_expansion_report

    payload = build_public_apis_expansion_report(module=module)
    if persist_report:
        payload = {**payload, **write_public_apis_expansion_report(payload, base_data_dir=base_data_dir)}
    return payload


def get_data_availability_tiers_report(
    module: str | None = None,
    *,
    persist_report: bool = False,
    base_data_dir: str | None = None,
) -> dict[str, Any]:
    from src.data.data_availability_tiers import build_data_availability_report, write_data_availability_report
    from src.data.data_source_registry import build_registry

    registry = build_registry(module=module)
    payload = build_data_availability_report(registry=registry, module=module)
    if persist_report:
        payload = {**payload, **write_data_availability_report(payload, base_data_dir=base_data_dir)}
    return payload


def get_data_source_registry_health(module: str | None = None) -> dict[str, Any]:
    from src.data.data_source_registry import build_registry_report

    return build_registry_report(module=module)


def get_scheduler_health(base_data_dir: str | None = None) -> dict[str, Any]:
    from src.services.scheduler_config import get_default_scheduler_config
    from src.services.system_health import get_system_health

    base = str(resolve_base_data_dir(base_data_dir))
    config = get_default_scheduler_config(base_data_dir=base)
    return get_system_health(config)


def get_security_readiness(base_data_dir: str | None = None) -> dict[str, Any]:
    from src.services.security_readiness import build_security_readiness_report

    return build_security_readiness_report(base_data_dir=str(resolve_base_data_dir(base_data_dir)))


def get_intelligence_readiness(base_data_dir: str | None = None) -> dict[str, Any]:
    from src.analytics.intelligence_readiness_report import build_intelligence_readiness_report

    return build_intelligence_readiness_report(base_data_dir=str(resolve_base_data_dir(base_data_dir)))


def get_strategy_readiness(base_data_dir: str | None = None) -> dict[str, Any]:
    from src.analytics.strategy_readiness_report import build_strategy_readiness_report

    return build_strategy_readiness_report(base_data_dir=str(resolve_base_data_dir(base_data_dir)))


def run_small_account_pattern_detection(
    items: list[dict] | None = None,
    *,
    base_data_dir: str | None = None,
) -> dict[str, Any]:
    from src.services.execution_service import detect_candlestick_patterns
    from src.services.execution_service import SAFETY_FLAGS

    rows = [row for row in (items or []) if isinstance(row, dict)]
    detections = []
    for row in rows:
        context = {
            "asset_symbol": row.get("asset_symbol") or row.get("symbol") or row.get("ticker") or "UNKNOWN",
            "asset_type": row.get("asset_type") or "stock",
            "timeframe": row.get("timeframe") or "unknown",
            "detected_at": row.get("detected_at"),
            "vwap": row.get("vwap"),
            "opening_range_high": row.get("opening_range_high"),
            "previous_close": row.get("previous_close"),
            "pullback_high": row.get("pullback_high"),
            "prior_high": row.get("prior_high"),
            "breakout_confirmation_score": row.get("breakout_confirmation_score", 50.0),
        }
        detections.extend(detect_candlestick_patterns(row.get("candles") or [], context))
    return {
        "ok": True,
        "status": "patterns_detected",
        "items_scanned": len(rows),
        "detections_created": len(detections),
        "detections": detections,
        **SAFETY_FLAGS,
    }


def run_small_account_review_cycle(
    items: list[dict] | None = None,
    *,
    session_state: dict | None = None,
    persist_queue: bool = False,
    base_data_dir: str | None = None,
) -> dict[str, Any]:
    from src.services.execution_service import run_small_account_review

    return run_small_account_review(
        items,
        session_state=session_state,
        persist_queue=persist_queue,
        base_data_dir=str(resolve_base_data_dir(base_data_dir)),
    )


def get_small_account_pattern_review_queue(
    base_data_dir: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    from src.analytics.pattern_review_queue import load_pattern_review_queue

    return load_pattern_review_queue(base_data_dir=str(resolve_base_data_dir(base_data_dir)), limit=limit)


def get_small_account_pattern_calibration(
    records: list[dict] | None = None,
    base_data_dir: str | None = None,
) -> dict[str, Any]:
    from src.research.pattern_calibration import build_pattern_calibration_report

    return build_pattern_calibration_report(records=records or [])


def get_small_account_micro_outcome_calibration(
    records: list[dict] | None = None,
    base_data_dir: str | None = None,
) -> dict[str, Any]:
    from src.analytics.micro_outcome_calibration import build_micro_calibration_report

    return build_micro_calibration_report(records=records or [])


def get_broker_quality(base_data_dir: str | None = None) -> dict[str, Any]:
    from src.services.execution_service import build_broker_quality_report

    return build_broker_quality_report()


def get_balance_sheet_risk(symbol: str, base_data_dir: str | None = None) -> dict[str, Any]:
    from src.core.balance_sheet_risk import evaluate_balance_sheet
    from src.services.execution_service import SAFETY_FLAGS

    base = resolve_base_data_dir(base_data_dir)
    sample_path = base / "small_account_review" / "balance_sheet_samples.json"
    samples: dict[str, Any] = {}
    if sample_path.exists():
        try:
            payload = json.loads(sample_path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                samples = payload
        except Exception:
            samples = {}
    key = str(symbol or "").upper()
    row = samples.get(key) if isinstance(samples, dict) else None
    result = evaluate_balance_sheet(row if isinstance(row, dict) else {})
    return {
        "ok": True,
        "status": "DATA_INSUFFICIENT" if result["data_insufficient"] else "ok",
        "symbol": key,
        "source": "local_sample" if isinstance(row, dict) else "local_sample_missing",
        "balance_sheet_risk": result,
        "storage_health": get_storage_health(),
        **SAFETY_FLAGS,
    }


def run_scheduler_once(*args, **kwargs) -> dict[str, Any]:
    from src.services.scheduler_runner import run_scheduler_once as _run_scheduler_once

    return _run_scheduler_once(*args, **kwargs)


def verify_ncaaf_cfbd_adapter(**kwargs: Any) -> dict[str, Any]:
    from src.providers.ncaaf_collegefootballdata_adapter import verify_ncaaf_cfbd_adapter as _verify_ncaaf_cfbd_adapter

    return _verify_ncaaf_cfbd_adapter(**kwargs)


def verify_data_source_registry(
    module: str | None = None,
    *,
    persist_report: bool = True,
    base_data_dir: str | None = None,
) -> dict[str, Any]:
    from src.data.data_source_registry import verify_registry

    return verify_registry(module=module, persist_report=persist_report, base_data_dir=base_data_dir)


def get_automation_calibration_report(base_data_dir: str | None = None) -> dict[str, Any]:
    from src.analytics.calibration import build_calibration_report

    return build_calibration_report(base_data_dir=str(resolve_base_data_dir(base_data_dir)), write_report=False)


def get_automation_outcomes(limit: int = 10, base_data_dir: str | None = None) -> dict[str, Any]:
    from src.services.outcome_store import load_outcome_records, load_outcome_state, summarize_outcomes

    base = str(resolve_base_data_dir(base_data_dir))
    state = load_outcome_state(base)
    items = list(state.get("items") or load_outcome_records(base))
    return {
        **state,
        "ok": True,
        "status": state.get("outcome_error_category") or "ok",
        "records": items,
        "items": items,
        "summary": summarize_outcomes(items),
    }


def ingest_automation_outcomes(
    records: list[dict[str, Any]] | None,
    *,
    source: str = "local_manual",
    dry_run: bool = True,
    persist: bool = False,
    base_data_dir: str | None = None,
) -> dict[str, Any]:
    from src.services.outcome_store import ingest_outcome_records

    return ingest_outcome_records(records, source=source, dry_run=dry_run, persist=persist, base_data_dir=str(resolve_base_data_dir(base_data_dir)))


def import_local_settlement_outcomes(
    records: list[dict[str, Any]] | None,
    *,
    supporting_paper_decisions: list[dict[str, Any]] | None = None,
    source: str = "local_repo_migration",
    migration_version: str = "kalshi_outcome_migration_v1",
    dry_run: bool = True,
    persist: bool = False,
    base_data_dir: str | None = None,
) -> dict[str, Any]:
    from src.data.outcome_migration import import_local_settlement_records

    return import_local_settlement_records(
        records,
        supporting_paper_decisions=supporting_paper_decisions,
        source=source,
        migration_version=migration_version,
        dry_run=dry_run,
        persist=persist,
        base_data_dir=str(resolve_base_data_dir(base_data_dir)),
    )


def discover_automation_outcome_completions(
    pending_rows: list[dict[str, Any]] | None = None,
    imported_rows: list[dict[str, Any]] | None = None,
    *,
    use_kalshi_snapshot: bool = True,
    write_local_report: bool = False,
    base_data_dir: str | None = None,
) -> dict[str, Any]:
    from src.services.settlement_service import build_outcome_completion_report, write_outcome_completion_candidates

    base = str(resolve_base_data_dir(base_data_dir))
    report = build_outcome_completion_report(
        pending_rows=pending_rows,
        imported_rows=imported_rows,
        use_kalshi_snapshot=use_kalshi_snapshot,
        base_data_dir=base,
    )
    if write_local_report:
        report = {**report, **write_outcome_completion_candidates(report, base_data_dir=base)}
    return report


def load_security_audit_records(*, base_data_dir: str | None = None, limit: int = 100) -> dict[str, Any]:
    from src.services.ledger_service import load_security_audit_records

    return load_security_audit_records(base_data_dir=base_data_dir, limit=limit)


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
) -> dict[str, Any]:
    from src.analytics.calibration_collector import run_collector_cycle

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
        base_data_dir=str(resolve_base_data_dir(base_data_dir)),
    )


def run_automation_calibration_collector_scheduled(
    payload: dict[str, Any] | None = None,
    *,
    base_data_dir: str | None = None,
) -> dict[str, Any]:
    from src.services.collector_scheduled_runner import run_scheduled_collector_cycle

    return run_scheduled_collector_cycle(payload, base_data_dir=str(resolve_base_data_dir(base_data_dir)))


def run_automation_deepseek_review(
    *,
    collector_cycle_report: dict[str, Any] | None = None,
    daily_report: dict[str, Any] | None = None,
    calibration_report: dict[str, Any] | None = None,
    sampled_contracts: list[dict[str, Any]] | None = None,
    candidate: dict[str, Any] | None = None,
    candidates: list[dict[str, Any]] | None = None,
    core_model_action: str | None = None,
    enabled: bool | None = None,
    review_queue_summary: dict[str, Any] | None = None,
    outcome_summary: dict[str, Any] | None = None,
    provider_health_summary: dict[str, Any] | None = None,
    manifold_cluster_summary: dict[str, Any] | None = None,
    markov_hmm_summary: dict[str, Any] | None = None,
    sportsbook_full_board_summary: dict[str, Any] | None = None,
    stock_crypto_pattern_summary: dict[str, Any] | None = None,
    kalshi_prediction_market_summary: dict[str, Any] | None = None,
    small_account_summary: dict[str, Any] | None = None,
    security_readiness_summary: dict[str, Any] | None = None,
    strategy_readiness_summary: dict[str, Any] | None = None,
    trap_no_bet_summary: dict[str, Any] | None = None,
    base_data_dir: str | None = None,
) -> dict[str, Any]:
    base = str(resolve_base_data_dir(base_data_dir))
    if candidate or candidates:
        from src.ai.deepseek_profit_lab import run_candidate_review

        review_candidate = dict(candidate or (candidates[0] if candidates else {}) or {})
        return run_candidate_review(
            candidate=review_candidate if review_candidate else None,
            core_model_action=core_model_action,
            enabled=enabled,
            base_data_dir=base,
            review_queue_summary=review_queue_summary,
            outcome_summary=outcome_summary,
            provider_health_summary=provider_health_summary,
            manifold_cluster_summary=manifold_cluster_summary,
            markov_hmm_summary=markov_hmm_summary,
            sportsbook_full_board_summary=sportsbook_full_board_summary,
            stock_crypto_pattern_summary=stock_crypto_pattern_summary,
            kalshi_prediction_market_summary=kalshi_prediction_market_summary,
            small_account_summary=small_account_summary,
            security_readiness_summary=security_readiness_summary,
            strategy_readiness_summary=strategy_readiness_summary,
            trap_no_bet_summary=trap_no_bet_summary,
            collector_cycle_report=collector_cycle_report,
            daily_report=daily_report,
            calibration_report=calibration_report,
            sampled_contracts=sampled_contracts,
        )

    from src.ai.deepseek_reviewer import run_deepseek_review

    return run_deepseek_review(
        collector_cycle_report=collector_cycle_report,
        daily_report=daily_report,
        calibration_report=calibration_report,
        sampled_contracts=sampled_contracts,
        enabled=enabled,
    )


def run_automation_deepseek_red_team(
    *,
    candidate: dict[str, Any] | None = None,
    candidates: list[dict[str, Any]] | None = None,
    enabled: bool | None = None,
    review_queue_summary: dict[str, Any] | None = None,
    calibration_summary: dict[str, Any] | None = None,
    outcome_summary: dict[str, Any] | None = None,
    provider_health_summary: dict[str, Any] | None = None,
    manifold_cluster_summary: dict[str, Any] | None = None,
    markov_hmm_summary: dict[str, Any] | None = None,
    sportsbook_full_board_summary: dict[str, Any] | None = None,
    stock_crypto_pattern_summary: dict[str, Any] | None = None,
    kalshi_prediction_market_summary: dict[str, Any] | None = None,
    small_account_summary: dict[str, Any] | None = None,
    security_readiness_summary: dict[str, Any] | None = None,
    strategy_readiness_summary: dict[str, Any] | None = None,
    trap_no_bet_summary: dict[str, Any] | None = None,
    base_data_dir: str | None = None,
) -> dict[str, Any]:
    from src.ai.deepseek_profit_lab import run_red_team_review

    return run_red_team_review(
        candidate=candidate,
        candidates=candidates,
        enabled=enabled,
        base_data_dir=str(resolve_base_data_dir(base_data_dir)),
        review_queue_summary=review_queue_summary,
        calibration_summary=calibration_summary,
        outcome_summary=outcome_summary,
        provider_health_summary=provider_health_summary,
        manifold_cluster_summary=manifold_cluster_summary,
        markov_hmm_summary=markov_hmm_summary,
        sportsbook_full_board_summary=sportsbook_full_board_summary,
        stock_crypto_pattern_summary=stock_crypto_pattern_summary,
        kalshi_prediction_market_summary=kalshi_prediction_market_summary,
        small_account_summary=small_account_summary,
        security_readiness_summary=security_readiness_summary,
        strategy_readiness_summary=strategy_readiness_summary,
        trap_no_bet_summary=trap_no_bet_summary,
    )


def get_deepseek_disagreements(limit: int = 100, base_data_dir: str | None = None) -> dict[str, Any]:
    from src.ai.deepseek_disagreement_queue import load_disagreement_queue

    return load_disagreement_queue(base_data_dir=str(resolve_base_data_dir(base_data_dir)), limit=limit)


def get_deepseek_daily_report(
    *,
    report_date: str | None = None,
    enabled: bool | None = None,
    persist_report: bool = True,
    base_data_dir: str | None = None,
) -> dict[str, Any]:
    from src.ai.deepseek_profit_lab import run_daily_report

    return run_daily_report(
        report_date=report_date,
        enabled=enabled,
        persist_report=persist_report,
        base_data_dir=str(resolve_base_data_dir(base_data_dir)),
    )


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
) -> dict[str, Any]:
    from src.market_intelligence.institutional_cross_asset_lab import run_institutional_lab as _run_institutional_lab

    return _run_institutional_lab(
        dry_run=dry_run,
        asset_classes=asset_classes,
        read_existing_outputs_only=read_existing_outputs_only,
        persist_lab_report=persist_lab_report,
        persist_outcomes=persist_outcomes,
        deepseek_review=deepseek_review,
        execution_simulation=execution_simulation,
        base_data_dir=str(resolve_base_data_dir(base_data_dir)),
    )


def get_institutional_lab_health(*, base_data_dir: str | None = None) -> dict[str, Any]:
    from src.market_intelligence.institutional_cross_asset_lab import get_institutional_lab_health as _get_institutional_lab_health

    return _get_institutional_lab_health(base_data_dir=str(resolve_base_data_dir(base_data_dir)))


def get_institutional_lab_report(*, base_data_dir: str | None = None) -> dict[str, Any]:
    from src.market_intelligence.institutional_cross_asset_lab import get_institutional_lab_report as _get_institutional_lab_report

    return _get_institutional_lab_report(base_data_dir=str(resolve_base_data_dir(base_data_dir)))


def get_institutional_lab_daily_report(*, report_date: str | None = None, base_data_dir: str | None = None) -> dict[str, Any]:
    from src.market_intelligence.institutional_cross_asset_lab import get_institutional_lab_daily_report as _get_institutional_lab_daily_report

    return _get_institutional_lab_daily_report(report_date=report_date, base_data_dir=str(resolve_base_data_dir(base_data_dir)))


def get_institutional_lab_audit(*, base_data_dir: str | None = None, limit: int = 100) -> dict[str, Any]:
    from src.market_intelligence.institutional_cross_asset_lab import get_institutional_lab_audit as _get_institutional_lab_audit

    return _get_institutional_lab_audit(base_data_dir=str(resolve_base_data_dir(base_data_dir)), limit=limit)


def run_institutional_deepseek_review(
    *,
    report: dict[str, Any] | None = None,
    enabled: bool | None = None,
    local_url: str | None = None,
    base_data_dir: str | None = None,
    persist_audit: bool = True,
) -> dict[str, Any]:
    from src.ai.institutional_deepseek_review import run_deepseek_sidecar_review

    return run_deepseek_sidecar_review(
        report=report,
        enabled=enabled,
        local_url=local_url,
        base_data_dir=str(resolve_base_data_dir(base_data_dir)),
        persist_audit=persist_audit,
    )


def simulate_institutional_execution(
    payload: dict[str, Any],
    *,
    records: list[dict[str, Any]] | None = None,
    calibration_report: dict[str, Any] | None = None,
    base_data_dir: str | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    from src.services.execution_service import simulate_execution

    return simulate_execution(
        payload,
        records=records,
        calibration_report=calibration_report,
        base_data_dir=str(resolve_base_data_dir(base_data_dir)),
        persist=persist,
    )


__all__ = [
    "get_automation_data_dir",
    "get_runtime_data_path",
    "get_scheduler_review_queue",
    "get_provider_health",
    "get_provider_registry_snapshot",
    "get_sharp_provider_health",
    "run_sharp_provider_snapshot",
    "get_kalshi_provider_health",
    "run_kalshi_provider_snapshot",
    "get_data_source_registry_snapshot",
    "get_data_source_coverage_snapshot",
    "get_data_source_research_lanes_snapshot",
    "get_data_source_env_var_registry",
    "get_data_source_priorities_snapshot",
    "get_public_apis_expansion_report",
    "get_data_availability_tiers_report",
    "get_data_source_registry_health",
    "get_scheduler_health",
    "get_security_readiness",
    "get_intelligence_readiness",
    "get_strategy_readiness",
    "run_small_account_pattern_detection",
    "run_small_account_review_cycle",
    "get_small_account_pattern_review_queue",
    "get_small_account_pattern_calibration",
    "get_small_account_micro_outcome_calibration",
    "get_broker_quality",
    "get_balance_sheet_risk",
    "verify_ncaaf_cfbd_adapter",
    "verify_data_source_registry",
    "get_automation_calibration_report",
    "get_automation_outcomes",
    "ingest_automation_outcomes",
    "import_local_settlement_outcomes",
    "discover_automation_outcome_completions",
    "load_security_audit_records",
    "run_automation_calibration_collector",
    "run_automation_calibration_collector_scheduled",
    "run_automation_deepseek_review",
    "run_automation_deepseek_red_team",
    "get_deepseek_disagreements",
    "get_deepseek_daily_report",
    "run_institutional_lab",
    "get_institutional_lab_health",
    "get_institutional_lab_report",
    "get_institutional_lab_daily_report",
    "get_institutional_lab_audit",
    "run_institutional_deepseek_review",
    "simulate_institutional_execution",
    "run_scheduler_once",
]

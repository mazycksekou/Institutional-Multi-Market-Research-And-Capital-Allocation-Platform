from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .alert_engine import build_alert
from .audit_log import append_audit_record
from .field_scorecard import build_field_scorecard
from .kalshi_monitor import monitor_kalshi_market
from .arbitrage_detector import detect_arbitrage
from .cross_book_line_comparator import compare_cross_book_lines
from .ev_line_shopper import shop_ev_lines
from .model_recheck_runner import run_model_recheck
from .middle_opportunity_detector import detect_middle_opportunity
from .news_event_monitor import monitor_news_events
from .odds_line_monitor import monitor_odds_lines
from .stake_sizing_simulator import simulate_stake_plan
from .opportunity_scoring import calculate_opportunity_score
from .player_prop_monitor import monitor_player_props
from .provider_registry import get_provider_registry
from .report_writer import write_report
from .review_queue import build_review_item, list_active_review_items, rescore_review_queue, upsert_review_item
from .scheduler_config import ensure_runtime_directories, get_default_scheduler_config, safe_run_id
from .snapshot_store import SnapshotStore
from .stock_monitor import monitor_stocks
from .system_health import get_system_health, write_system_health


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_scheduler_once(
    *,
    injected_data: dict[str, Any] | None = None,
    base_data_dir: str | None = None,
    dry_run: bool = True,
    run_key: str | None = None,
) -> dict[str, Any]:
    if not dry_run:
        raise ValueError("automation scheduler run-once only supports dry_run=true")

    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    run_seed = run_key or datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    run_id = safe_run_id("automation_scheduler_run", run_seed)
    snapshot_store = SnapshotStore(config)
    payload = injected_data or {}
    providers = get_provider_registry()

    append_audit_record(
        config,
        {
            "run_id": run_id,
            "event": "scheduler_run_started",
            "status": "started",
            "dry_run": True,
            "provider_count": len(providers),
            "started_at": _utc_now_iso(),
        },
    )

    candidates: list[dict[str, Any]] = []
    monitor_errors: list[dict[str, str]] = []

    monitor_specs = [
        (
            "odds_line_monitor",
            monitor_odds_lines,
            {
                "previous_snapshot": payload.get("odds_previous"),
                "current_snapshot": payload.get("odds_current"),
                "provider": "sportsbooks",
                "config": config,
            },
        ),
        (
            "player_prop_monitor",
            monitor_player_props,
            {
                "previous_snapshot": payload.get("props_previous"),
                "current_snapshot": payload.get("props_current"),
                "provider": "odds_api",
                "config": config,
            },
        ),
        (
            "stock_monitor",
            monitor_stocks,
            {
                "previous_snapshot": payload.get("stocks_previous"),
                "current_snapshot": payload.get("stocks_current"),
                "provider": "alpaca",
                "config": config,
            },
        ),
        (
            "kalshi_monitor",
            monitor_kalshi_market,
            {
                "previous_snapshot": payload.get("kalshi_previous"),
                "current_snapshot": payload.get("kalshi_current"),
                "provider": "kalshi",
                "config": config,
            },
        ),
        (
            "news_event_monitor",
            monitor_news_events,
            {
                "events": payload.get("news_events"),
                "provider": "news_provider",
                "config": config,
            },
        ),
    ]

    for monitor_name, runner, kwargs in monitor_specs:
        try:
            result = runner(**kwargs)
            candidates.extend(result.get("candidates", []))
            snapshot = result.get("snapshot")
            if snapshot is not None:
                snapshot_store.save_snapshot(monitor_name, run_id, snapshot)
        except Exception as exc:  # pragma: no cover - defensive safety capture
            monitor_errors.append({"monitor": monitor_name, "error": str(exc)})

    recheck_results = [
        run_model_recheck(candidate)
        for candidate in payload.get("model_rechecks", [])
        if isinstance(candidate, dict)
    ]

    saved_items = []
    for candidate in candidates:
        field_scores = build_field_scorecard(
            candidate,
            roi_target_percent=config["roi_target_percent"],
        )
        opportunity_score = calculate_opportunity_score(field_scores)
        candidate["field_scores"] = field_scores
        candidate["opportunity_score"] = opportunity_score
        candidate["confidence"] = round(field_scores["confidence_score"] / 10, 4)
        candidate["risk"] = round(field_scores["risk_score"] / 10, 4)
        candidate["liquidity"] = round(field_scores["liquidity_score"] / 10, 4)
        candidate.update(build_alert(candidate, config["score_thresholds"]))
        review_item = build_review_item(candidate, config)
        if review_item:
            saved_items.append(upsert_review_item(config, review_item))

    active_items = rescore_review_queue(config)
    report = write_report(
        config,
        report_name=f"scheduler_run_{run_id}",
        payload={
            "run_id": run_id,
            "dry_run": True,
            "human_approval_required": config["human_approval_required"],
            "monitor_errors": monitor_errors,
            "candidate_count": len(candidates),
            "review_item_count": len(active_items),
            "recheck_results": recheck_results,
            "saved_review_items": saved_items,
        },
    )
    health = write_system_health(
        config,
        {
            "last_run_id": run_id,
            "last_run_at": _utc_now_iso(),
            "monitor_errors": monitor_errors,
        },
    )

    append_audit_record(
        config,
        {
            "run_id": run_id,
            "event": "scheduler_run_completed",
            "status": "completed",
            "dry_run": True,
            "candidate_count": len(candidates),
            "review_item_count": len(active_items),
            "monitor_error_count": len(monitor_errors),
            "completed_at": _utc_now_iso(),
        },
    )

    return {
        "ok": True,
        "schema_version": config["schema_version"],
        "run_id": run_id,
        "dry_run": True,
        "human_approval_required": config["human_approval_required"],
        "auto_bet_enabled": config["auto_bet_enabled"],
        "auto_trade_enabled": config["auto_trade_enabled"],
        "auto_execution_enabled": config["auto_execution_enabled"],
        "paper_execution_only": config["paper_execution_only"],
        "alert_only_mode": config["alert_only_mode"],
        "providers": sorted(providers),
        "candidates_processed": len(candidates),
        "review_queue_size": len(active_items),
        "recheck_results": recheck_results,
        "monitor_errors": monitor_errors,
        "report": report,
        "health": health,
    }


def get_scheduler_health(base_data_dir: str | None = None) -> dict[str, Any]:
    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    return get_system_health(config)


def get_scheduler_review_queue(base_data_dir: str | None = None) -> dict[str, Any]:
    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    items = list_active_review_items(config)
    return {
        "ok": True,
        "schema_version": config["schema_version"],
        "count": len(items),
        "items": items,
        "human_approval_required": config["human_approval_required"],
        "auto_execution_enabled": config["auto_execution_enabled"],
    }

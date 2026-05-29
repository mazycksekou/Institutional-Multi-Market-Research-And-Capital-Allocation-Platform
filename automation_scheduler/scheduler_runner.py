from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .provider_adapter_base import ProviderAdapterBase
from .provider_health import summarize_provider_health, write_provider_health_snapshot
from .scheduler_config import get_default_scheduler_config, ensure_runtime_directories
from .snapshot_store import SnapshotStore
from .report_writer import write_report
from .review_queue import list_active_review_items
from .system_health import write_system_health
from .run_context import create_run_context
from .sharp_sportsbook_adapter import SharpSportsbookAdapter


def _collect_provider_placeholders(config: dict[str, Any]) -> dict[str, Any]:
    snapshots = []
    skipped: list[dict[str, str]] = []
    for provider_id, contract in config.get("providers", {}).items():
        if provider_id == "sharp_sportsbook":
            sharp = SharpSportsbookAdapter(contract)
            config_check = sharp.validate_config()
            sharp_reason = "dry_run_placeholder"
            if "provider_disabled" in config_check["blockers"]:
                sharp_reason = "provider_disabled"
            elif "live_reads_disabled" in config_check["blockers"]:
                sharp_reason = "live_reads_disabled"
            elif "blocked_missing_credentials" in config_check["blockers"]:
                sharp_reason = "missing_credentials"
            skipped.append({"provider_id": provider_id, "reason": sharp_reason})
            snapshots.append(sharp.fetch_snapshot())
            continue

        adapter = ProviderAdapterBase(contract)
        config_check = adapter.validate_config()
        skipped_reason = "dry_run_placeholder"
        if "disabled_provider" in config_check["blockers"]:
            skipped_reason = "provider_disabled"
        elif "live_calls_disabled" in config_check["blockers"]:
            skipped_reason = "live_reads_disabled"
        elif "missing_credentials" in config_check["blockers"]:
            skipped_reason = "missing_credentials"
        skipped.append({"provider_id": provider_id, "reason": skipped_reason})
        snapshots.append(adapter.fetch_snapshot())
    write_provider_health_snapshot(config.get("providers", {}))
    return {
        "snapshots": snapshots,
        "skipped": skipped,
        "health": summarize_provider_health(config.get("providers", {})),
    }


def run_scheduler_once(*, injected_data: dict[str, Any] | None = None, base_data_dir: str | None = None, dry_run: bool = True, run_key: str | None = None) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("automation scheduler run-once only supports dry_run=true")
    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    ctx = create_run_context(config)
    store = SnapshotStore(config)
    payload = injected_data or {}
    store.save_snapshot("scheduler_runs", ctx["run_id"], payload)
    provider_result = _collect_provider_placeholders(config)
    queue = list_active_review_items(config)
    skipped = list(payload.get("skipped_items", [])) + provider_result["skipped"]
    report = write_report(
        config,
        report_name=f"scheduler_run_{ctx['run_id']}",
        payload={
            "run_id": ctx["run_id"],
            "created_at": ctx["created_at"],
            "dry_run": True,
            "summary": {"review_queue_size": len(queue)},
            "alerts": [],
            "review_items": queue,
            "skipped_items": skipped,
            "provider_health": provider_result["health"],
            "provider_snapshots": provider_result["snapshots"],
            "errors": [],
            "governance_status": ctx["governance_status"],
        },
    )
    write_system_health(config, {"last_run_id": ctx["run_id"], "last_run_at": datetime.now(timezone.utc).isoformat()})
    return {
        "ok": True,
        "run_id": ctx["run_id"],
        "created_at": ctx["created_at"],
        "dry_run": True,
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "candidates_processed": len(payload.get("candidates", [])),
        "review_queue_size": len(queue),
        "skipped_items": skipped,
        "skipped_count": len(skipped),
        "provider_count": int(provider_result["health"]["provider_count"]),
        "enabled_provider_count": int(provider_result["health"]["enabled_provider_count"]),
        "live_calls_enabled_count": int(provider_result["health"]["live_calls_enabled_count"]),
        "report": report,
        "blockers": [],
    }

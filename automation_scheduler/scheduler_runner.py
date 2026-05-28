from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .scheduler_config import get_default_scheduler_config, ensure_runtime_directories
from .snapshot_store import SnapshotStore
from .report_writer import write_report
from .review_queue import list_active_review_items
from .system_health import write_system_health
from .run_context import create_run_context


def run_scheduler_once(*, injected_data: dict[str, Any] | None = None, base_data_dir: str | None = None, dry_run: bool = True, run_key: str | None = None) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("automation scheduler run-once only supports dry_run=true")
    config = get_default_scheduler_config(base_data_dir=base_data_dir)
    ensure_runtime_directories(config)
    ctx = create_run_context(config)
    store = SnapshotStore(config)
    payload = injected_data or {}
    store.save_snapshot("scheduler_runs", ctx["run_id"], payload)
    queue = list_active_review_items(config)
    skipped = list(payload.get("skipped_items", []))
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
        "report": report,
        "blockers": [],
    }

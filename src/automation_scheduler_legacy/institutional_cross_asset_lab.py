from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .data_paths import get_storage_health, resolve_base_data_dir
from src.services.ledger_service import append_audit_record, load_audit_records
from .institutional_cross_asset_adapters import ASSET_CLASSES, compact_redact, read_existing_outputs
from .institutional_cross_asset_calibration import build_calibration_by_asset_class
from .institutional_cross_asset_reports import load_daily_report, load_latest_report, write_daily_report, write_run_artifacts
from .institutional_deepseek_review import run_deepseek_sidecar_review
from src.services.execution_service import simulate_execution
from .institutional_risk_engine import assess_institutional_risk
from .scheduler_config import safe_run_id, utc_now_iso


LAB_SAFETY_FLAGS = {
    "provider_write": False,
    "execution_allowed": False,
    "live_execution_enabled": False,
    "auto_execution_enabled": False,
    "auto_bet_enabled": False,
    "auto_trade_enabled": False,
    "kalshi_order_execution_enabled": False,
    "sportsbook_bet_execution_enabled": False,
    "broker_order_execution_enabled": False,
    "human_approval_required": True,
    "paper_only": True,
    "review_only": True,
    "simulation_only": True,
}


def _lab_root(base_data_dir: str = "data") -> Path:
    path = resolve_base_data_dir(base_data_dir) / "institutional_lab"
    path.mkdir(parents=True, exist_ok=True)
    for child in ("items", "daily", "reports", "audit", "execution_sim", "locks"):
        (path / child).mkdir(parents=True, exist_ok=True)
    return path


def _lock_path(base_data_dir: str = "data") -> Path:
    return _lab_root(base_data_dir) / "locks" / "institutional_lab.lock"


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _acquire_lock(base_data_dir: str, run_id: str, stale_after_seconds: int = 900) -> tuple[bool, bool]:
    path = _lock_path(base_data_dir)
    skipped_due_to_lock = False
    existing = _read_json(path)
    if isinstance(existing, dict):
        acquired_at = _parse_time(existing.get("acquired_at"))
        if acquired_at and datetime.now(timezone.utc) - acquired_at < timedelta(seconds=stale_after_seconds):
            return False, True
        try:
            path.unlink()
        except FileNotFoundError:
            pass
    payload = {"run_id": run_id, "acquired_at": utc_now_iso(), "provider_write": False, "execution_allowed": False}
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        with os.fdopen(os.open(path, flags), "w", encoding="utf-8") as handle:
            json.dump(payload, handle, separators=(",", ":"), sort_keys=True)
        return True, skipped_due_to_lock
    except FileExistsError:
        return False, True


def _release_lock(base_data_dir: str, run_id: str) -> None:
    path = _lock_path(base_data_dir)
    existing = _read_json(path)
    if isinstance(existing, dict) and existing.get("run_id") == run_id:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def get_institutional_lab_health(*, base_data_dir: str = "data") -> dict[str, Any]:
    base_data_dir = str(resolve_base_data_dir(base_data_dir))
    latest = load_latest_report(base_data_dir=base_data_dir)
    audit = load_audit_records(base_data_dir=base_data_dir, limit=1)
    return {
        "ok": True,
        "status": "ok",
        "sidecar_status": "ready",
        "latest_run_id": latest.get("run_id"),
        "latest_status": latest.get("status", "not_run"),
        "audit_records_count": int(audit.get("total_count", 0)),
        "lock_present": _lock_path(base_data_dir).exists(),
        "storage_backend": "file",
        "storage_health": get_storage_health(),
        "raw_payload_included": False,
        **LAB_SAFETY_FLAGS,
    }


def _status_by_asset(calibration: dict[str, Any]) -> dict[str, str]:
    reports = calibration.get("asset_classes") or {}
    return {asset: str((reports.get(asset) or {}).get("status") or "insufficient_data") for asset in ASSET_CLASSES}


def run_institutional_lab(
    *,
    dry_run: bool = True,
    asset_classes: list[str] | None = None,
    read_existing_outputs_only: bool = True,
    persist_lab_report: bool = True,
    persist_outcomes: bool = False,
    deepseek_review: bool = False,
    execution_simulation: bool = False,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    base_data_dir = str(resolve_base_data_dir(base_data_dir))
    if dry_run is not True:
        raise ValueError("institutional lab only supports dry_run=true")
    if read_existing_outputs_only is not True:
        raise ValueError("institutional lab only supports read_existing_outputs_only=true")
    run_id = f"institutional_lab_{safe_run_id('institutional_lab', utc_now_iso())}"
    lock_acquired, skipped_due_to_lock = _acquire_lock(base_data_dir, run_id)
    if not lock_acquired:
        return {
            "ok": True,
            "status": "skipped_due_to_lock",
            "run_id": run_id,
            "lock_acquired": False,
            "skipped_due_to_lock": skipped_due_to_lock,
            "records_read": 0,
            "records_normalized": 0,
            "duplicate_records_skipped": 0,
            "duplicate_outcomes_skipped": 0,
            "duplicate_simulations_skipped": 0,
            "raw_payload_included": False,
            **LAB_SAFETY_FLAGS,
        }

    try:
        requested = [asset for asset in (asset_classes or list(ASSET_CLASSES)) if asset in ASSET_CLASSES]
        adapter_result = read_existing_outputs(base_data_dir=base_data_dir, asset_classes=requested)
        records = [compact_redact(row) for row in adapter_result.get("records", []) if isinstance(row, dict)]
        calibration = build_calibration_by_asset_class(records)
        risk_results = [assess_institutional_risk(row, calibration_report=calibration) for row in records]
        risk_blocks = sorted({block for result in risk_results for block in result.get("risk_blocks", [])})
        deepseek = {"status": "disabled", "enabled": False, "reviewer_side_effects": "none", "provider_write": False}
        execution_result: dict[str, Any] = {"execution_desk_status": "simulation_only", "simulated_ticket_created": False, "provider_write": False}
        if deepseek_review:
            deepseek = run_deepseek_sidecar_review(
                report={"records": records[:25], "calibration": calibration, "risk_blocks": risk_blocks},
                enabled=True,
                base_data_dir=base_data_dir,
            )
        if execution_simulation and records:
            execution_result = simulate_execution(
                {
                    "simulation_only": True,
                    "live_execution_requested": False,
                    "candidate_id": records[0].get("sidecar_id"),
                    "asset_class": records[0].get("asset_class"),
                    "provider": records[0].get("provider"),
                    "human_command": "simulate_only",
                    "max_theoretical_risk": 0,
                    "submit_live_order": False,
                },
                records=records,
                calibration_report=calibration,
                base_data_dir=base_data_dir,
            )
        result = {
            "ok": True,
            "status": "completed",
            "run_id": run_id,
            "created_at": utc_now_iso(),
            "dry_run": True,
            "read_existing_outputs_only": True,
            "persist_lab_report": bool(persist_lab_report),
            "persist_outcomes": bool(persist_outcomes),
            "outcome_persistence_blocked_reason": "sidecar_default_no_outcome_store_mutation" if persist_outcomes else None,
            "lock_acquired": True,
            "skipped_due_to_lock": False,
            "records_read": int(adapter_result.get("records_read", 0)),
            "records_normalized": int(adapter_result.get("records_normalized", len(records))),
            "records_with_outcomes": len([row for row in records if row.get("final_outcome") is not None or row.get("final_price") is not None]),
            "duplicate_records_skipped": int(adapter_result.get("duplicate_records_skipped", 0)),
            "duplicate_outcomes_skipped": 0,
            "duplicate_simulations_skipped": 0,
            "source_counts": dict(adapter_result.get("source_counts") or {}),
            "unavailable": dict(adapter_result.get("unavailable") or {}),
            "unknown_asset_classes": list(adapter_result.get("unknown_asset_classes") or []),
            "outcome_records_count": int(adapter_result.get("outcome_records_count", 0)),
            "matched_outcomes_count": int(calibration.get("matched_outcomes_count", 0)),
            "status_by_asset_class": _status_by_asset(calibration),
            "calibration": calibration,
            "risk_blocks": risk_blocks,
            "risk_summary": {
                "risk_records_count": len(risk_results),
                "blocked_records_count": len([row for row in risk_results if row.get("risk_blocks")]),
                "top_risk_blocks": risk_blocks[:25],
            },
            "deepseek_review": deepseek,
            "execution_simulation": execution_result,
            "records": records[:250],
            "raw_payload_included": False,
            **LAB_SAFETY_FLAGS,
        }
        audit = append_audit_record(
            action_type="sidecar_run",
            run_id=run_id,
            input_payload={
                "asset_classes": requested,
                "read_existing_outputs_only": True,
                "persist_outcomes": persist_outcomes,
            },
            output_payload={
                "records_normalized": result["records_normalized"],
                "matched_outcomes_count": result["matched_outcomes_count"],
                "status_by_asset_class": result["status_by_asset_class"],
            },
            safety_flags=LAB_SAFETY_FLAGS,
            compact_summary="Institutional sidecar run completed; no provider write.",
            base_data_dir=base_data_dir,
        )
        result["audit_id"] = audit["audit_id"]
        if persist_lab_report:
            result.update(write_run_artifacts(result, base_data_dir=base_data_dir))
            daily = write_daily_report(result, base_data_dir=base_data_dir)
            result["daily_report_path"] = daily.get("daily_report_path")
            result["daily_markdown_path"] = daily.get("daily_markdown_path")
        return compact_redact(result)
    finally:
        _release_lock(base_data_dir, run_id)


def get_institutional_lab_report(*, base_data_dir: str = "data") -> dict[str, Any]:
    base_data_dir = str(resolve_base_data_dir(base_data_dir))
    return load_latest_report(base_data_dir=base_data_dir)


def get_institutional_lab_daily_report(*, base_data_dir: str = "data", report_date: str | None = None) -> dict[str, Any]:
    base_data_dir = str(resolve_base_data_dir(base_data_dir))
    return load_daily_report(base_data_dir=base_data_dir, report_date=report_date)


def get_institutional_lab_audit(*, base_data_dir: str = "data", limit: int = 100) -> dict[str, Any]:
    base_data_dir = str(resolve_base_data_dir(base_data_dir))
    return load_audit_records(base_data_dir=base_data_dir, limit=limit)

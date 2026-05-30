from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .data_paths import resolve_base_data_dir
from .institutional_cross_asset_adapters import compact_redact
from .scheduler_config import hash_payload, safe_run_id, sanitize_filename, utc_now_iso


AUDIT_ACTION_TYPES = {
    "sidecar_run",
    "adapter_normalization",
    "calibration_report",
    "deepseek_review",
    "execution_simulation",
    "risk_check",
    "daily_report",
}


def _audit_dir(base_data_dir: str = "data") -> Path:
    path = resolve_base_data_dir(base_data_dir) / "institutional_lab" / "audit"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _date_from_timestamp(timestamp: str) -> str:
    return str(timestamp)[:10]


def _audit_path(base_data_dir: str, timestamp: str) -> Path:
    return _audit_dir(base_data_dir) / f"{sanitize_filename(_date_from_timestamp(timestamp))}.json"


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _existing_items(path: Path) -> list[dict[str, Any]]:
    payload = _read_json(path)
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return [row for row in payload["items"] if isinstance(row, dict)]
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    return []


def append_audit_record(
    *,
    action_type: str,
    run_id: str | None = None,
    cycle_id: str | None = None,
    asset_class: str | None = None,
    provider: str | None = None,
    source_record_id: str | None = None,
    input_payload: Any = None,
    output_payload: Any = None,
    safety_flags: dict[str, Any] | None = None,
    compact_summary: str | None = None,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    timestamp = utc_now_iso()
    safe_input = compact_redact(input_payload)
    safe_output = compact_redact(output_payload)
    flags = {
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "simulated_ticket_created": False,
        "actual_order_submitted": False,
        "actual_bet_submitted": False,
        "actual_trade_submitted": False,
        "user_command_required": True,
        **dict(safety_flags or {}),
    }
    for key in ("provider_write", "execution_allowed", "live_execution_enabled", "actual_order_submitted", "actual_bet_submitted", "actual_trade_submitted"):
        flags[key] = False
    flags["user_command_required"] = True
    seed = "|".join(
        [
            str(action_type),
            str(run_id or ""),
            str(cycle_id or ""),
            str(source_record_id or ""),
            timestamp,
            hash_payload(safe_input)[:12],
            hash_payload(safe_output)[:12],
        ]
    )
    record = {
        "audit_id": f"audit_{safe_run_id('institutional_audit', seed)}",
        "run_id": run_id,
        "cycle_id": cycle_id,
        "action_type": action_type if action_type in AUDIT_ACTION_TYPES else "sidecar_run",
        "asset_class": asset_class,
        "provider": provider,
        "source_record_id": source_record_id,
        "timestamp": timestamp,
        "input_hash": hash_payload(safe_input),
        "output_hash": hash_payload(safe_output),
        "safety_flags": flags,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "simulated_ticket_created": bool(flags.get("simulated_ticket_created", False)),
        "actual_order_submitted": False,
        "actual_bet_submitted": False,
        "actual_trade_submitted": False,
        "user_command_required": True,
        "compact_summary": str(compact_summary or "")[:500],
    }
    path = _audit_path(base_data_dir, timestamp)
    items = _existing_items(path)
    items.append(record)
    wrapper = {
        "storage_backend": "file",
        "date": _date_from_timestamp(timestamp),
        "last_updated_at": timestamp,
        "count": len(items),
        "items": items,
    }
    _atomic_write_json(path, wrapper)
    return {
        "ok": True,
        "audit_id": record["audit_id"],
        "audit_path": str(path.relative_to(resolve_base_data_dir(base_data_dir))).replace("\\", "/"),
        "record": record,
    }


def load_audit_records(*, base_data_dir: str = "data", limit: int = 100) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for path in sorted(_audit_dir(base_data_dir).glob("*.json")):
        items.extend(_existing_items(path))
    ordered = sorted(items, key=lambda row: str(row.get("timestamp") or ""), reverse=True)
    cap = max(1, min(int(limit or 100), 500))
    return {
        "ok": True,
        "status": "ok",
        "storage_backend": "file",
        "total_count": len(ordered),
        "count": min(len(ordered), cap),
        "items": ordered[:cap],
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "raw_payload_included": False,
    }

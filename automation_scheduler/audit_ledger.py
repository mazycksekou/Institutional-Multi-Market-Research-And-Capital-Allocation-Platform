from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .data_paths import resolve_base_data_dir
from .scheduler_config import hash_payload, safe_run_id, sanitize_filename, utc_now_iso
from .secret_safety import redact_sensitive, secret_safety_fields
from .security_event_types import normalize_event_type
from .security_policy import locked_safety_flags


def _audit_dir(base_data_dir: str | None = None) -> Path:
    path = resolve_base_data_dir(base_data_dir) / "security" / "audit"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _existing_items(path: Path) -> list[dict[str, Any]]:
    payload = _read_json(path)
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return [item for item in payload["items"] if isinstance(item, dict)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def append_security_event(
    *,
    event_type: str,
    actor_type: str = "system",
    actor_provider: str | None = None,
    action_requested: str | None = None,
    action_allowed: bool = False,
    denial_reason: str | None = None,
    asset_type: str | None = None,
    market_type: str | None = None,
    provider_name: str | None = None,
    request_payload: Any = None,
    response_payload: Any = None,
    base_data_dir: str | None = None,
) -> dict[str, Any]:
    timestamp = utc_now_iso()
    safe_request = redact_sensitive(request_payload)
    safe_response = redact_sensitive(response_payload)
    event_type = normalize_event_type(event_type)
    seed = "|".join(
        [
            event_type,
            str(actor_type or "unknown"),
            str(actor_provider or ""),
            str(action_requested or ""),
            timestamp,
            hash_payload(safe_request)[:16],
            hash_payload(safe_response)[:16],
        ]
    )
    event_id = f"security_event_{safe_run_id('security_audit', seed)}"
    record = {
        "event_id": event_id,
        "event_type": event_type,
        "timestamp": timestamp,
        "actor_type": str(actor_type or "unknown"),
        "actor_provider": actor_provider,
        "action_requested": action_requested,
        "action_allowed": False,
        "denial_reason": denial_reason,
        "asset_type": asset_type,
        "market_type": market_type,
        "provider_name": provider_name,
        "request_hash": hash_payload(safe_request),
        "response_hash": hash_payload(safe_response),
        "redacted": True,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "raw_payload_exposed": False,
        "raw_payload_included": False,
        "secrets_detected": False,
        "secrets_included": False,
        **secret_safety_fields(source_payload={"request": request_payload, "response": response_payload}, redacted_payload={"request": safe_request, "response": safe_response}),
    }
    record.update(locked_safety_flags())
    record["action_allowed"] = False
    path = _audit_dir(base_data_dir) / f"{sanitize_filename(timestamp[:10])}.json"
    items = _existing_items(path)
    items.append(record)
    wrapper = {
        "ok": True,
        "status": "ok",
        "storage_backend": "file",
        "date": timestamp[:10],
        "last_updated_at": timestamp,
        "count": len(items),
        "items": items,
        **locked_safety_flags(),
    }
    _atomic_write_json(path, wrapper)
    return {
        "ok": True,
        "status": "audit_record_written",
        "event_id": event_id,
        "audit_path": str(path.relative_to(resolve_base_data_dir(base_data_dir))).replace("\\", "/"),
        "record": record,
        **locked_safety_flags(),
    }


def load_security_audit_records(*, base_data_dir: str | None = None, limit: int = 100) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for path in sorted(_audit_dir(base_data_dir).glob("*.json")):
        items.extend(_existing_items(path))
    ordered = sorted(items, key=lambda item: str(item.get("timestamp") or ""), reverse=True)
    cap = max(1, min(int(limit or 100), 500))
    return {
        "ok": True,
        "status": "ok",
        "storage_backend": "file",
        "total_count": len(ordered),
        "count": min(len(ordered), cap),
        "items": ordered[:cap],
        **locked_safety_flags(),
    }

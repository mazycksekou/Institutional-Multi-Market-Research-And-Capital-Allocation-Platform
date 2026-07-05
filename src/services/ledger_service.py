"""Canonical ledger service helpers for audit and performance records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.services.ledger_support import (
    SCHEMA_VERSION,
    build_context_bucket,
    compact_redact,
    hash_payload,
    redact_sensitive,
    resolve_base_data_dir,
    safe_run_id,
    sanitize_filename,
    secret_safety_fields,
    utc_now_iso,
    normalize_event_type,
    locked_safety_flags,
)


STRATEGY_PERFORMANCE_SCHEMA_VERSION = "automation_scheduler.v1.strategy_performance_ledger.v1"


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


def _audit_dir(base_data_dir: str | None = None) -> Path:
    path = resolve_base_data_dir(base_data_dir) / "security" / "audit"
    path.mkdir(parents=True, exist_ok=True)
    return path


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


def _institutional_audit_dir(base_data_dir: str = "data") -> Path:
    path = resolve_base_data_dir(base_data_dir) / "institutional_lab" / "audit"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _institutional_audit_path(base_data_dir: str, timestamp: str) -> Path:
    return _institutional_audit_dir(base_data_dir) / f"{sanitize_filename(str(timestamp)[:10])}.json"


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
        "action_type": action_type if action_type in {
            "sidecar_run",
            "adapter_normalization",
            "calibration_report",
            "deepseek_review",
            "execution_simulation",
            "risk_check",
            "daily_report",
        } else "sidecar_run",
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
    path = _institutional_audit_path(base_data_dir, timestamp)
    items = _existing_items(path)
    items.append(record)
    wrapper = {
        "storage_backend": "file",
        "date": str(timestamp)[:10],
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
    for path in sorted(_institutional_audit_dir(base_data_dir).glob("*.json")):
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


def _strategy_ledger_path(base_data_dir: str | None = None) -> Path:
    path = resolve_base_data_dir(base_data_dir) / "strategy" / "performance_ledger.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _read_strategy_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    items = payload.get("items") if isinstance(payload, dict) else payload
    return [dict(item) for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _write_strategy_records(path: Path, payload: Mapping[str, Any]) -> None:
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def append_strategy_performance_record(record: Mapping[str, Any], *, base_data_dir: str | None = None, limit: int = 5000) -> dict[str, Any]:
    safe = redact_sensitive(dict(record))
    now = utc_now_iso()
    strategy_id = str(safe.get("strategy_id") or "unknown")
    candidate_id = str(safe.get("candidate_id") or safe.get("ticker") or "unknown")
    item = {
        "ledger_id": safe.get("ledger_id") or f"strategy_perf_{safe_run_id('strategy_perf', strategy_id + candidate_id + now + hash_payload(safe)[:16])}",
        "strategy_id": strategy_id,
        "candidate_id": candidate_id,
        "asset_type": safe.get("asset_type"),
        "market_type": safe.get("market_type"),
        "provider": safe.get("provider"),
        "context_bucket": build_context_bucket(safe),
        "outcome_status": safe.get("outcome_status"),
        "expected_value": safe.get("expected_value"),
        "average_return": safe.get("average_return") or safe.get("return"),
        "average_closing_line_value": safe.get("average_closing_line_value") or safe.get("clv"),
        "false_positive": bool(safe.get("false_positive", False)),
        "false_negative": bool(safe.get("false_negative", False)),
        "settled_at": safe.get("settled_at"),
        "created_at": now,
        "redacted": True,
        **secret_safety_fields(source_payload=record, redacted_payload=safe),
        **locked_safety_flags(),
    }
    path = _strategy_ledger_path(base_data_dir)
    items = _read_strategy_records(path)
    items.append(item)
    cap = max(1, min(int(limit or 5000), 20000))
    items = sorted(items, key=lambda row: str(row.get("created_at") or ""), reverse=True)[:cap]
    wrapper = {"ok": True, "status": "ok", "schema_version": STRATEGY_PERFORMANCE_SCHEMA_VERSION, "count": len(items), "items": items, **locked_safety_flags()}
    _write_strategy_records(path, wrapper)
    return {"ok": True, "status": "strategy_performance_record_written", "ledger_id": item["ledger_id"], "record": item, **locked_safety_flags()}


def load_strategy_performance_ledger(*, base_data_dir: str | None = None, limit: int = 500) -> dict[str, Any]:
    items = _read_strategy_records(_strategy_ledger_path(base_data_dir))
    cap = max(1, min(int(limit or 500), 5000))
    return {
        "ok": True,
        "status": "ok",
        "schema_version": STRATEGY_PERFORMANCE_SCHEMA_VERSION,
        "total_count": len(items),
        "count": min(len(items), cap),
        "items": items[:cap],
        "redacted": True,
        **locked_safety_flags(),
    }


def summarize_strategy_performance(records: list[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    rows = [dict(row) for row in (records or []) if isinstance(row, Mapping)]
    by_strategy: dict[str, dict[str, Any]] = {}
    for row in rows:
        sid = str(row.get("strategy_id") or "unknown")
        bucket = by_strategy.setdefault(sid, {"strategy_id": sid, "sample_size": 0, "false_positive_count": 0, "expected_value_sum": 0.0})
        bucket["sample_size"] += 1
        bucket["false_positive_count"] += 1 if bool(row.get("false_positive")) else 0
        try:
            bucket["expected_value_sum"] += float(row.get("expected_value") or 0.0)
        except (TypeError, ValueError):
            pass
    summaries = []
    for item in by_strategy.values():
        sample = max(1, int(item["sample_size"]))
        summaries.append(
            {
                "strategy_id": item["strategy_id"],
                "sample_size": item["sample_size"],
                "false_positive_rate": item["false_positive_count"] / sample,
                "expected_value": item["expected_value_sum"] / sample,
            }
        )
    return {"ok": True, "status": "strategy_performance_summary", "total_records": len(rows), "strategies": summaries, **locked_safety_flags()}


__all__ = [
    "STRATEGY_PERFORMANCE_SCHEMA_VERSION",
    "append_security_event",
    "load_security_audit_records",
    "append_audit_record",
    "load_audit_records",
    "append_strategy_performance_record",
    "load_strategy_performance_ledger",
    "summarize_strategy_performance",
]

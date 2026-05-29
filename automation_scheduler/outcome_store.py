from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .scheduler_config import SCHEMA_VERSION, safe_run_id, sanitize_filename, utc_now_iso

OUTCOME_SCHEMA_VERSION = f"{SCHEMA_VERSION}.local_outcome_store.v1"
SUPPORTED_OUTCOME_STATUSES = {"settled", "void", "cancelled", "unknown"}
SUPPORTED_FINAL_OUTCOMES = {"yes", "no", "win", "loss", "push", "void", "unknown"}
SUPPORTED_SOURCES = {"local_manual", "imported_file", "test_fixture"}
_SENSITIVE_KEY_PARTS = ("key", "secret", "token", "password", "auth", "credential", "signature", "header")
_RAW_PAYLOAD_KEYS = {
    "provider_payload",
    "raw_payload",
    "external_payload",
    "source_payload",
    "raw_provider_payload",
    "raw_kalshi_payload",
    "raw_sharp_payload",
}


def _outcome_dir(base_data_dir: str = "data") -> Path:
    path = Path(base_data_dir) / "outcomes"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _items_dir(base_data_dir: str = "data") -> Path:
    path = _outcome_dir(base_data_dir) / "items"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _latest_path(base_data_dir: str = "data") -> Path:
    return _outcome_dir(base_data_dir) / "latest.json"


def _legacy_path(base_data_dir: str = "data") -> Path:
    return _outcome_dir(base_data_dir) / "outcomes.json"


def _batch_path(base_data_dir: str, batch_id: str) -> Path:
    return _items_dir(base_data_dir) / f"{sanitize_filename(batch_id)}.json"


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp_path.replace(path)


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _project_relative_path(base_data_dir: str, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path(base_data_dir).resolve())).replace("\\", "/")
    except Exception:
        return path.name


def _safe_scalar(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return None


def _clean_notes(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text[:240] if text else None


def _sanitize_mapping(payload: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in payload.items():
        key_text = str(key)
        lower_key = key_text.lower()
        if lower_key in _RAW_PAYLOAD_KEYS or any(part in lower_key for part in _SENSITIVE_KEY_PARTS):
            continue
        if key_text == "notes":
            cleaned = _clean_notes(value)
            if cleaned is not None:
                safe[key_text] = cleaned
        elif isinstance(value, list):
            safe[key_text] = [_safe_scalar(item) for item in value if _safe_scalar(item) is not None][:25]
        elif isinstance(value, dict):
            safe[key_text] = _sanitize_mapping(value)
        else:
            safe[key_text] = _safe_scalar(value)
    return safe


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _has_matching_key(record: dict[str, Any]) -> bool:
    if record.get("decision_id") or record.get("review_item_id"):
        return True
    ticker = record.get("ticker") or record.get("contract_id")
    if ticker:
        return True
    return bool(record.get("run_id") and ticker)


def _natural_key(record: dict[str, Any]) -> str:
    market_key = record.get("contract_id") or record.get("ticker") or record.get("decision_id") or record.get("review_item_id")
    return "|".join(
        [
            str(record.get("provider") or "unknown"),
            str(record.get("market_type") or "unknown"),
            str(market_key or "unknown"),
            str(record.get("settled_at") or "unknown"),
        ]
    )


def _derive_outcome_id(record: dict[str, Any]) -> str:
    if record.get("outcome_id"):
        return str(record["outcome_id"])
    seed = "|".join(
        [
            _natural_key(record),
            str(record.get("final_outcome") or "unknown"),
            str(record.get("outcome_status") or "unknown"),
        ]
    )
    return f"outcome_{safe_run_id('local_outcome', seed)}"


def validate_outcome_record(
    record: dict[str, Any],
    *,
    source: str = "local_manual",
    now: datetime | None = None,
) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(record, dict):
        return None, "invalid_record_type"
    safe = _sanitize_mapping(record)
    provider = str(safe.get("provider") or "").strip()
    market_type = str(safe.get("market_type") or "").strip()
    if not provider:
        return None, "missing_provider"
    if not market_type:
        return None, "missing_market_type"
    if not _has_matching_key(safe):
        return None, "missing_matching_key"

    outcome_status = str(safe.get("outcome_status") or "unknown").strip().lower()
    final_outcome = str(safe.get("final_outcome") or "unknown").strip().lower()
    if outcome_status not in SUPPORTED_OUTCOME_STATUSES:
        return None, "unsupported_outcome_status"
    if final_outcome not in SUPPORTED_FINAL_OUTCOMES:
        return None, "unsupported_final_outcome"

    settled_at = safe.get("settled_at")
    parsed_settled_at = _parse_datetime(settled_at)
    if outcome_status in {"settled", "void", "cancelled"} and parsed_settled_at is None:
        return None, "missing_or_invalid_settled_at"
    current = now or datetime.now(timezone.utc)
    if parsed_settled_at and parsed_settled_at > current + timedelta(minutes=5):
        return None, "future_settled_at"

    outcome_source = str(safe.get("source") or source or "local_manual").strip().lower()
    if outcome_source not in SUPPORTED_SOURCES:
        return None, "unsupported_source"

    cleaned = {
        "schema_version": OUTCOME_SCHEMA_VERSION,
        "outcome_id": _derive_outcome_id({**safe, "outcome_status": outcome_status, "final_outcome": final_outcome}),
        "provider": provider,
        "market_type": market_type,
        "ticker": safe.get("ticker"),
        "contract_id": safe.get("contract_id"),
        "review_item_id": safe.get("review_item_id"),
        "decision_id": safe.get("decision_id"),
        "run_id": safe.get("run_id"),
        "close_time": safe.get("close_time"),
        "settled_at": settled_at,
        "outcome_status": outcome_status,
        "final_outcome": final_outcome,
        "closing_price": safe.get("closing_price"),
        "settlement_price": safe.get("settlement_price"),
        "source": outcome_source,
        "created_at": safe.get("created_at") or utc_now_iso(),
        "notes": _clean_notes(safe.get("notes")),
    }
    return cleaned, None


def load_outcome_records(base_data_dir: str = "data") -> list[dict[str, Any]]:
    latest = _read_json(_latest_path(base_data_dir))
    if isinstance(latest, dict) and isinstance(latest.get("items"), list):
        return [row for row in latest["items"] if isinstance(row, dict)]
    legacy = _read_json(_legacy_path(base_data_dir))
    if isinstance(legacy, list):
        return [row for row in legacy if isinstance(row, dict)]
    if isinstance(legacy, dict) and isinstance(legacy.get("items"), list):
        return [row for row in legacy["items"] if isinstance(row, dict)]
    return []


def load_outcome_state(base_data_dir: str = "data") -> dict[str, Any]:
    latest_path = _latest_path(base_data_dir)
    latest = _read_json(latest_path)
    if isinstance(latest, dict) and isinstance(latest.get("items"), list):
        items = [row for row in latest["items"] if isinstance(row, dict)]
        return {
            "storage_backend": str(latest.get("storage_backend") or "file"),
            "latest_batch_id": latest.get("latest_batch_id"),
            "last_updated_at": latest.get("last_updated_at"),
            "outcome_read_ok": True,
            "outcome_error_category": None,
            "outcome_read_path": _project_relative_path(base_data_dir, latest_path),
            "items_read_count": len(items),
            "items": items,
        }
    malformed_latest = latest_path.exists() and latest is None
    legacy = _read_json(_legacy_path(base_data_dir))
    if isinstance(legacy, list):
        items = [row for row in legacy if isinstance(row, dict)]
        return {
            "storage_backend": "file",
            "latest_batch_id": None,
            "last_updated_at": None,
            "outcome_read_ok": True,
            "outcome_error_category": None,
            "outcome_read_path": _project_relative_path(base_data_dir, _legacy_path(base_data_dir)),
            "items_read_count": len(items),
            "items": items,
        }
    return {
        "storage_backend": "file",
        "latest_batch_id": None,
        "last_updated_at": None,
        "outcome_read_ok": not malformed_latest,
        "outcome_error_category": "malformed_latest_outcome_file" if malformed_latest else None,
        "outcome_read_path": None,
        "items_read_count": 0,
        "items": [],
    }


def _dedupe_records(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    by_id = {str(row.get("outcome_id")): row for row in existing if isinstance(row, dict) and row.get("outcome_id")}
    natural_keys = {_natural_key(row) for row in existing if isinstance(row, dict)}
    accepted: list[dict[str, Any]] = []
    duplicate_count = 0
    for row in incoming:
        outcome_id = str(row.get("outcome_id"))
        natural = _natural_key(row)
        if outcome_id in by_id or natural in natural_keys:
            duplicate_count += 1
            continue
        by_id[outcome_id] = row
        natural_keys.add(natural)
        accepted.append(row)
    all_rows = sorted(by_id.values(), key=lambda item: (str(item.get("settled_at") or ""), str(item.get("outcome_id") or "")))
    return all_rows, accepted, duplicate_count


def _write_outcome_state(base_data_dir: str, *, batch_id: str, all_items: list[dict[str, Any]], batch_items: list[dict[str, Any]]) -> dict[str, Any]:
    now = utc_now_iso()
    wrapper = {
        "schema_version": OUTCOME_SCHEMA_VERSION,
        "storage_backend": "file",
        "latest_batch_id": batch_id,
        "last_updated_at": now,
        "items_written_count": len(batch_items),
        "total_count": len(all_items),
        "items": all_items,
    }
    batch_wrapper = {
        **wrapper,
        "items": batch_items,
        "batch_count": len(batch_items),
    }
    latest_path = _latest_path(base_data_dir)
    batch_path = _batch_path(base_data_dir, batch_id)
    _atomic_write_json(latest_path, wrapper)
    _atomic_write_json(batch_path, batch_wrapper)
    _atomic_write_json(_legacy_path(base_data_dir), all_items)
    return {
        "storage_backend": "file",
        "latest_batch_id": batch_id,
        "last_updated_at": now,
        "outcome_write_path": _project_relative_path(base_data_dir, latest_path),
        "outcome_items_batch_path": _project_relative_path(base_data_dir, batch_path),
        "outcome_records_written": len(batch_items),
        "total_count": len(all_items),
    }


def summarize_outcomes(records: list[dict[str, Any]]) -> dict[str, Any]:
    provider_counts: dict[str, int] = {}
    outcome_status_counts: dict[str, int] = {}
    final_outcome_counts: dict[str, int] = {}
    for row in records:
        provider = str(row.get("provider") or "unknown")
        provider_counts[provider] = provider_counts.get(provider, 0) + 1
        status = str(row.get("outcome_status") or "unknown")
        outcome_status_counts[status] = outcome_status_counts.get(status, 0) + 1
        final = str(row.get("final_outcome") or "unknown")
        final_outcome_counts[final] = final_outcome_counts.get(final, 0) + 1
    return {
        "total_count": len(records),
        "provider_counts": provider_counts,
        "outcome_status_counts": outcome_status_counts,
        "final_outcome_counts": final_outcome_counts,
    }


def ingest_outcome_records(
    records: list[dict[str, Any]] | None,
    *,
    source: str = "local_manual",
    dry_run: bool = True,
    persist: bool = False,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    rows = [row for row in (records or []) if isinstance(row, dict)]
    rejected_reason_counts: dict[str, int] = {}
    valid_rows: list[dict[str, Any]] = []
    for row in rows:
        cleaned, reason = validate_outcome_record(row, source=source)
        if reason:
            rejected_reason_counts[reason] = rejected_reason_counts.get(reason, 0) + 1
            continue
        valid_rows.append(cleaned or {})

    existing = load_outcome_records(base_data_dir)
    all_rows, batch_rows, duplicate_count = _dedupe_records(existing, valid_rows)
    if duplicate_count:
        rejected_reason_counts["duplicate_outcome"] = rejected_reason_counts.get("duplicate_outcome", 0) + duplicate_count

    should_persist = bool(persist)
    batch_id = f"outcome_batch_{safe_run_id('outcome_batch', utc_now_iso() + str(len(batch_rows)))}"
    storage: dict[str, Any] = {
        "storage_backend": "file",
        "latest_batch_id": None,
        "last_updated_at": None,
        "outcome_write_path": None,
        "outcome_records_written": 0,
        "total_count": len(existing),
    }
    if should_persist and batch_rows:
        storage = _write_outcome_state(base_data_dir, batch_id=batch_id, all_items=all_rows, batch_items=batch_rows)

    return {
        "ok": True,
        "status": "outcomes_ingested" if should_persist and batch_rows else "outcomes_validated",
        "dry_run": bool(dry_run),
        "local_persistence": bool(should_persist and batch_rows),
        "persisted": bool(should_persist and batch_rows),
        "provider_write": False,
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "records_received": len(rows),
        "records_valid": len(valid_rows),
        "records_rejected": sum(rejected_reason_counts.values()),
        "rejected_reason_counts": rejected_reason_counts,
        "duplicate_count": duplicate_count,
        "outcome_records_written": int(storage.get("outcome_records_written", 0)),
        "storage_backend": storage.get("storage_backend", "file"),
        "latest_batch_id": storage.get("latest_batch_id"),
        "last_updated_at": storage.get("last_updated_at"),
        "outcome_write_path": storage.get("outcome_write_path"),
        "total_count": storage.get("total_count", len(existing)),
        "accepted_records": batch_rows,
    }

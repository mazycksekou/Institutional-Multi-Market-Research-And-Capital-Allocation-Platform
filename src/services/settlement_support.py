from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from src.services.runtime_shared import resolve_base_data_dir, sanitize_filename, utc_now_iso


OUTCOME_SCHEMA_VERSION = "src.services.settlement_support.v1"
SUPPORTED_OUTCOME_STATUSES = {"settled", "void", "cancelled"}
SUPPORTED_FINAL_OUTCOMES = {"yes", "no", "win", "loss", "push", "void"}
SUPPORTED_SOURCES = {"local_manual", "imported_file", "test_fixture", "read_only_settlement"}
PERSISTABLE_SOURCES = {"local_manual", "imported_file", "read_only_settlement"}

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
    from src.services.runtime_shared import safe_run_id

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
        "evidence_type": safe.get("evidence_type"),
        "evidence_summary": _clean_notes(safe.get("evidence_summary")),
        "created_at": safe.get("created_at") or utc_now_iso(),
        "notes": _clean_notes(safe.get("notes")),
    }
    return cleaned, None


__all__ = [
    "OUTCOME_SCHEMA_VERSION",
    "PERSISTABLE_SOURCES",
    "SUPPORTED_FINAL_OUTCOMES",
    "SUPPORTED_OUTCOME_STATUSES",
    "SUPPORTED_SOURCES",
    "resolve_base_data_dir",
    "sanitize_filename",
    "utc_now_iso",
    "validate_outcome_record",
]

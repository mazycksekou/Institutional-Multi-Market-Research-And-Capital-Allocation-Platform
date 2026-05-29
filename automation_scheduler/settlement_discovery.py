from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .kalshi_readonly_adapter import KalshiReadonlyAdapter
from .outcome_store import PERSISTABLE_SOURCES, validate_outcome_record
from .scheduler_config import sanitize_filename, utc_now_iso

READ_ONLY_SETTLEMENT_SOURCE = "read_only_settlement"

_KALSHI_PROVIDER = "kalshi_prediction_market"
_RESULT_FIELDS = (
    "settlement_result",
    "settlementResult",
    "result",
    "outcome",
    "final_outcome",
    "finalOutcome",
    "settled_outcome",
    "settledOutcome",
    "winning_side",
    "winningSide",
)
_STATUS_FIELDS = (
    "settlement_status",
    "settlementStatus",
    "status",
    "market_status",
    "marketStatus",
)
_SETTLED_STATUS_VALUES = {"settled", "final", "resolved", "closed", "expired"}
_NOT_SETTLED_STATUS_VALUES = {"open", "active", "initialized", "trading", "not_settled", "unsettled"}
_VOID_STATUS_VALUES = {"void", "cancelled", "canceled"}


def _outcome_dir(base_data_dir: str) -> Path:
    path = Path(base_data_dir) / "outcomes"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _norm(value: Any) -> str:
    return _safe_text(value).lower().replace("-", "_").replace(" ", "_")


def _market_keys(row: dict[str, Any]) -> set[str]:
    keys: set[str] = set()
    for name in ("contract_id", "contractId", "ticker", "market_ticker", "marketTicker", "market_id", "marketId"):
        value = row.get(name)
        if value:
            keys.add(str(value).strip().lower())
    return keys


def load_pending_outcome_rows(base_data_dir: str = "data") -> list[dict[str, Any]]:
    rows = _read_json(_outcome_dir(base_data_dir) / "pending_real_outcomes.local.json")
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def load_imported_outcome_rows(base_data_dir: str = "data") -> list[dict[str, Any]]:
    rows = _read_json(_outcome_dir(base_data_dir) / "import_outcomes.local.json")
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def summarize_pending_outcome_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "pending_rows_count": len(rows),
        "completed_rows_count": sum(1 for row in rows if row.get("outcome_status") and row.get("final_outcome") and row.get("settled_at")),
        "rows_with_decision_id": sum(1 for row in rows if row.get("decision_id")),
        "rows_with_review_item_id": sum(1 for row in rows if row.get("review_item_id")),
        "rows_with_ticker": sum(1 for row in rows if row.get("ticker")),
        "rows_with_contract_id": sum(1 for row in rows if row.get("contract_id")),
        "rows_missing_outcome_status": sum(1 for row in rows if not row.get("outcome_status")),
        "rows_missing_final_outcome": sum(1 for row in rows if not row.get("final_outcome")),
        "rows_missing_settled_at": sum(1 for row in rows if not row.get("settled_at")),
    }


def _first_field(row: dict[str, Any], field_names: tuple[str, ...]) -> tuple[str | None, Any]:
    for name in field_names:
        if row.get(name) not in (None, ""):
            return name, row.get(name)
    source = row.get("source_payload_redacted")
    if isinstance(source, dict):
        for name in field_names:
            if source.get(name) not in (None, ""):
                return name, source.get(name)
    return None, None


def _normalize_result(value: Any) -> str | None:
    text = _norm(value)
    if text in {"yes", "y", "true", "1", "yes_won", "yes_win"}:
        return "yes"
    if text in {"no", "n", "false", "0", "no_won", "no_win"}:
        return "no"
    if text in _VOID_STATUS_VALUES or text == "voided":
        return "void"
    return None


def classify_kalshi_settlement(record: dict[str, Any]) -> dict[str, Any]:
    result_field, result_value = _first_field(record, _RESULT_FIELDS)
    status_field, status_value = _first_field(record, _STATUS_FIELDS)
    normalized_result = _normalize_result(result_value)
    normalized_status = _norm(status_value)
    evidence_fields = [field for field in (result_field, status_field) if field]

    if normalized_result in {"yes", "no"}:
        return {
            "classification": f"settled_{normalized_result}",
            "outcome_status": "settled",
            "final_outcome": normalized_result,
            "evidence_type": "explicit_settlement_field",
            "evidence_fields": evidence_fields,
        }
    if normalized_result == "void" or normalized_status in _VOID_STATUS_VALUES:
        return {
            "classification": "void_or_cancelled",
            "outcome_status": "void" if normalized_status != "cancelled" else "cancelled",
            "final_outcome": "void",
            "evidence_type": "explicit_settlement_field",
            "evidence_fields": evidence_fields,
        }
    if normalized_status in _NOT_SETTLED_STATUS_VALUES:
        return {
            "classification": "not_settled",
            "outcome_status": None,
            "final_outcome": None,
            "evidence_type": "status_field_only",
            "evidence_fields": evidence_fields,
        }
    if normalized_status in _SETTLED_STATUS_VALUES:
        return {
            "classification": "unknown",
            "outcome_status": None,
            "final_outcome": None,
            "evidence_type": "closed_without_explicit_result",
            "evidence_fields": evidence_fields,
        }
    return {
        "classification": "unknown",
        "outcome_status": None,
        "final_outcome": None,
        "evidence_type": "missing_explicit_settlement_field",
        "evidence_fields": evidence_fields,
    }


def _candidate_from_pending(pending: dict[str, Any], classification: dict[str, Any], record: dict[str, Any]) -> dict[str, Any] | None:
    final_outcome = classification.get("final_outcome")
    outcome_status = classification.get("outcome_status")
    if not final_outcome or not outcome_status:
        return None
    settled_at = (
        record.get("settlement_time")
        or record.get("settled_at")
        or record.get("expiration_time")
        or record.get("close_time")
        or pending.get("close_time")
    )
    if not settled_at:
        return None
    return {
        "provider": _KALSHI_PROVIDER,
        "market_type": pending.get("market_type") or "prediction_market",
        "decision_id": pending.get("decision_id"),
        "review_item_id": pending.get("review_item_id"),
        "run_id": pending.get("run_id"),
        "ticker": pending.get("ticker") or record.get("ticker"),
        "contract_id": pending.get("contract_id") or record.get("contract_id"),
        "outcome_status": outcome_status,
        "final_outcome": final_outcome,
        "settled_at": settled_at,
        "source": READ_ONLY_SETTLEMENT_SOURCE,
        "evidence_type": classification.get("evidence_type"),
        "evidence_summary": "field_names:" + ",".join(classification.get("evidence_fields", [])[:6]),
        "notes": "Read-only explicit settlement field; provider_write=false.",
    }


def discover_kalshi_settlements_for_pending_rows(
    pending_rows: list[dict[str, Any]],
    *,
    read_only_records: list[dict[str, Any]] | None = None,
    adapter: KalshiReadonlyAdapter | None = None,
) -> dict[str, Any]:
    kalshi_rows = [row for row in pending_rows if str(row.get("provider") or "").lower() == _KALSHI_PROVIDER]
    snapshot_status = None
    blockers: list[str] = []
    if read_only_records is None:
        snapshot = (adapter or KalshiReadonlyAdapter()).fetch_snapshot()
        snapshot_status = snapshot.get("status")
        blockers = list(snapshot.get("blockers", []))[:10]
        read_only_records = [row for row in snapshot.get("records", []) if isinstance(row, dict)]

    record_lookup: dict[str, dict[str, Any]] = {}
    for record in read_only_records or []:
        for key in _market_keys(record):
            record_lookup[key] = record

    classification_counts: Counter[str] = Counter()
    rejected_reason_counts: Counter[str] = Counter()
    completion_candidates: list[dict[str, Any]] = []
    matched_count = 0
    field_presence: Counter[str] = Counter()
    for row in kalshi_rows:
        matched_record = None
        for key in _market_keys(row):
            if key in record_lookup:
                matched_record = record_lookup[key]
                break
        if matched_record is None:
            rejected_reason_counts["no_read_only_record_match"] += 1
            classification_counts["unknown"] += 1
            continue
        matched_count += 1
        for field in (*_RESULT_FIELDS, *_STATUS_FIELDS):
            if matched_record.get(field) not in (None, ""):
                field_presence[field] += 1
            source = matched_record.get("source_payload_redacted")
            if isinstance(source, dict) and source.get(field) not in (None, ""):
                field_presence[field] += 1
        classification = classify_kalshi_settlement(matched_record)
        class_name = str(classification.get("classification") or "unknown")
        classification_counts[class_name] += 1
        candidate = _candidate_from_pending(row, classification, matched_record)
        if candidate is not None:
            completion_candidates.append(candidate)
        elif class_name == "unknown":
            rejected_reason_counts[str(classification.get("evidence_type") or "unknown_settlement")] += 1
        elif class_name == "not_settled":
            rejected_reason_counts["not_settled"] += 1

    return {
        "ok": True,
        "status": "settlement_discovery_complete",
        "provider_write": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "snapshot_status": snapshot_status,
        "blockers": blockers,
        "pending_kalshi_rows": len(kalshi_rows),
        "read_only_records_checked": len(read_only_records or []),
        "read_only_records_matched": matched_count,
        "settled_yes_count": int(classification_counts.get("settled_yes", 0)),
        "settled_no_count": int(classification_counts.get("settled_no", 0)),
        "not_settled_count": int(classification_counts.get("not_settled", 0)),
        "unknown_count": int(classification_counts.get("unknown", 0)),
        "void_cancelled_count": int(classification_counts.get("void_or_cancelled", 0)),
        "completion_candidates_count": len(completion_candidates),
        "rejected_reason_counts": dict(rejected_reason_counts),
        "settlement_field_presence_counts": dict(field_presence),
        "completion_candidates": completion_candidates,
    }


def validate_imported_outcome_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid: list[dict[str, Any]] = []
    rejected_reason_counts: Counter[str] = Counter()
    for row in rows:
        cleaned, reason = validate_outcome_record(row, source=str(row.get("source") or "imported_file"))
        source = str((cleaned or row).get("source") or "").lower()
        if cleaned and source not in PERSISTABLE_SOURCES:
            reason = "non_real_source_not_persistable"
            cleaned = None
        if reason:
            rejected_reason_counts[str(reason)] += 1
            continue
        valid.append(cleaned or {})
    return {
        "rows_found": len(rows),
        "valid_rows": len(valid),
        "rejected_rows": int(sum(rejected_reason_counts.values())),
        "rejected_reason_counts": dict(rejected_reason_counts),
        "completion_candidates": valid,
    }


def build_outcome_completion_report(
    *,
    pending_rows: list[dict[str, Any]] | None = None,
    imported_rows: list[dict[str, Any]] | None = None,
    read_only_records: list[dict[str, Any]] | None = None,
    adapter: KalshiReadonlyAdapter | None = None,
    base_data_dir: str = "data",
    use_kalshi_snapshot: bool = True,
) -> dict[str, Any]:
    pending = list(pending_rows if pending_rows is not None else load_pending_outcome_rows(base_data_dir))
    imported = list(imported_rows if imported_rows is not None else load_imported_outcome_rows(base_data_dir))
    discovery = discover_kalshi_settlements_for_pending_rows(
        pending,
        read_only_records=read_only_records if read_only_records is not None or not use_kalshi_snapshot else None,
        adapter=adapter,
    ) if use_kalshi_snapshot or read_only_records is not None else discover_kalshi_settlements_for_pending_rows(pending, read_only_records=[])
    imported_result = validate_imported_outcome_rows(imported)
    candidates = list(discovery.get("completion_candidates", [])) + list(imported_result.get("completion_candidates", []))
    return {
        "ok": True,
        "status": "completion_candidates_ready" if candidates else "no_completion_candidates",
        "provider_write": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "pending_diagnostics": summarize_pending_outcome_rows(pending),
        "kalshi_discovery": {k: v for k, v in discovery.items() if k != "completion_candidates"},
        "imported_file": {k: v for k, v in imported_result.items() if k != "completion_candidates"},
        "completion_candidates_count": len(candidates),
        "completion_candidates": candidates,
    }


def write_outcome_completion_candidates(report: dict[str, Any], base_data_dir: str = "data") -> dict[str, Any]:
    out_dir = _outcome_dir(base_data_dir)
    candidates = list(report.get("completion_candidates", []))
    payload = {
        "created_at": utc_now_iso(),
        "status": report.get("status"),
        "provider_write": False,
        "completion_candidates_count": len(candidates),
        "completion_candidates": candidates,
        "diagnostics": {
            "pending_diagnostics": report.get("pending_diagnostics", {}),
            "kalshi_discovery": report.get("kalshi_discovery", {}),
            "imported_file": report.get("imported_file", {}),
        },
    }
    path = out_dir / "outcome_completion_candidates.local.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return {"completion_candidate_path": str(path).replace("\\", "/"), "completion_candidates_count": len(candidates)}

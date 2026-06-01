from __future__ import annotations

import json
import urllib.request
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .calibration import _match_rank
from .data_paths import get_storage_health, resolve_base_data_dir
from .outcome_store import ingest_outcome_records, load_outcome_records, validate_outcome_record
from .paper_decision_ledger import load_paper_decisions
from .scheduler_config import SCHEMA_VERSION, safe_run_id, sanitize_filename, utc_now_iso


MIGRATION_VERSION = "kalshi_outcome_migration_v1"
MIGRATED_FROM = "local_repo_data"
KALSHI_PROVIDER = "kalshi_prediction_market"
PREDICTION_MARKET = "prediction_market"
MIGRATION_SCHEMA_VERSION = f"{SCHEMA_VERSION}.kalshi_outcome_migration.v1"

RAW_PAYLOAD_KEYS = {
    "provider_payload",
    "raw_payload",
    "external_payload",
    "source_payload",
    "source_payload_redacted",
    "raw_provider_payload",
    "raw_kalshi_payload",
    "raw_sharp_payload",
    "provider_request",
    "provider_response",
    "request_body",
    "response_body",
    "headers",
    "authorization_header",
    "signed_url",
}
SECRET_KEY_PARTS = ("key", "secret", "token", "password", "auth", "credential", "signature", "private")
UNSAFE_EXECUTION_FIELDS = {
    "provider_write",
    "execution_allowed",
    "live_execution_enabled",
    "auto_execution_enabled",
    "auto_bet_enabled",
    "auto_trade_enabled",
    "kalshi_order_execution_enabled",
    "sportsbook_bet_execution_enabled",
    "broker_order_execution_enabled",
    "crypto_trade_execution_enabled",
    "stock_trade_execution_enabled",
    "submit_live_order",
    "submit_live_bet",
    "submit_live_trade",
    "submit_order",
    "submit_bet",
    "submit_trade",
}
ALLOWED_OUTCOME_SOURCES = {"read_only_settlement", "local_manual", "imported_file"}
MIGRATION_OUTCOME_FIELDS = {
    "source",
    "provider",
    "provider_id",
    "market_type",
    "ticker",
    "market_id",
    "contract_id",
    "event_id",
    "final_outcome",
    "outcome_status",
    "settled_at",
    "original_run_id",
    "source_run_id",
    "run_id",
    "batch_id",
    "paper_decision_id",
    "review_decision_id",
    "decision_id",
    "review_item_id",
    "selection",
    "contract_title",
    "close_time",
    "normalized_identity",
    "migrated_from",
    "migration_version",
    "evidence_type",
    "evidence_summary",
}
PAPER_DECISION_FIELDS = {
    "schema_version",
    "decision_id",
    "run_id",
    "review_item_id",
    "provider",
    "source_type",
    "market_type",
    "ticker",
    "contract_id",
    "event",
    "title",
    "observed_price",
    "price_source",
    "implied_probability",
    "liquidity_tier",
    "liquidity_score",
    "spread_score",
    "pricing_quality_score",
    "risk_score",
    "confidence_score",
    "review_priority_score",
    "reason_codes",
    "recommendation_status",
    "execution_allowed",
    "paper_only",
    "created_at",
    "snapshot_id",
    "report_path",
    "close_time",
    "outcome_status",
    "settled_at",
    "final_outcome",
    "paper_result",
    "paper_roi_estimate",
    "calibration_bucket",
    "migrated_from",
    "migration_version",
}


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _items_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return [row for row in payload["items"] if isinstance(row, dict)]
    return []


def _source_paths(default_dir: Path, explicit: list[str | Path] | None) -> list[Path]:
    if explicit is not None:
        return [Path(path) for path in explicit]
    paths: list[Path] = []
    paths.extend(sorted((default_dir / "items").glob("*.json")) if (default_dir / "items").exists() else [])
    for name in ("outcomes.json", "latest.json", "paper_decisions.json"):
        candidate = default_dir / name
        if candidate.exists():
            paths.append(candidate)
    return paths


def _batch_id_from_payload(path: Path, payload: Any) -> str:
    if isinstance(payload, dict):
        for key in ("latest_batch_id", "batch_id", "run_id", "latest_run_id"):
            if payload.get(key):
                return str(payload[key])
    return path.stem


def _has_forbidden_key(value: Any) -> tuple[bool, str | None]:
    if isinstance(value, dict):
        for key, item in value.items():
            text = str(key)
            lower = text.lower()
            if lower in RAW_PAYLOAD_KEYS:
                return True, "raw_payload_field_rejected"
            if any(part in lower for part in SECRET_KEY_PARTS):
                return True, "secret_like_field_rejected"
            found, reason = _has_forbidden_key(item)
            if found:
                return found, reason
    elif isinstance(value, list):
        for item in value:
            found, reason = _has_forbidden_key(item)
            if found:
                return found, reason
    return False, None


def _has_inference_marker(record: dict[str, Any]) -> bool:
    text = " ".join(str(record.get(key) or "") for key in ("source", "evidence_type", "evidence_summary", "notes")).lower()
    if "infer" in text:
        return True
    return any(bool(record.get(key)) for key in ("infer_outcomes", "inferred_outcomes", "allow_inferred_outcomes"))


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _market_key(record: dict[str, Any]) -> str:
    return str(record.get("ticker") or record.get("contract_id") or record.get("market_id") or "").strip()


def _clean_scalar(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return None


def _compact_reason_codes(value: Any) -> list[Any]:
    if not isinstance(value, list):
        return []
    return [_clean_scalar(item) for item in value if _clean_scalar(item) is not None][:25]


def _clean_paper_decision(record: dict[str, Any]) -> dict[str, Any]:
    cleaned = {key: _clean_scalar(record.get(key)) for key in PAPER_DECISION_FIELDS if key in record and key != "reason_codes"}
    if "reason_codes" in record:
        cleaned["reason_codes"] = _compact_reason_codes(record.get("reason_codes"))
    cleaned["provider"] = cleaned.get("provider") or record.get("provider_id") or KALSHI_PROVIDER
    cleaned["market_type"] = cleaned.get("market_type") or PREDICTION_MARKET
    cleaned["source_type"] = cleaned.get("source_type") or PREDICTION_MARKET
    cleaned["execution_allowed"] = False
    cleaned["paper_only"] = True
    cleaned["migrated_from"] = MIGRATED_FROM
    cleaned["migration_version"] = MIGRATION_VERSION
    return {key: value for key, value in cleaned.items() if value is not None}


def _paper_decision_key(record: dict[str, Any]) -> str:
    if record.get("decision_id"):
        return f"decision:{record.get('decision_id')}"
    return "|".join(
        [
            str(record.get("run_id") or ""),
            str(record.get("review_item_id") or ""),
            str(record.get("provider") or record.get("provider_id") or ""),
            str(record.get("market_type") or record.get("source_type") or ""),
            _market_key(record),
        ]
    )


def discover_local_outcome_records(source_paths: list[str | Path] | None = None) -> dict[str, Any]:
    base = resolve_base_data_dir("data")
    paths = _source_paths(base / "outcomes", source_paths)
    records: list[dict[str, Any]] = []
    for path in paths:
        payload = _read_json(path)
        batch_id = _batch_id_from_payload(path, payload)
        for row in _items_from_payload(payload):
            copy = dict(row)
            copy["_source_path"] = str(path)
            copy["_batch_id"] = batch_id
            records.append(copy)
    return {
        "ok": True,
        "status": "ok",
        "records": records,
        "records_found": len(records),
        "source_paths": [str(path) for path in paths],
        "raw_payload_included": False,
        "secrets_included": False,
    }


def discover_local_paper_decisions(source_paths: list[str | Path] | None = None) -> dict[str, Any]:
    base = resolve_base_data_dir("data")
    paths = _source_paths(base / "paper_ledger", source_paths)
    decisions: list[dict[str, Any]] = []
    for path in paths:
        payload = _read_json(path)
        for row in _items_from_payload(payload):
            copy = dict(row)
            copy["_source_path"] = str(path)
            decisions.append(copy)
    return {
        "ok": True,
        "status": "ok",
        "records": decisions,
        "records_found": len(decisions),
        "source_paths": [str(path) for path in paths],
        "raw_payload_included": False,
        "secrets_included": False,
    }


def build_outcome_identity(record: dict[str, Any]) -> str:
    provider = str(record.get("provider_id") or record.get("provider") or KALSHI_PROVIDER).strip()
    market_key = _market_key(record)
    final = str(record.get("final_outcome") or "").strip().lower()
    settled = str(record.get("settled_at") or "").strip()
    if provider and market_key:
        return f"{provider}|{market_key}"
    return f"{provider}|{market_key}|{final}|{settled}"


def normalize_migration_outcome(record: dict[str, Any]) -> dict[str, Any]:
    provider = str(record.get("provider_id") or record.get("provider") or KALSHI_PROVIDER).strip()
    ticker = record.get("ticker") or record.get("contract_id") or record.get("market_id")
    contract_id = record.get("contract_id") or record.get("ticker") or record.get("market_id")
    normalized = {
        "source": str(record.get("source") or "read_only_settlement").strip(),
        "provider_id": provider,
        "market_type": str(record.get("market_type") or PREDICTION_MARKET).strip(),
        "ticker": _clean_scalar(ticker),
        "market_id": _clean_scalar(record.get("market_id")),
        "contract_id": _clean_scalar(contract_id),
        "event_id": _clean_scalar(record.get("event_id")),
        "final_outcome": str(record.get("final_outcome") or "").strip().lower(),
        "outcome_status": str(record.get("outcome_status") or "").strip().lower(),
        "settled_at": _clean_scalar(record.get("settled_at")),
        "original_run_id": _clean_scalar(record.get("original_run_id") or record.get("run_id")),
        "source_run_id": _clean_scalar(record.get("source_run_id") or record.get("run_id")),
        "batch_id": _clean_scalar(record.get("batch_id") or record.get("_batch_id")),
        "paper_decision_id": _clean_scalar(record.get("paper_decision_id") or record.get("decision_id")),
        "review_decision_id": _clean_scalar(record.get("review_decision_id") or record.get("review_item_id")),
        "selection": _clean_scalar(record.get("selection") or record.get("contract_title")),
        "close_time": _clean_scalar(record.get("close_time")),
        "evidence_type": _clean_scalar(record.get("evidence_type")),
        "evidence_summary": _clean_scalar(record.get("evidence_summary")),
        "migrated_from": MIGRATED_FROM,
        "migration_version": MIGRATION_VERSION,
    }
    normalized["normalized_identity"] = build_outcome_identity(normalized)
    return {key: value for key, value in normalized.items() if value not in (None, "")}


def validate_migration_outcome(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        return {"ok": False, "reason": "invalid_record_type", "record": None}
    found_forbidden, forbidden_reason = _has_forbidden_key(record)
    if found_forbidden:
        return {"ok": False, "reason": forbidden_reason, "record": None}
    for field in UNSAFE_EXECUTION_FIELDS:
        if record.get(field) is True:
            return {"ok": False, "reason": f"{field}_rejected", "record": None}
    if _has_inference_marker(record):
        return {"ok": False, "reason": "inferred_outcomes_rejected", "record": None}

    normalized = normalize_migration_outcome(record)
    unknown_fields = sorted(set(normalized) - MIGRATION_OUTCOME_FIELDS)
    if unknown_fields:
        return {"ok": False, "reason": "unexpected_field", "record": None, "fields": unknown_fields}
    if normalized.get("provider_id") != KALSHI_PROVIDER:
        return {"ok": False, "reason": "unsupported_provider", "record": None}
    if normalized.get("final_outcome") not in {"yes", "no"}:
        return {"ok": False, "reason": "unsupported_final_outcome", "record": None}
    if normalized.get("outcome_status") != "settled":
        return {"ok": False, "reason": "unsupported_outcome_status", "record": None}
    if normalized.get("source") not in ALLOWED_OUTCOME_SOURCES:
        return {"ok": False, "reason": "unsupported_source", "record": None}
    if normalized.get("source") != "read_only_settlement" and normalized.get("evidence_type") != "explicit_settlement_field":
        return {"ok": False, "reason": "non_read_only_source_requires_explicit_evidence", "record": None}
    if not _market_key(normalized):
        return {"ok": False, "reason": "missing_matching_key", "record": None}
    if not _parse_time(normalized.get("settled_at")):
        return {"ok": False, "reason": "missing_or_invalid_settled_at", "record": None}

    compatible = {
        "provider": normalized["provider_id"],
        "market_type": normalized["market_type"],
        "ticker": normalized.get("ticker"),
        "contract_id": normalized.get("contract_id"),
        "review_item_id": normalized.get("review_decision_id"),
        "decision_id": normalized.get("paper_decision_id"),
        "run_id": normalized.get("source_run_id"),
        "close_time": normalized.get("close_time"),
        "outcome_status": normalized.get("outcome_status"),
        "final_outcome": normalized.get("final_outcome"),
        "settled_at": normalized.get("settled_at"),
        "source": normalized.get("source"),
        "evidence_type": normalized.get("evidence_type"),
        "evidence_summary": normalized.get("evidence_summary"),
    }
    cleaned, reason = validate_outcome_record(compatible, source=str(normalized.get("source")))
    if reason:
        return {"ok": False, "reason": reason, "record": None}
    return {"ok": True, "reason": None, "record": normalized}


def dedupe_migration_outcomes(records: list[dict[str, Any]]) -> dict[str, Any]:
    rejected_reason_counts: Counter[str] = Counter()
    rejected_records: list[dict[str, Any]] = []
    by_identity: dict[str, dict[str, Any]] = {}
    duplicate_count = 0
    for record in records:
        validation = validate_migration_outcome(record)
        if not validation["ok"]:
            reason = str(validation.get("reason") or "invalid")
            rejected_reason_counts[reason] += 1
            rejected_records.append({"reason": reason})
            continue
        normalized = dict(validation["record"])
        identity = str(normalized["normalized_identity"])
        existing = by_identity.get(identity)
        if existing is None:
            by_identity[identity] = normalized
            continue
        duplicate_count += 1
        if (
            existing.get("final_outcome") != normalized.get("final_outcome")
            or existing.get("settled_at") != normalized.get("settled_at")
        ):
            rejected_reason_counts["duplicate_identity_conflict"] += 1
            rejected_records.append({"reason": "duplicate_identity_conflict", "normalized_identity": identity})
    rows = sorted(by_identity.values(), key=lambda row: (str(row.get("settled_at") or ""), str(row.get("normalized_identity") or "")))
    return {
        "ok": not rejected_reason_counts.get("duplicate_identity_conflict", 0),
        "status": "ok" if not rejected_reason_counts else "validated_with_rejections",
        "records": rows,
        "records_valid": len(rows),
        "records_rejected": sum(rejected_reason_counts.values()),
        "rejected_reason_counts": dict(rejected_reason_counts),
        "duplicate_count": duplicate_count,
        "rejected_records": rejected_records,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def _matching_paper_decisions(outcomes: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for outcome in outcomes:
        compatible_outcome = _outcome_to_store_record(outcome)
        for decision in decisions:
            if _match_rank(decision, compatible_outcome) > 0:
                selected[_paper_decision_key(decision)] = _clean_paper_decision(decision)
    return sorted(selected.values(), key=lambda row: (str(row.get("created_at") or ""), str(row.get("decision_id") or "")))


def build_kalshi_outcome_migration_package() -> dict[str, Any]:
    run_id = f"kalshi_outcome_migration_{safe_run_id('kalshi_outcome_migration', utc_now_iso())}"
    discovered = discover_local_outcome_records()
    deduped = dedupe_migration_outcomes(discovered["records"])
    records = [row for row in deduped["records"] if row.get("provider_id") == KALSHI_PROVIDER and row.get("source") == "read_only_settlement"]
    paper_discovery = discover_local_paper_decisions()
    supporting = _matching_paper_decisions(records, paper_discovery["records"])
    final_counts = Counter(str(row.get("final_outcome") or "unknown") for row in records)
    package = {
        "ok": True,
        "status": "package_built",
        "schema_version": MIGRATION_SCHEMA_VERSION,
        "migration_version": MIGRATION_VERSION,
        "run_id": run_id,
        "created_at": utc_now_iso(),
        "migrated_from": MIGRATED_FROM,
        "source": "local_repo_migration",
        "records": records,
        "supporting_paper_decisions": supporting,
        "records_discovered": int(discovered["records_found"]),
        "records_valid": len(records),
        "records_rejected": int(deduped["records_rejected"]),
        "rejected_reason_counts": dict(deduped["rejected_reason_counts"]),
        "duplicate_count": int(deduped["duplicate_count"]),
        "raw_duplicate_reference_count": int(deduped["duplicate_count"]),
        "logical_duplicate_count": 0,
        "final_outcome_counts": dict(final_counts),
        "supporting_paper_decision_count": len(supporting),
        "source_paths": list(discovered["source_paths"]),
        "paper_decision_source_paths": list(paper_discovery["source_paths"]),
        "provider_write": False,
        "execution_allowed": False,
        "execution_allowed_count": 0,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "crypto_trade_execution_enabled": False,
        "stock_trade_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "actual_crypto_swaps_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
    }
    return package


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _migration_dir(base_data_dir: str = "data") -> Path:
    path = resolve_base_data_dir(base_data_dir) / "outcomes" / "migration"
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_migration_package(package: dict[str, Any], dry_run: bool = True) -> dict[str, Any]:
    root = _migration_dir("data")
    run_id = str(package.get("run_id") or f"kalshi_outcome_migration_{uuid.uuid4().hex[:12]}")
    created = _parse_time(str(package.get("created_at") or "")) or datetime.now(timezone.utc)
    day = created.date().isoformat()
    payload = {**package, "dry_run": bool(dry_run), "raw_payload_included": False, "secrets_included": False}
    latest_path = root / "kalshi_local_outcomes_migration.latest.json"
    item_path = root / "items" / f"{sanitize_filename(run_id)}.json"
    daily_json_path = root / "daily" / f"{day}.json"
    daily_md_path = root / "daily" / f"{day}.md"
    _atomic_write_json(latest_path, payload)
    _atomic_write_json(item_path, payload)
    _atomic_write_json(daily_json_path, payload)
    lines = [
        f"# Kalshi Outcome Migration {day}",
        "",
        f"- run_id: {run_id}",
        f"- records_valid: {payload.get('records_valid', 0)}",
        f"- records_rejected: {payload.get('records_rejected', 0)}",
        f"- duplicate_count: {payload.get('duplicate_count', 0)}",
        f"- raw_duplicate_reference_count: {payload.get('raw_duplicate_reference_count', payload.get('duplicate_count', 0))}",
        f"- logical_duplicate_count: {payload.get('logical_duplicate_count', 0)}",
        f"- final_outcome_counts: {payload.get('final_outcome_counts', {})}",
        f"- supporting_paper_decision_count: {payload.get('supporting_paper_decision_count', 0)}",
        "- provider_write: false",
        "- execution_allowed: false",
        "- raw_payload_included: false",
        "- secrets_included: false",
    ]
    daily_md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "status": "migration_package_written",
        "latest_path": str(latest_path),
        "item_path": str(item_path),
        "daily_json_path": str(daily_json_path),
        "daily_markdown_path": str(daily_md_path),
        "records_valid": int(payload.get("records_valid", 0)),
        "records_rejected": int(payload.get("records_rejected", 0)),
        "duplicate_count": int(payload.get("duplicate_count", 0)),
        "raw_duplicate_reference_count": int(payload.get("raw_duplicate_reference_count", payload.get("duplicate_count", 0))),
        "logical_duplicate_count": int(payload.get("logical_duplicate_count", 0)),
        "raw_payload_included": False,
        "secrets_included": False,
    }


def _outcome_to_store_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider": record.get("provider_id") or record.get("provider") or KALSHI_PROVIDER,
        "market_type": record.get("market_type") or PREDICTION_MARKET,
        "ticker": record.get("ticker"),
        "contract_id": record.get("contract_id") or record.get("ticker"),
        "review_item_id": record.get("review_decision_id") or record.get("review_item_id"),
        "decision_id": record.get("paper_decision_id") or record.get("decision_id"),
        "run_id": record.get("source_run_id") or record.get("run_id") or record.get("original_run_id"),
        "close_time": record.get("close_time"),
        "outcome_status": record.get("outcome_status"),
        "final_outcome": record.get("final_outcome"),
        "settled_at": record.get("settled_at"),
        "source": record.get("source") or "read_only_settlement",
        "evidence_type": record.get("evidence_type") or "explicit_settlement_field",
        "evidence_summary": record.get("evidence_summary") or "local_repo_migration",
    }


def compare_migration_package_to_render(package: dict[str, Any], render_outcomes: list[dict[str, Any]] | dict[str, Any] | None = None) -> dict[str, Any]:
    records = list(package.get("records") or [])
    if isinstance(render_outcomes, dict):
        existing = list(render_outcomes.get("records") or render_outcomes.get("items") or [])
        render_count = int(render_outcomes.get("total_count", len(existing)))
    else:
        existing = list(render_outcomes or [])
        render_count = len(existing)
    local_ids = {build_outcome_identity(row) for row in records}
    render_ids = {build_outcome_identity(row) for row in existing}
    overlap = sorted(local_ids & render_ids)
    local_only = sorted(local_ids - render_ids)
    render_only = sorted(render_ids - local_ids)
    return {
        "ok": True,
        "status": "compared",
        "local_package_count": len(local_ids),
        "render_outcomes_count": render_count,
        "overlap_count": len(overlap),
        "local_only_count": len(local_only),
        "render_only_count": max(0, len(render_only)),
        "duplicate_count": int(package.get("duplicate_count", 0)),
        "invalid_local_count": int(package.get("records_rejected", 0)),
        "would_insert_count": len(local_only),
        "overlap_id_sample": overlap[:10],
        "raw_payload_included": False,
        "secrets_included": False,
    }


def build_import_plan(package: dict[str, Any], render_state: dict[str, Any]) -> dict[str, Any]:
    comparison = compare_migration_package_to_render(package, render_state)
    projected = int(render_state.get("total_count", comparison["render_outcomes_count"])) + int(comparison["would_insert_count"])
    recommendation = "dry_run_import"
    if comparison["invalid_local_count"] > 0:
        recommendation = "fix_invalid_local_records"
    elif comparison["would_insert_count"] == 0:
        recommendation = "no_import_needed"
    return {
        "ok": True,
        "status": "import_plan_built",
        **comparison,
        "projected_outcomes_after_import": projected,
        "recommendation": recommendation,
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def _dedupe_supporting_paper_decisions(records: list[dict[str, Any]]) -> dict[str, Any]:
    rejected_reason_counts: Counter[str] = Counter()
    by_key: dict[str, dict[str, Any]] = {}
    for record in records:
        found_forbidden, reason = _has_forbidden_key(record)
        if found_forbidden:
            rejected_reason_counts[str(reason)] += 1
            continue
        if record.get("execution_allowed") is True:
            rejected_reason_counts["execution_allowed_rejected"] += 1
            continue
        cleaned = _clean_paper_decision(record)
        if not cleaned.get("decision_id") and not cleaned.get("review_item_id") and not _market_key(cleaned):
            rejected_reason_counts["missing_paper_decision_match_key"] += 1
            continue
        by_key[_paper_decision_key(cleaned)] = cleaned
    return {
        "records": sorted(by_key.values(), key=lambda row: (str(row.get("created_at") or ""), str(row.get("decision_id") or ""))),
        "records_rejected": sum(rejected_reason_counts.values()),
        "rejected_reason_counts": dict(rejected_reason_counts),
    }


def _match_count(records: list[dict[str, Any]], paper_decisions: list[dict[str, Any]]) -> tuple[int, int]:
    matched = 0
    for record in records:
        store_record = _outcome_to_store_record(record)
        if any(_match_rank(decision, store_record) > 0 for decision in paper_decisions):
            matched += 1
    return matched, max(0, len(records) - matched)


def _write_supporting_paper_decisions(base_data_dir: str, records: list[dict[str, Any]], import_run_id: str) -> dict[str, Any]:
    if not records:
        return {"paper_decisions_written": 0, "paper_ledger_items_path": None}
    root = resolve_base_data_dir(base_data_dir) / "paper_ledger" / "items"
    path = root / f"{sanitize_filename(import_run_id)}_supporting_paper_decisions.json"
    wrapper = {
        "schema_version": MIGRATION_SCHEMA_VERSION,
        "storage_backend": "file",
        "latest_run_id": import_run_id,
        "last_updated_at": utc_now_iso(),
        "items_written_count": len(records),
        "items": records,
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }
    _atomic_write_json(path, wrapper)
    return {"paper_decisions_written": len(records), "paper_ledger_items_path": str(path)}


def _write_import_audit(base_data_dir: str, payload: dict[str, Any], import_run_id: str) -> str:
    root = resolve_base_data_dir(base_data_dir) / "outcomes" / "migration" / "import_audit"
    path = root / "items" / f"{sanitize_filename(import_run_id)}.json"
    safe = {key: value for key, value in payload.items() if key not in {"accepted_records", "records"}}
    safe["raw_payload_included"] = False
    safe["secrets_included"] = False
    _atomic_write_json(path, safe)
    _atomic_write_json(root / "latest.json", safe)
    return str(path)


def import_local_settlement_records(
    records: list[dict[str, Any]] | None,
    *,
    supporting_paper_decisions: list[dict[str, Any]] | None = None,
    source: str = "local_repo_migration",
    migration_version: str = MIGRATION_VERSION,
    dry_run: bool = True,
    persist: bool = False,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    base = str(resolve_base_data_dir(base_data_dir))
    import_run_id = f"kalshi_outcome_import_{safe_run_id('kalshi_outcome_import', utc_now_iso() + str(len(records or [])))}"
    if source != "local_repo_migration":
        return _import_response(
            status="invalid_request",
            dry_run=dry_run,
            persist=persist,
            migration_version=migration_version,
            records_received=len(records or []),
            rejected_reason_counts={"unsupported_import_source": 1},
            base_data_dir=base,
        )
    if migration_version != MIGRATION_VERSION:
        return _import_response(
            status="invalid_request",
            dry_run=dry_run,
            persist=persist,
            migration_version=migration_version,
            records_received=len(records or []),
            rejected_reason_counts={"unsupported_migration_version": 1},
            base_data_dir=base,
        )

    deduped = dedupe_migration_outcomes([row for row in (records or []) if isinstance(row, dict)])
    valid_records = list(deduped["records"])
    rejected_reason_counts = Counter(deduped["rejected_reason_counts"])
    paper_result = _dedupe_supporting_paper_decisions(list(supporting_paper_decisions or []))
    rejected_reason_counts.update(paper_result["rejected_reason_counts"])

    existing_outcomes = load_outcome_records(base)
    existing_ids = {build_outcome_identity(row) for row in existing_outcomes}
    duplicates = [row for row in valid_records if build_outcome_identity(row) in existing_ids]
    to_insert = [row for row in valid_records if build_outcome_identity(row) not in existing_ids]

    existing_paper = load_paper_decisions(base)
    existing_paper_keys = {_paper_decision_key(row) for row in existing_paper}
    supporting = [row for row in paper_result["records"] if _paper_decision_key(row) not in existing_paper_keys]
    combined_paper = existing_paper + supporting
    matched_count, unmatched_count = _match_count(to_insert, combined_paper)

    should_persist = bool(persist) and not bool(dry_run)
    blocked_reason = None
    inserted_count = 0
    audit_path = None
    paper_write = {"paper_decisions_written": 0, "paper_ledger_items_path": None}
    if rejected_reason_counts:
        blocked_reason = "validation_failed"
        should_persist = False
    elif unmatched_count > 0:
        blocked_reason = "unmatched_paper_decisions"
        should_persist = False
    elif not persist:
        blocked_reason = "persist_false"
    elif dry_run:
        blocked_reason = "dry_run"

    if should_persist and to_insert:
        paper_write = _write_supporting_paper_decisions(base, supporting, import_run_id)
        ingest_records = [_outcome_to_store_record(row) for row in to_insert]
        ingest = ingest_outcome_records(
            ingest_records,
            source="read_only_settlement",
            dry_run=False,
            persist=True,
            base_data_dir=base,
        )
        inserted_count = int(ingest.get("outcome_records_written", 0))
    elif should_persist and not to_insert:
        inserted_count = 0

    after_count = len(existing_outcomes) + (inserted_count if should_persist else len(to_insert))
    status = "outcomes_imported" if should_persist and inserted_count else "outcomes_import_validated"
    if blocked_reason in {"validation_failed", "unmatched_paper_decisions"}:
        status = blocked_reason
    response = _import_response(
        status=status,
        dry_run=dry_run,
        persist=persist,
        migration_version=migration_version,
        records_received=len(records or []),
        records_valid=len(valid_records),
        records_rejected=sum(rejected_reason_counts.values()),
        rejected_reason_counts=dict(rejected_reason_counts),
        duplicate_count=len(duplicates) + int(deduped["duplicate_count"]),
        would_insert_count=len(to_insert),
        inserted_count=inserted_count,
        matched_paper_decision_count=matched_count,
        unmatched_count=unmatched_count,
        render_existing_outcomes_count=len(existing_outcomes),
        render_outcomes_after_import_if_persisted=after_count,
        base_data_dir=base,
        persistence_blocked_reason=blocked_reason,
        supporting_paper_decisions_received=len(supporting_paper_decisions or []),
        supporting_paper_decisions_valid=len(paper_result["records"]),
        supporting_paper_decisions_written=int(paper_write.get("paper_decisions_written", 0)),
        paper_ledger_items_path=paper_write.get("paper_ledger_items_path"),
    )
    if should_persist:
        audit_path = _write_import_audit(base, response, import_run_id)
        response["audit_report_path"] = audit_path
    return response


def _import_response(
    *,
    status: str,
    dry_run: bool,
    persist: bool,
    migration_version: str,
    records_received: int,
    base_data_dir: str,
    records_valid: int = 0,
    records_rejected: int = 0,
    rejected_reason_counts: dict[str, int] | None = None,
    duplicate_count: int = 0,
    would_insert_count: int = 0,
    inserted_count: int = 0,
    matched_paper_decision_count: int = 0,
    unmatched_count: int = 0,
    render_existing_outcomes_count: int = 0,
    render_outcomes_after_import_if_persisted: int = 0,
    persistence_blocked_reason: str | None = None,
    supporting_paper_decisions_received: int = 0,
    supporting_paper_decisions_valid: int = 0,
    supporting_paper_decisions_written: int = 0,
    paper_ledger_items_path: str | None = None,
) -> dict[str, Any]:
    return {
        "ok": status not in {"invalid_request", "validation_failed", "unmatched_paper_decisions"},
        "status": status,
        "dry_run": bool(dry_run),
        "persist": bool(persist),
        "records_received": int(records_received),
        "records_valid": int(records_valid),
        "records_rejected": int(records_rejected),
        "rejected_reason_counts": dict(rejected_reason_counts or {}),
        "duplicate_count": int(duplicate_count),
        "would_insert_count": int(would_insert_count),
        "inserted_count": int(inserted_count),
        "matched_paper_decision_count": int(matched_paper_decision_count),
        "unmatched_count": int(unmatched_count),
        "render_existing_outcomes_count": int(render_existing_outcomes_count),
        "render_outcomes_after_import_if_persisted": int(render_outcomes_after_import_if_persisted),
        "migration_version": migration_version,
        "audit_report_path": None,
        "persistence_blocked_reason": persistence_blocked_reason,
        "supporting_paper_decisions_received": int(supporting_paper_decisions_received),
        "supporting_paper_decisions_valid": int(supporting_paper_decisions_valid),
        "supporting_paper_decisions_written": int(supporting_paper_decisions_written),
        "paper_ledger_items_path": paper_ledger_items_path,
        "storage_backend": "file",
        "storage_health": get_storage_health(),
        "provider_write": False,
        "execution_allowed": False,
        "execution_allowed_count": 0,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "crypto_trade_execution_enabled": False,
        "stock_trade_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "actual_crypto_swaps_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def post_import_dry_run(base_url: str, package: dict[str, Any], timeout: int = 30) -> dict[str, Any]:
    payload = {
        "dry_run": True,
        "persist": False,
        "source": "local_repo_migration",
        "migration_version": package.get("migration_version", MIGRATION_VERSION),
        "records": list(package.get("records") or []),
        "supporting_paper_decisions": list(package.get("supporting_paper_decisions") or []),
    }
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/automation/outcomes/import-local-settlements",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "kalshi-outcome-migration/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8-sig"))
    except Exception as exc:
        return {
            "ok": False,
            "status": "dry_run_request_failed",
            "error": str(exc)[:240],
            "raw_payload_included": False,
            "secrets_included": False,
        }

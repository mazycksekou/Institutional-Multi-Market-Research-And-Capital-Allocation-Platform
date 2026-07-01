from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.brokerage.ledger import record_ledger_event

from src.data.data_paths import resolve_base_data_dir
from src.services.scheduler_config import SCHEMA_VERSION, safe_run_id, sanitize_filename, utc_now_iso

LEDGER_SCHEMA_VERSION = f"{SCHEMA_VERSION}.paper_decision_ledger.v2"
_SENSITIVE_KEY_PARTS = ("key", "secret", "token", "password", "auth", "credential", "signature", "header")
_RAW_PAYLOAD_KEYS = {
    "provider_payload",
    "raw_payload",
    "external_payload",
    "source_payload",
    "source_payload_redacted",
    "raw_provider_payload",
    "raw_kalshi_payload",
    "raw_sharp_payload",
}


def _ledger_dir(base_data_dir: str = "data") -> Path:
    path = resolve_base_data_dir(base_data_dir) / "paper_ledger"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _items_dir(base_data_dir: str = "data") -> Path:
    path = _ledger_dir(base_data_dir) / "items"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _legacy_path(base_data_dir: str = "data") -> Path:
    return _ledger_dir(base_data_dir) / "paper_decisions.json"


def _latest_path(base_data_dir: str = "data") -> Path:
    return _ledger_dir(base_data_dir) / "latest.json"


def _run_path(base_data_dir: str, run_id: str) -> Path:
    return _items_dir(base_data_dir) / f"{sanitize_filename(str(run_id))}.json"


def _project_relative_path(base_data_dir: str, path: Path) -> str:
    root = resolve_base_data_dir(base_data_dir)
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return path.name


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


def _items_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return [item for item in payload["items"] if isinstance(item, dict)]
    return []


def _decision_dedupe_key(item: dict[str, Any]) -> str:
    if item.get("decision_id"):
        return f"decision:{item.get('decision_id')}"
    seed = "|".join(
        [
            str(item.get("run_id") or "unknown_run"),
            str(item.get("review_item_id") or "unknown_review_item"),
            str(item.get("provider") or item.get("provider_id") or "unknown_provider"),
            str(item.get("market_type") or item.get("source_type") or "unknown_market_type"),
            str(item.get("ticker") or item.get("contract_id") or "unknown_contract"),
        ]
    )
    return f"fallback:{seed}"


def _dedupe_decisions(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        by_key[_decision_dedupe_key(item)] = item
    return sorted(
        by_key.values(),
        key=lambda row: (
            str(row.get("created_at") or ""),
            str(row.get("run_id") or ""),
            str(row.get("decision_id") or ""),
        ),
    )


def _safe_scalar(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return None


def _sanitize_mapping(payload: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in payload.items():
        key_text = str(key)
        lower_key = key_text.lower()
        if lower_key in _RAW_PAYLOAD_KEYS or any(part in lower_key for part in _SENSITIVE_KEY_PARTS):
            continue
        if isinstance(value, dict):
            safe[key_text] = _sanitize_mapping(value)
        elif isinstance(value, list):
            safe[key_text] = [_safe_scalar(item) for item in value if _safe_scalar(item) is not None][:25]
        else:
            safe[key_text] = _safe_scalar(value)
    return safe


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _observed_price(item: dict[str, Any]) -> Any:
    for key in ("yes_price", "odds_or_price", "best_odds", "best_line"):
        value = item.get(key)
        if value is not None:
            return value
    return item.get("implied_probability")


def _decision_id(item: dict[str, Any], run_id: str | None) -> str:
    seed = "|".join(
        [
            str(run_id or item.get("run_id") or "unknown_run"),
            str(item.get("id") or item.get("review_item_id") or "unknown_review_item"),
            str(item.get("provider_id") or item.get("provider") or "unknown_provider"),
            str(item.get("ticker") or item.get("contract_id") or item.get("event_id") or "unknown_market"),
        ]
    )
    return f"decision_{safe_run_id('paper_decision', seed)}"


def create_paper_decision_record(
    candidate: dict[str, Any],
    *,
    run_id: str | None = None,
    snapshot_id: str | None = None,
    report_path: str | None = None,
    base_data_dir: str = "data",
    persist: bool = True,
) -> dict[str, Any]:
    now = utc_now_iso()
    item = _sanitize_mapping(dict(candidate))
    review_item_id = str(item.get("id") or item.get("review_item_id") or item.get("decision_id") or "unknown_review_item")
    decision = {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "decision_id": _decision_id(item, run_id),
        "run_id": run_id or item.get("run_id") or snapshot_id,
        "review_item_id": review_item_id,
        "provider": item.get("provider_id", item.get("provider", "unknown")),
        "source_type": item.get("source_type", item.get("market_type", "unknown")),
        "market_type": item.get("market_type", "unknown"),
        "ticker": item.get("ticker"),
        "contract_id": item.get("contract_id"),
        "event": item.get("event_name") or item.get("event_title"),
        "title": item.get("contract_title") or item.get("selection"),
        "observed_price": _observed_price(item),
        "price_source": item.get("price_source"),
        "implied_probability": item.get("implied_probability"),
        "liquidity_tier": item.get("liquidity_tier"),
        "liquidity_score": item.get("liquidity_score"),
        "spread_score": item.get("spread_score"),
        "pricing_quality_score": item.get("pricing_quality_score"),
        "risk_score": item.get("risk_score"),
        "confidence_score": item.get("confidence_score"),
        "review_priority_score": item.get("review_priority_score"),
        "reason_codes": list(item.get("reason_codes") or [])[:25],
        "recommendation_status": item.get("recommendation_status", "review_only"),
        "execution_allowed": False,
        "paper_only": True,
        "created_at": item.get("created_at") or now,
        "snapshot_id": snapshot_id,
        "report_path": report_path,
        "close_time": item.get("close_time") or item.get("market_close_at"),
        "outcome_status": item.get("outcome_status") or "pending",
        "settled_at": item.get("settled_at"),
        "final_outcome": item.get("final_outcome"),
        "paper_result": item.get("paper_result"),
        "paper_roi_estimate": item.get("paper_roi_estimate"),
        "calibration_bucket": item.get("calibration_bucket"),
    }
    if persist:
        existing = load_paper_decisions(base_data_dir)
        by_id = {str(row.get("decision_id")): row for row in existing if isinstance(row, dict)}
        by_id[str(decision["decision_id"])] = decision
        _save_legacy_decisions(list(by_id.values()), base_data_dir)
    decision_snapshot = {key: value for key, value in decision.items() if key != "brokerage_ledger_event"}
    decision["brokerage_ledger_event"] = record_ledger_event(
        event_type="paper_decision_record_created",
        subject_id=str(decision["decision_id"]),
        payload={"paper_decision_record": decision_snapshot},
        metadata={"source_module": "automation_scheduler.paper_decision_ledger"},
    )
    return decision


def _save_legacy_decisions(items: list[dict[str, Any]], base_data_dir: str = "data") -> None:
    safe_items = [_sanitize_mapping(item) for item in items if isinstance(item, dict)]
    _atomic_write_json(_legacy_path(base_data_dir), safe_items)


def load_paper_decisions(base_data_dir: str = "data") -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    items_dir = _items_dir(base_data_dir)
    if items_dir.exists():
        for path in sorted(items_dir.glob("*.json")):
            items.extend(_items_from_payload(_read_json(path)))
    items.extend(_items_from_payload(_read_json(_legacy_path(base_data_dir))))
    items.extend(_items_from_payload(_read_json(_latest_path(base_data_dir))))
    return _dedupe_decisions(items)


def load_paper_decision_state(base_data_dir: str = "data") -> dict[str, Any]:
    latest_path = _latest_path(base_data_dir)
    latest = _read_json(latest_path)
    if isinstance(latest, dict) and isinstance(latest.get("items"), list):
        items = [item for item in latest["items"] if isinstance(item, dict)]
        return {
            "storage_backend": str(latest.get("storage_backend") or "file"),
            "latest_run_id": latest.get("latest_run_id"),
            "last_updated_at": latest.get("last_updated_at"),
            "ledger_read_ok": True,
            "ledger_error_category": None,
            "ledger_read_path": _project_relative_path(base_data_dir, latest_path),
            "items_read_count": len(items),
            "items": items,
        }
    malformed_latest = latest_path.exists() and latest is None
    legacy = _read_json(_legacy_path(base_data_dir))
    if isinstance(legacy, list):
        items = [item for item in legacy if isinstance(item, dict)]
        return {
            "storage_backend": "file",
            "latest_run_id": None,
            "last_updated_at": None,
            "ledger_read_ok": True,
            "ledger_error_category": None,
            "ledger_read_path": _project_relative_path(base_data_dir, _legacy_path(base_data_dir)),
            "items_read_count": len(items),
            "items": items,
        }
    return {
        "storage_backend": "file",
        "latest_run_id": None,
        "last_updated_at": None,
        "ledger_read_ok": not malformed_latest,
        "ledger_error_category": "malformed_latest_paper_ledger_file" if malformed_latest else None,
        "ledger_read_path": None,
        "items_read_count": 0,
        "items": [],
    }


def persist_paper_decisions_for_review_items(
    items: list[dict[str, Any]],
    *,
    run_id: str,
    snapshot_id: str | None = None,
    report_path: str | None = None,
    base_data_dir: str = "data",
) -> dict[str, Any]:
    now = utc_now_iso()
    decisions = [
        create_paper_decision_record(
            item,
            run_id=run_id,
            snapshot_id=snapshot_id or run_id,
            report_path=report_path,
            base_data_dir=base_data_dir,
            persist=False,
        )
        for item in items
        if isinstance(item, dict)
    ]
    wrapper = {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "storage_backend": "file",
        "latest_run_id": str(run_id),
        "last_updated_at": now,
        "items_written_count": len(decisions),
        "items": decisions,
    }
    latest_path = _latest_path(base_data_dir)
    run_path = _run_path(base_data_dir, run_id)
    _atomic_write_json(latest_path, wrapper)
    _atomic_write_json(run_path, wrapper)
    _save_legacy_decisions(decisions, base_data_dir)
    record_ledger_event(
        event_type="paper_decision_records_persisted",
        subject_id=str(run_id),
        payload={"paper_decisions_written": len(decisions)},
        metadata={"source_module": "automation_scheduler.paper_decision_ledger"},
    )
    return {
        "storage_backend": "file",
        "latest_run_id": str(run_id),
        "last_updated_at": now,
        "paper_ledger_write_path": _project_relative_path(base_data_dir, latest_path),
        "paper_ledger_items_run_path": _project_relative_path(base_data_dir, run_path),
        "paper_decisions_written": len(decisions),
    }


def summarize_paper_decisions(items: list[dict[str, Any]]) -> dict[str, Any]:
    provider_counts: dict[str, int] = {}
    market_type_counts: dict[str, int] = {}
    liquidity_tier_counts: dict[str, int] = {}
    score_field_presence_counts = {
        "liquidity_score": 0,
        "spread_score": 0,
        "pricing_quality_score": 0,
        "risk_score": 0,
        "confidence_score": 0,
        "review_priority_score": 0,
    }
    settlement_field_presence_counts = {
        "outcome_status": 0,
        "settled_at": 0,
        "final_outcome": 0,
        "paper_result": 0,
        "paper_roi_estimate": 0,
    }
    for item in items:
        provider = str(item.get("provider") or "unknown")
        provider_counts[provider] = provider_counts.get(provider, 0) + 1
        market_type = str(item.get("market_type") or "unknown")
        market_type_counts[market_type] = market_type_counts.get(market_type, 0) + 1
        tier = item.get("liquidity_tier")
        if tier:
            tier_key = str(tier)
            liquidity_tier_counts[tier_key] = liquidity_tier_counts.get(tier_key, 0) + 1
        for field in score_field_presence_counts:
            if item.get(field) is not None:
                score_field_presence_counts[field] += 1
        for field in settlement_field_presence_counts:
            if item.get(field) is not None:
                settlement_field_presence_counts[field] += 1
    settled = [item for item in items if str(item.get("outcome_status") or "").lower() == "settled" or item.get("final_outcome") is not None]
    return {
        "paper_decisions_count": len(items),
        "provider_counts": provider_counts,
        "market_type_counts": market_type_counts,
        "liquidity_tier_counts": liquidity_tier_counts,
        "score_field_presence_counts": score_field_presence_counts,
        "settlement_field_presence_counts": settlement_field_presence_counts,
        "records_with_outcome_count": len(settled),
        "records_without_outcome_count": max(0, len(items) - len(settled)),
        "execution_allowed_count": len([item for item in items if bool(item.get("execution_allowed"))]),
        "paper_only_count": len([item for item in items if bool(item.get("paper_only"))]),
    }


def to_float_or_none(value: Any) -> float | None:
    return _to_float(value)

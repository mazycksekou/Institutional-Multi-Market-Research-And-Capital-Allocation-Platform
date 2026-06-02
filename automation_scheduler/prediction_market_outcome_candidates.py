from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .data_paths import get_runtime_data_path, get_storage_health, resolve_base_data_dir
from .paper_decision_ledger import load_paper_decisions
from .review_queue import load_review_queue_state
from .scheduler_config import SCHEMA_VERSION, safe_run_id, sanitize_filename, utc_now_iso


PREDICTION_MARKET_OUTCOME_CANDIDATE_SCHEMA_VERSION = f"{SCHEMA_VERSION}.prediction_market_outcome_candidates.v1"

ACCEPTED_EXPLICIT_FIELDS = (
    "result",
    "final_outcome",
    "settlement_result",
    "provider_normalized_result",
    "provider_normalized_outcome",
    "normalized_result",
    "normalized_outcome",
)

BOOLEAN_SETTLEMENT_FIELDS = {
    "settled_yes": "yes",
    "settled_no": "no",
}

PRICE_ONLY_FIELDS = (
    "yes_price",
    "no_price",
    "yes_bid",
    "yes_ask",
    "no_bid",
    "no_ask",
    "bid",
    "ask",
    "bid_price",
    "ask_price",
    "last_trade_price",
    "market_price",
    "implied_probability",
    "odds_or_price",
)

RAW_OR_SECRET_KEY_PARTS = (
    "raw_payload",
    "provider_payload",
    "external_payload",
    "source_payload",
    "api_key",
    "secret",
    "token",
    "password",
    "credential",
    "authorization",
    "signature",
)


def _normalize_outcome(value: Any) -> str | None:
    if isinstance(value, bool):
        return "yes" if value else "no"
    text = str(value or "").strip().lower()
    if text in {"yes", "y", "true", "1", "settled_yes", "resolved_yes", "result=yes"}:
        return "yes"
    if text in {"no", "n", "false", "0", "settled_no", "resolved_no", "result=no"}:
        return "no"
    return None


def _is_true_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value == 1
    return str(value or "").strip().lower() in {"true", "yes", "1", "settled", "settled_yes", "settled_no"}


def _safe_scalar(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return None


def _safe_get(row: dict[str, Any], key: str) -> Any:
    value = row.get(key)
    return _safe_scalar(value)


def _contains_any_value(row: dict[str, Any], keys: tuple[str, ...]) -> bool:
    return any(row.get(key) not in (None, "") for key in keys)


def _is_closed_without_result(row: dict[str, Any]) -> bool:
    status_values = [
        row.get("status"),
        row.get("market_status"),
        row.get("outcome_status"),
        row.get("settlement_status"),
        row.get("state"),
    ]
    closed_tokens = {"closed", "complete", "completed", "settled", "resolved", "final"}
    return any(str(value or "").strip().lower() in closed_tokens for value in status_values)


def _identity(row: dict[str, Any], source_record_type: str) -> str:
    seed = "|".join(
        [
            source_record_type,
            str(row.get("decision_id") or ""),
            str(row.get("review_item_id") or row.get("id") or ""),
            str(row.get("provider") or row.get("provider_id") or ""),
            str(row.get("ticker") or row.get("contract_id") or row.get("market_id") or ""),
            str(row.get("close_time") or row.get("market_close_at") or ""),
        ]
    )
    return f"outcome_candidate_{safe_run_id('prediction_market_outcome_candidate', seed)}"


def compact_prediction_market_record(row: dict[str, Any], *, source_record_type: str) -> dict[str, Any]:
    return {
        "source_record_type": source_record_type,
        "decision_id": _safe_get(row, "decision_id"),
        "review_item_id": _safe_get(row, "review_item_id") or _safe_get(row, "id"),
        "run_id": _safe_get(row, "run_id"),
        "provider": _safe_get(row, "provider") or _safe_get(row, "provider_id"),
        "source_type": _safe_get(row, "source_type"),
        "market_type": _safe_get(row, "market_type"),
        "ticker": _safe_get(row, "ticker"),
        "contract_id": _safe_get(row, "contract_id"),
        "market_id": _safe_get(row, "market_id"),
        "event": _safe_get(row, "event") or _safe_get(row, "event_name") or _safe_get(row, "event_title"),
        "title": _safe_get(row, "title") or _safe_get(row, "contract_title") or _safe_get(row, "selection"),
        "close_time": _safe_get(row, "close_time") or _safe_get(row, "market_close_at"),
        "settled_at": _safe_get(row, "settled_at"),
        "status": _safe_get(row, "status"),
        "market_status": _safe_get(row, "market_status"),
        "outcome_status": _safe_get(row, "outcome_status"),
        "settlement_status": _safe_get(row, "settlement_status"),
    }


def is_prediction_market_record(row: dict[str, Any]) -> bool:
    haystack = " ".join(
        str(row.get(key) or "").lower()
        for key in (
            "provider",
            "provider_id",
            "source_type",
            "market_type",
            "module",
            "asset_type",
            "source",
        )
    )
    return any(token in haystack for token in ("prediction_market", "kalshi", "polymarket", "manifold"))


def evaluate_outcome_evidence(row: dict[str, Any], *, source_record_type: str = "unknown") -> dict[str, Any]:
    safe_record = compact_prediction_market_record(row, source_record_type=source_record_type)
    explicit: list[tuple[str, str, Any]] = []

    for field in ACCEPTED_EXPLICIT_FIELDS:
        if field not in row or row.get(field) in (None, ""):
            continue
        normalized = _normalize_outcome(row.get(field))
        if normalized is None:
            return {
                **safe_record,
                "candidate_accepted": False,
                "rejection_reason": "ambiguous_result",
                "evidence_field": field,
                "evidence_value": _safe_scalar(row.get(field)),
                "raw_payload_included": False,
                "secrets_included": False,
            }
        explicit.append((field, normalized, _safe_scalar(row.get(field))))

    for field, normalized in BOOLEAN_SETTLEMENT_FIELDS.items():
        if _is_true_value(row.get(field)):
            explicit.append((field, normalized, True))

    unique_outcomes = {outcome for _, outcome, _ in explicit}
    if len(unique_outcomes) > 1:
        return {
            **safe_record,
            "candidate_accepted": False,
            "rejection_reason": "ambiguous_result",
            "evidence_field": "conflicting_explicit_fields",
            "evidence_value": None,
            "raw_payload_included": False,
            "secrets_included": False,
        }

    if explicit:
        evidence_field, outcome, evidence_value = explicit[0]
        return {
            **safe_record,
            "candidate_accepted": True,
            "outcome_candidate_id": _identity(row, source_record_type),
            "explicit_outcome": outcome,
            "evidence_field": evidence_field,
            "evidence_value": evidence_value,
            "evidence_type": "explicit_settlement_result",
            "would_persist_outcome": False,
            "raw_payload_included": False,
            "secrets_included": False,
        }

    if _is_closed_without_result(row):
        reason = "closed_without_explicit_result"
    elif _contains_any_value(row, PRICE_ONLY_FIELDS):
        reason = "price_only_inference_rejected"
    else:
        reason = "missing_result"
    return {
        **safe_record,
        "candidate_accepted": False,
        "rejection_reason": reason,
        "evidence_field": None,
        "evidence_value": None,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def _read_review_items(base_data_dir: str | Path) -> list[dict[str, Any]]:
    base = resolve_base_data_dir(base_data_dir)
    state = load_review_queue_state({"paths": {"review_queue": str(base / "review_queue")}})
    return [row for row in list(state.get("items") or []) if isinstance(row, dict)]


def load_prediction_market_source_records(*, base_data_dir: str | Path = "data") -> list[dict[str, Any]]:
    decisions = [
        {**row, "_source_record_type": "paper_decision"}
        for row in load_paper_decisions(str(resolve_base_data_dir(base_data_dir)))
        if isinstance(row, dict)
    ]
    review_items = [
        {**row, "_source_record_type": "review_queue"}
        for row in _read_review_items(base_data_dir)
        if isinstance(row, dict)
    ]
    records = [row for row in decisions + review_items if is_prediction_market_record(row)]
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for row in records:
        key = "|".join(
            [
                str(row.get("_source_record_type") or ""),
                str(row.get("decision_id") or row.get("id") or row.get("review_item_id") or ""),
                str(row.get("ticker") or row.get("contract_id") or row.get("market_id") or ""),
            ]
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(json.dumps(payload, separators=(",", ":"), sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _report_root(base_data_dir: str | Path | None = None) -> Path:
    if base_data_dir is None:
        return get_runtime_data_path("prediction_market_outcome_candidates")
    root = resolve_base_data_dir(base_data_dir) / "prediction_market_outcome_candidates"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _relative(path: Path, base_data_dir: str | Path | None = None) -> str:
    root = resolve_base_data_dir(base_data_dir)
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return path.name


def render_candidate_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Prediction Market Outcome Candidates",
        "",
        f"- created_at: {report.get('created_at')}",
        f"- source_records_scanned: {report.get('source_records_scanned')}",
        f"- candidates_count: {report.get('candidates_count')}",
        f"- rejected_count: {report.get('rejected_count')}",
        "- would_persist_outcomes: false",
        "- provider_write: false",
        "- execution_allowed: false",
        "- raw_payload_included: false",
        "- secrets_included: false",
        "",
        "## Candidates",
    ]
    for row in list(report.get("candidates") or [])[:25]:
        lines.append(
            f"- {row.get('ticker') or row.get('contract_id') or row.get('market_id')}: {row.get('explicit_outcome')} via {row.get('evidence_field')}"
        )
    if not report.get("candidates"):
        lines.append("- none")
    return "\n".join(lines) + "\n"


def write_candidate_report(report: dict[str, Any], *, base_data_dir: str | Path | None = None) -> dict[str, Any]:
    root = _report_root(base_data_dir)
    created = str(report.get("created_at") or utc_now_iso())
    day = created[:10] if created else datetime.now(timezone.utc).date().isoformat()
    run_id = str(report.get("run_id") or sanitize_filename(f"prediction_market_outcome_candidates_{created}_{uuid4().hex[:8]}"))
    latest_json = root / "latest.json"
    latest_md = root / "latest.md"
    item_json = root / "items" / f"{sanitize_filename(run_id)}.json"
    item_md = root / "items" / f"{sanitize_filename(run_id)}.md"
    daily_json = root / "daily" / f"{day}.json"
    daily_md = root / "daily" / f"{day}.md"
    safe_report = {
        **report,
        "would_persist_outcomes": False,
        "provider_write": False,
        "execution_allowed": False,
        "raw_payload_included": False,
        "secrets_included": False,
    }
    markdown = render_candidate_markdown(safe_report)
    for path in (latest_json, item_json, daily_json):
        _atomic_write_json(path, safe_report)
    for path in (latest_md, item_md, daily_md):
        _atomic_write_text(path, markdown)
    return {
        "candidate_latest_json_path": _relative(latest_json, base_data_dir),
        "candidate_latest_markdown_path": _relative(latest_md, base_data_dir),
        "candidate_item_json_path": _relative(item_json, base_data_dir),
        "candidate_item_markdown_path": _relative(item_md, base_data_dir),
        "candidate_daily_json_path": _relative(daily_json, base_data_dir),
        "candidate_daily_markdown_path": _relative(daily_md, base_data_dir),
    }


def build_candidate_report(
    *,
    records: list[dict[str, Any]] | None = None,
    base_data_dir: str | Path = "data",
    persist: bool = False,
    module: str | None = None,
    source_id: str | None = None,
    local_record_limit: int = 250,
) -> dict[str, Any]:
    all_records = records if records is not None else load_prediction_market_source_records(base_data_dir=base_data_dir)
    filtered = [row for row in all_records if isinstance(row, dict)]
    if module:
        needle = str(module).strip().lower()
        filtered = [
            row for row in filtered
            if needle in {
                str(row.get("module") or "").lower(),
                str(row.get("market_type") or "").lower(),
                str(row.get("source_type") or "").lower(),
            }
            or needle in str(row.get("provider") or row.get("provider_id") or "").lower()
        ]
    if source_id:
        needle = str(source_id).strip().lower()
        filtered = [
            row for row in filtered
            if needle in {
                str(row.get("source_id") or "").lower(),
                str(row.get("provider") or "").lower(),
                str(row.get("provider_id") or "").lower(),
            }
        ]
    limit = max(1, min(int(local_record_limit or 250), 1000))
    filtered = filtered[:limit]

    evaluated = [
        evaluate_outcome_evidence(row, source_record_type=str(row.get("_source_record_type") or "provided_record"))
        for row in filtered
    ]
    candidates = [row for row in evaluated if bool(row.get("candidate_accepted"))]
    rejected = [row for row in evaluated if not bool(row.get("candidate_accepted"))]
    rejection_counts: dict[str, int] = {}
    for row in rejected:
        reason = str(row.get("rejection_reason") or "unknown")
        rejection_counts[reason] = rejection_counts.get(reason, 0) + 1
    now = utc_now_iso()
    run_id = sanitize_filename(f"prediction_market_outcome_candidates_{now.replace(':', '-')}_{uuid4().hex[:8]}")
    report = {
        "ok": True,
        "status": "prediction_market_outcome_candidate_check_complete",
        "schema_version": PREDICTION_MARKET_OUTCOME_CANDIDATE_SCHEMA_VERSION,
        "created_at": now,
        "run_id": run_id,
        "module_filter": module,
        "source_id_filter": source_id,
        "source_records_scanned": len(filtered),
        "candidates_count": len(candidates),
        "rejected_count": len(rejected),
        "rejection_reason_counts": rejection_counts,
        "candidates": candidates,
        "rejected_sample": rejected[:25],
        "accepted_evidence_fields": list(ACCEPTED_EXPLICIT_FIELDS) + list(BOOLEAN_SETTLEMENT_FIELDS),
        "rejected_evidence_rules": [
            "price_only_inference_rejected",
            "closed_without_explicit_result",
            "ambiguous_result",
            "missing_result",
        ],
        "would_persist_outcomes": False,
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
        "storage_backend": "file",
        "storage_health": get_storage_health(),
    }
    if persist:
        report.update(write_candidate_report(report, base_data_dir=base_data_dir))
    return report


def contains_raw_or_secret_keys(payload: Any) -> bool:
    text = str(payload).lower()
    return any(token in text for token in RAW_OR_SECRET_KEY_PARTS)

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .data_paths import get_runtime_data_path, get_storage_health, resolve_base_data_dir
from src.services.prediction_market_runtime_bridge import KalshiReadonlyAdapter
from .kalshi_readonly_readiness import build_kalshi_readonly_adapter
from .paper_decision_ledger import load_paper_decisions
from .review_queue import load_review_queue_state
from .scheduler_config import SCHEMA_VERSION, safe_run_id, sanitize_filename, utc_now_iso
from .settlement_discovery import discover_kalshi_settlements_for_pending_rows


PREDICTION_MARKET_OUTCOME_CANDIDATE_SCHEMA_VERSION = f"{SCHEMA_VERSION}.prediction_market_outcome_candidates.v1"
KALSHI_PROVIDER_ID = "kalshi_prediction_market"
MAX_TINY_PROVIDER_CALLS = 3
MAX_TINY_PROVIDER_RECORDS = 5

ZERO_CALL_REASON_CATEGORIES = {
    "provider_not_ready",
    "live_reads_disabled",
    "credentials_missing",
    "no_pending_records",
    "no_provider_eligible_records",
    "missing_required_identifiers",
    "all_records_rejected_before_provider_check",
    "call_budget_zero",
    "tiny_provider_mode_not_requested",
    "unknown_diagnostic_gap",
}

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


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _clean_reason(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    mapping = {
        "blocked_missing_credentials": "credentials_missing",
        "missing_credentials": "credentials_missing",
        "provider_disabled": "provider_not_ready",
        "live_reads_disabled": "live_reads_disabled",
        "dry_run_required": "provider_not_ready",
        "auto_execution_not_allowed": "provider_not_ready",
        "read_only_required": "provider_not_ready",
    }
    cleaned = mapping.get(text, text or "unknown_diagnostic_gap")
    if any(token in cleaned for token in ("secret", "token", "password", "credential_value", "api_key_value")):
        return "provider_not_ready"
    return cleaned


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


def _is_kalshi_record(row: dict[str, Any]) -> bool:
    haystack = " ".join(str(row.get(key) or "").lower() for key in ("provider", "provider_id", "source", "source_id"))
    return "kalshi" in haystack or str(row.get("provider") or "").lower() == KALSHI_PROVIDER_ID


def _market_identifier(row: dict[str, Any]) -> str | None:
    for key in ("ticker", "contract_id", "market_id"):
        value = row.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return None


def _pending_provider_rows(records: list[dict[str, Any]], *, max_records: int) -> list[dict[str, Any]]:
    return _provider_selection_diagnostics(records, provider_selection_limit=max_records)["selected_rows"]


def _provider_row_from_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "provider": KALSHI_PROVIDER_ID,
        "market_type": row.get("market_type") or "prediction_market",
        "decision_id": row.get("decision_id"),
        "review_item_id": row.get("review_item_id") or row.get("id"),
        "run_id": row.get("run_id"),
        "ticker": row.get("ticker"),
        "contract_id": row.get("contract_id"),
        "market_id": row.get("market_id"),
        "close_time": row.get("close_time") or row.get("market_close_at"),
        "_source_record_type": row.get("_source_record_type") or "local_record",
    }


def _provider_selection_diagnostics(records: list[dict[str, Any]], *, provider_selection_limit: int) -> dict[str, Any]:
    pending_records_seen = 0
    provider_eligible: list[dict[str, Any]] = []
    ineligible_reason_counts: dict[str, int] = {}
    missing_identifier_count = 0
    missing_ticker_count = 0
    missing_market_id_count = 0
    local_explicit_outcome_count = 0
    already_settled_or_closed_without_result_count = 0

    def mark(reason: str) -> None:
        ineligible_reason_counts[reason] = ineligible_reason_counts.get(reason, 0) + 1

    for row in records:
        if not isinstance(row, dict):
            mark("malformed_record")
            continue
        if not is_prediction_market_record(row):
            mark("non_prediction_market_record")
            continue
        if not _is_kalshi_record(row):
            mark("unsupported_prediction_market_provider")
            continue
        pending_records_seen += 1
        local_evidence = evaluate_outcome_evidence(row, source_record_type=str(row.get("_source_record_type") or "local_record"))
        rejection_reason = str(local_evidence.get("rejection_reason") or "")
        if bool(local_evidence.get("candidate_accepted")):
            local_explicit_outcome_count += 1
            already_settled_or_closed_without_result_count += 1
            mark("local_explicit_outcome")
            continue
        if rejection_reason == "closed_without_explicit_result":
            already_settled_or_closed_without_result_count += 1
        if row.get("ticker") in (None, ""):
            missing_ticker_count += 1
        if row.get("market_id") in (None, ""):
            missing_market_id_count += 1
        if not _market_identifier(row):
            missing_identifier_count += 1
            mark("missing_required_identifiers")
            continue
        provider_eligible.append(_provider_row_from_record(row))

    selection_limit = max(0, int(provider_selection_limit or 0))
    selected = provider_eligible[:selection_limit]
    provider_ineligible_records = max(0, len(records) - len(provider_eligible))
    return {
        "pending_records_seen": pending_records_seen,
        "provider_eligible_records": len(provider_eligible),
        "provider_ineligible_records": provider_ineligible_records,
        "provider_ineligible_reason_counts": ineligible_reason_counts,
        "missing_identifier_count": missing_identifier_count,
        "missing_ticker_count": missing_ticker_count,
        "missing_market_id_count": missing_market_id_count,
        "already_settled_or_closed_without_result_count": already_settled_or_closed_without_result_count,
        "local_explicit_outcome_count": local_explicit_outcome_count,
        "provider_selection_limit": selection_limit,
        "provider_selected_count": len(selected),
        "selected_rows": selected,
    }


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


def _empty_provider_check(
    *,
    allow_tiny_provider_calls: bool,
    max_provider_calls: int,
    max_records: int,
    status: str,
    block_reason: str | None = None,
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    diagnostic_payload = dict(diagnostics or {})
    return {
        "provider_settlement_check_enabled": bool(allow_tiny_provider_calls),
        "provider_settlement_check_status": status,
        "provider_call_block_reason": block_reason,
        "provider_calls_attempted": 0,
        "provider_calls_succeeded": 0,
        "provider_calls_failed": 0,
        "provider_records_returned": 0,
        "markets_checked_with_provider": 0,
        "explicit_outcomes_found": 0,
        "provider_rejected_count": 0,
        "provider_rejection_reasons": {},
        "rate_limited": False,
        "persisted": False,
        "dry_run": True,
        "provider_write": False,
        "execution_allowed": False,
        "execution_allowed_count": 0,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "max_provider_calls_effective": max_provider_calls if allow_tiny_provider_calls else 0,
        "max_records_effective": max_records if allow_tiny_provider_calls else 0,
        "raw_payload_included": False,
        "secrets_included": False,
        **diagnostic_payload,
    }


def _provider_error_reason(fetch: dict[str, Any]) -> str:
    for key in ("blocker", "status"):
        value = fetch.get(key)
        if value:
            return str(value)
    errors = fetch.get("errors")
    if isinstance(errors, list) and errors:
        return str(errors[0])
    blockers = fetch.get("blockers")
    if isinstance(blockers, list) and blockers:
        return str(blockers[0])
    return "provider_error"


def _provider_is_rate_limited(fetch: dict[str, Any]) -> bool:
    return int(fetch.get("http_status") or 0) == 429 or _provider_error_reason(fetch) == "http_429"


def _provider_readiness_diagnostics(adapter: Any) -> dict[str, Any]:
    validator = getattr(adapter, "validate_config", None)
    if not callable(validator):
        return {
            "provider_readiness_status": "provider_ready",
            "provider_readiness_blockers": [],
            "provider_config_present": True,
            "live_read_enabled": True,
            "credentials_present": True,
        }
    config = validator()
    raw_blockers = [str(item) for item in list(config.get("blockers") or [])]
    blockers = sorted({ _clean_reason(item) for item in raw_blockers if item })
    ready = bool(config.get("ok"))
    if ready:
        blockers = []
    credential_status = str(config.get("credential_status") or "").strip().lower()
    credentials_present = bool(credential_status == "ok") if credential_status else "credentials_missing" not in blockers
    live_read_enabled = bool(config.get("live_reads_enabled", config.get("live_calls_enabled", ready and "live_reads_disabled" not in blockers)))
    provider_config_present = bool(config.get("provider_enabled", ready and "provider_not_ready" not in blockers))
    return {
        "provider_readiness_status": "provider_ready" if ready else "provider_not_ready",
        "provider_readiness_blockers": blockers,
        "provider_config_present": provider_config_present,
        "live_read_enabled": live_read_enabled,
        "credentials_present": credentials_present,
    }


def _zero_call_reason(
    *,
    allow_tiny_provider_calls: bool,
    effective_calls: int,
    effective_records: int,
    readiness: dict[str, Any],
    selection: dict[str, Any],
    calls_attempted: int = 0,
) -> str | None:
    if calls_attempted > 0:
        return None
    if not allow_tiny_provider_calls:
        return "tiny_provider_mode_not_requested"
    if effective_calls <= 0 or effective_records <= 0:
        return "call_budget_zero"
    if str(readiness.get("provider_readiness_status") or "") != "provider_ready":
        blockers = set(str(item) for item in list(readiness.get("provider_readiness_blockers") or []))
        if "provider_not_ready" in blockers:
            return "provider_not_ready"
        if "live_reads_disabled" in blockers:
            return "live_reads_disabled"
        if "credentials_missing" in blockers:
            return "credentials_missing"
        return "provider_not_ready"
    if int(selection.get("pending_records_seen") or 0) <= 0:
        return "no_pending_records"
    if int(selection.get("provider_eligible_records") or 0) <= 0:
        if int(selection.get("missing_identifier_count") or 0) > 0:
            return "missing_required_identifiers"
        return "no_provider_eligible_records"
    if int(selection.get("provider_selected_count") or 0) <= 0:
        return "all_records_rejected_before_provider_check"
    return "unknown_diagnostic_gap"


def _provider_selection_blocker(
    *,
    allow_tiny_provider_calls: bool,
    effective_calls: int,
    effective_records: int,
    readiness: dict[str, Any],
    selection: dict[str, Any],
) -> str | None:
    reason = _zero_call_reason(
        allow_tiny_provider_calls=allow_tiny_provider_calls,
        effective_calls=effective_calls,
        effective_records=effective_records,
        readiness=readiness,
        selection=selection,
        calls_attempted=0,
    )
    return None if reason == "unknown_diagnostic_gap" and int(selection.get("provider_selected_count") or 0) > 0 else reason


def _base_zero_call_diagnostics(
    *,
    allow_tiny_provider_calls: bool,
    effective_calls: int,
    effective_records: int,
    readiness: dict[str, Any],
    selection: dict[str, Any],
    calls_attempted: int = 0,
) -> dict[str, Any]:
    why = _zero_call_reason(
        allow_tiny_provider_calls=allow_tiny_provider_calls,
        effective_calls=effective_calls,
        effective_records=effective_records,
        readiness=readiness,
        selection=selection,
        calls_attempted=calls_attempted,
    )
    return {
        "tiny_provider_mode_requested": bool(allow_tiny_provider_calls),
        "tiny_provider_mode_allowed": bool(allow_tiny_provider_calls and effective_calls > 0 and effective_records > 0),
        **readiness,
        **{key: value for key, value in selection.items() if key != "selected_rows"},
        "provider_selection_blocker": _provider_selection_blocker(
            allow_tiny_provider_calls=allow_tiny_provider_calls,
            effective_calls=effective_calls,
            effective_records=effective_records,
            readiness=readiness,
            selection=selection,
        ),
        "why_provider_calls_zero": why,
    }


def _fetch_tiny_read_only_records(
    pending_rows: list[dict[str, Any]],
    *,
    adapter: Any,
    max_provider_calls: int,
) -> dict[str, Any]:
    provider_records: list[dict[str, Any]] = []
    checked_rows: list[dict[str, Any]] = []
    rejected: dict[str, int] = {}
    calls_attempted = 0
    calls_succeeded = 0
    calls_failed = 0
    rate_limited = False
    stop_reason: str | None = None

    fetch_markets = getattr(adapter, "fetch_markets", None)
    if not callable(fetch_markets):
        return {
            "provider_records": [],
            "checked_rows": [],
            "provider_calls_attempted": 0,
            "provider_calls_succeeded": 0,
            "provider_calls_failed": 0,
            "provider_records_returned": 0,
            "markets_checked_with_provider": 0,
            "rate_limited": False,
            "stop_reason": "adapter_missing_fetch_markets",
            "rejected_reason_counts": {"adapter_missing_fetch_markets": len(pending_rows)},
        }

    for row in pending_rows:
        if calls_attempted >= max_provider_calls:
            stop_reason = "max_provider_calls_reached"
            break
        market_key = _market_identifier(row)
        if not market_key:
            rejected["missing_market_identifier"] = rejected.get("missing_market_identifier", 0) + 1
            continue
        calls_attempted += 1
        fetch = fetch_markets(params={"ticker": market_key, "limit": 1})
        if _provider_is_rate_limited(fetch):
            calls_failed += 1
            rate_limited = True
            stop_reason = "rate_limited"
            rejected["http_429"] = rejected.get("http_429", 0) + 1
            break
        if not bool(fetch.get("ok")) or str(fetch.get("status") or "") == "provider_error":
            calls_failed += 1
            reason = _provider_error_reason(fetch)
            stop_reason = reason
            rejected[reason] = rejected.get(reason, 0) + 1
            break
        records = [record for record in list(fetch.get("records") or []) if isinstance(record, dict)]
        provider_records.extend(records[:1])
        checked_rows.append(row)
        calls_succeeded += 1

    return {
        "provider_records": provider_records,
        "checked_rows": checked_rows,
        "provider_calls_attempted": calls_attempted,
        "provider_calls_succeeded": calls_succeeded,
        "provider_calls_failed": calls_failed,
        "provider_records_returned": len(provider_records),
        "markets_checked_with_provider": len(checked_rows),
        "rate_limited": rate_limited,
        "stop_reason": stop_reason,
        "rejected_reason_counts": rejected,
    }


def run_tiny_read_only_settlement_check(
    records: list[dict[str, Any]],
    *,
    allow_tiny_provider_calls: bool = False,
    max_provider_calls: int = 0,
    max_records: int = 0,
    adapter: Any | None = None,
) -> dict[str, Any]:
    effective_calls = max(0, min(_safe_int(max_provider_calls, 0), MAX_TINY_PROVIDER_CALLS))
    effective_records = max(0, min(_safe_int(max_records, 0), MAX_TINY_PROVIDER_RECORDS))
    provider_selection_limit = min(effective_calls, effective_records) if allow_tiny_provider_calls else 0
    selection = _provider_selection_diagnostics(records, provider_selection_limit=provider_selection_limit)
    adapter = adapter or build_kalshi_readonly_adapter()
    readiness = _provider_readiness_diagnostics(adapter)
    diagnostics = _base_zero_call_diagnostics(
        allow_tiny_provider_calls=allow_tiny_provider_calls,
        effective_calls=effective_calls,
        effective_records=effective_records,
        readiness=readiness,
        selection=selection,
        calls_attempted=0,
    )
    if not allow_tiny_provider_calls or effective_calls <= 0 or effective_records <= 0:
        return _empty_provider_check(
            allow_tiny_provider_calls=allow_tiny_provider_calls,
            max_provider_calls=effective_calls,
            max_records=effective_records,
            status="provider_calls_disabled",
            block_reason=diagnostics["why_provider_calls_zero"],
            diagnostics=diagnostics,
        )

    pending_rows = list(selection.get("selected_rows") or [])
    if not pending_rows:
        return _empty_provider_check(
            allow_tiny_provider_calls=allow_tiny_provider_calls,
            max_provider_calls=effective_calls,
            max_records=effective_records,
            status="no_pending_prediction_market_records" if int(selection.get("pending_records_seen") or 0) <= 0 else "no_provider_eligible_records",
            block_reason=diagnostics["why_provider_calls_zero"],
            diagnostics=diagnostics,
        )

    if str(readiness.get("provider_readiness_status") or "") != "provider_ready":
        return _empty_provider_check(
            allow_tiny_provider_calls=allow_tiny_provider_calls,
            max_provider_calls=effective_calls,
            max_records=effective_records,
            status="provider_not_ready",
            block_reason=diagnostics["why_provider_calls_zero"],
            diagnostics=diagnostics,
        )

    fetched = _fetch_tiny_read_only_records(
        pending_rows,
        adapter=adapter,
        max_provider_calls=effective_calls,
    )
    post_fetch_diagnostics = _base_zero_call_diagnostics(
        allow_tiny_provider_calls=allow_tiny_provider_calls,
        effective_calls=effective_calls,
        effective_records=effective_records,
        readiness=readiness,
        selection=selection,
        calls_attempted=int(fetched.get("provider_calls_attempted") or 0),
    )
    checked_rows = list(fetched.get("checked_rows") or [])
    provider_records = list(fetched.get("provider_records") or [])
    discovery = discover_kalshi_settlements_for_pending_rows(checked_rows, read_only_records=provider_records)
    provider_candidates: list[dict[str, Any]] = []
    provider_rejections = dict(fetched.get("rejected_reason_counts") or {})
    for candidate in list(discovery.get("completion_candidates") or []):
        if str(candidate.get("final_outcome") or "").lower() not in {"yes", "no"}:
            provider_rejections["explicit_non_yes_no_result"] = provider_rejections.get("explicit_non_yes_no_result", 0) + 1
            continue
        evidence = evaluate_outcome_evidence(
            {**candidate, "result": candidate.get("final_outcome")},
            source_record_type="provider_settlement_discovery",
        )
        if bool(evidence.get("candidate_accepted")):
            provider_candidates.append(evidence)
        else:
            reason = str(evidence.get("rejection_reason") or "unknown_provider_result")
            provider_rejections[reason] = provider_rejections.get(reason, 0) + 1

    for reason, count in dict(discovery.get("rejected_reason_counts") or {}).items():
        provider_rejections[str(reason)] = provider_rejections.get(str(reason), 0) + int(count)

    provider_rejected_count = int(sum(provider_rejections.values()))
    status = "provider_settlement_check_complete"
    if fetched.get("rate_limited"):
        status = "provider_rate_limited"
    elif fetched.get("stop_reason") and fetched.get("provider_calls_failed"):
        status = "provider_error_stopped"
    return {
        "provider_settlement_check_enabled": True,
        "provider_settlement_check_status": status,
        "provider_call_block_reason": fetched.get("stop_reason"),
        "provider_calls_attempted": int(fetched.get("provider_calls_attempted") or 0),
        "provider_calls_succeeded": int(fetched.get("provider_calls_succeeded") or 0),
        "provider_calls_failed": int(fetched.get("provider_calls_failed") or 0),
        "provider_records_returned": int(fetched.get("provider_records_returned") or 0),
        "markets_checked_with_provider": int(fetched.get("markets_checked_with_provider") or 0),
        "explicit_outcomes_found": len(provider_candidates),
        "provider_rejected_count": provider_rejected_count,
        "provider_rejection_reasons": provider_rejections,
        "provider_candidates": provider_candidates,
        "rate_limited": bool(fetched.get("rate_limited")),
        "persisted": False,
        "dry_run": True,
        "provider_write": False,
        "execution_allowed": False,
        "execution_allowed_count": 0,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "max_provider_calls_effective": effective_calls,
        "max_records_effective": effective_records,
        "raw_payload_included": False,
        "secrets_included": False,
        **post_fetch_diagnostics,
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
    allow_tiny_provider_calls: bool = False,
    max_provider_calls: int = 0,
    max_records: int = 0,
    provider_adapter: Any | None = None,
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
    provider_check = run_tiny_read_only_settlement_check(
        filtered,
        allow_tiny_provider_calls=allow_tiny_provider_calls,
        max_provider_calls=max_provider_calls,
        max_records=max_records,
        adapter=provider_adapter,
    )
    provider_candidates = [row for row in list(provider_check.get("provider_candidates") or []) if isinstance(row, dict)]
    candidates.extend(provider_candidates)
    for reason, count in dict(provider_check.get("provider_rejection_reasons") or {}).items():
        rejection_counts[str(reason)] = rejection_counts.get(str(reason), 0) + int(count)
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
        "local_rejected_count": len(rejected),
        "provider_rejected_count": int(provider_check.get("provider_rejected_count") or 0),
        "rejected_count": len(rejected) + int(provider_check.get("provider_rejected_count") or 0),
        "rejection_reason_counts": rejection_counts,
        "rejection_reasons": rejection_counts,
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
        "persisted": False,
        "dry_run": True,
        **{key: value for key, value in provider_check.items() if key != "provider_candidates"},
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

from __future__ import annotations

from typing import Any

_SECRET_KEYS = ("key", "secret", "token", "password", "auth", "credential", "signature", "header")


def _redact(payload: Any) -> Any:
    if isinstance(payload, dict):
        out: dict[str, Any] = {}
        for k, v in payload.items():
            lk = str(k).lower()
            if any(s in lk for s in _SECRET_KEYS):
                out[k] = "[redacted]"
            elif lk in {"provider_payload", "raw_payload", "external_payload", "source_payload", "source_payload_redacted", "raw_provider_payload", "raw_kalshi_payload", "raw_sharp_payload"}:
                out[k] = "[omitted]"
            else:
                out[k] = _redact(v)
        return out
    if isinstance(payload, list):
        return [_redact(v) for v in payload]
    return payload


def redact_and_limit_payload(payload: Any, limit: int = 10, verbose: bool = False) -> Any:
    safe = _redact(payload)
    max_items = 100 if verbose else 10
    cap = max(1, min(int(limit or max_items), max_items))
    if isinstance(safe, list):
        return safe[:cap]
    if isinstance(safe, dict):
        compact = dict(safe)
        for k in list(compact.keys()):
            if isinstance(compact[k], list):
                compact[k] = compact[k][:cap]
        return compact
    return safe


def compact_health_response(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(payload.get("ok", True)),
        "status": "ok" if payload.get("ok", True) else "error",
        "timestamp": payload.get("checked_at") or payload.get("created_at"),
        "dry_run": bool(payload.get("dry_run", True)),
        "human_approval_required": bool(payload.get("human_approval_required", True)),
        "auto_execution_enabled": bool(payload.get("auto_execution_enabled", False)),
        "counts": {
            "review_queue_count": int(payload.get("review_queue_count", payload.get("count", 0))),
            "provider_count": int(payload.get("provider_count", 0)),
            "enabled_provider_count": int(payload.get("enabled_provider_count", 0)),
            "live_calls_enabled_count": int(payload.get("live_calls_enabled_count", 0)),
            "providers_blocked_count": int(payload.get("providers_blocked_count", 0)),
        },
        "blockers": list(payload.get("blockers", []))[:10],
        "top_reasons": list(payload.get("top_reasons", []))[:10],
        "review_queue_storage_backend": payload.get("review_queue_storage_backend"),
        "review_queue_total_count": int(payload.get("review_queue_total_count", payload.get("review_queue_count", payload.get("count", 0)))),
        "review_queue_last_updated_at": payload.get("review_queue_last_updated_at"),
        "review_queue_latest_run_id": payload.get("review_queue_latest_run_id"),
        "review_queue_read_ok": bool(payload.get("review_queue_read_ok", True)),
    }


def compact_review_queue_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    items = list(payload.get("items", []))[: max(1, min(limit, 10))]
    top = []
    for it in items:
        top.append(
            {
                "candidate_type": it.get("candidate_type"),
                "provider_id": it.get("provider_id", it.get("provider")),
                "event_id": it.get("event_id"),
                "event_name": it.get("event_name"),
                "sport": it.get("sport"),
                "league": it.get("league"),
                "market": it.get("market"),
                "selection": it.get("selection"),
                "market_id": it.get("market_id"),
                "contract_id": it.get("contract_id"),
                "ticker": it.get("ticker"),
                "source_type": it.get("source_type", it.get("market_type")),
                "reason": it.get("reason"),
                "reason_codes": list(it.get("reason_codes", []))[:10],
                "book": it.get("book"),
                "best_book": it.get("best_book"),
                "best_odds": it.get("best_odds"),
                "best_line": it.get("best_line"),
                "yes_bid": it.get("yes_bid"),
                "yes_ask": it.get("yes_ask"),
                "no_bid": it.get("no_bid"),
                "no_ask": it.get("no_ask"),
                "yes_price": it.get("yes_price"),
                "no_price": it.get("no_price"),
                "price_source": it.get("price_source"),
                "derived_price": bool(it.get("derived_price", False)),
                "partial_pricing": bool(it.get("partial_pricing", False)),
                "pricing_quality": it.get("pricing_quality"),
                "implied_probability": it.get("implied_probability"),
                "volume": it.get("volume"),
                "open_interest": it.get("open_interest"),
                "liquidity_score": it.get("liquidity_score"),
                "liquidity_policy_version": it.get("liquidity_policy_version"),
                "liquidity_source": it.get("liquidity_source"),
                "liquidity_tier": it.get("liquidity_tier"),
                "liquidity_reason": it.get("liquidity_reason"),
                "low_liquidity_flag": bool(it.get("low_liquidity_flag", it.get("low_liquidity", False))),
                "missing_liquidity_flag": bool(it.get("missing_liquidity_flag", it.get("missing_liquidity", False))),
                "low_liquidity": bool(it.get("low_liquidity", False)),
                "close_time": it.get("close_time", it.get("market_close_at")),
                "status_reason": it.get("status_reason"),
                "settlement_rule_status": it.get("settlement_rule_status"),
                "data_quality_status": it.get("data_quality_status"),
                "no_vig_probability": it.get("no_vig_probability"),
                "ev_percent": it.get("ev_percent"),
                "opportunity_score": it.get("opportunity_score"),
                "review_priority_score": it.get("review_priority_score"),
                "confidence_score": it.get("confidence_score"),
                "risk_score": it.get("risk_score"),
                "spread_score": it.get("spread_score"),
                "pricing_quality_score": it.get("pricing_quality_score"),
                "close_time_score": it.get("close_time_score"),
                "market_structure_score": it.get("market_structure_score"),
                "recommended_action": it.get("recommended_action"),
                "recommendation_status": it.get("recommendation_status", "review_only"),
                "blockers": list(it.get("blockers", []))[:10],
                "top_reasons": list(it.get("top_reasons", []))[:5],
                "human_approval_required": True,
                "auto_execution_enabled": False,
                "execution_allowed": False,
            }
        )
    summary = dict(payload.get("summary", {}))
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "ok"),
        "review_required_count": len([item for item in top if item.get("recommended_action") in {"review_required", "urgent_review"}]),
        "watch_recheck_count": len([item for item in top if item.get("recommended_action") == "watch_recheck"]),
        "total_count": int(summary.get("total_count", payload.get("count", len(top)))),
        "provider_counts": dict(summary.get("provider_counts", {})),
        "kalshi_candidate_count": int(summary.get("kalshi_candidate_count", 0)),
        "sharp_candidate_count": int(summary.get("sharp_candidate_count", 0)),
        "prediction_market_count": int(summary.get("prediction_market_count", 0)),
        "sportsbook_count": int(summary.get("sportsbook_count", 0)),
        "review_only_count": int(summary.get("review_only_count", 0)),
        "execution_allowed_count": int(summary.get("execution_allowed_count", 0)),
        "low_liquidity_count": int(summary.get("low_liquidity_count", summary.get("flagged_low_liquidity_count", 0))),
        "missing_liquidity_count": int(summary.get("missing_liquidity_count", 0)),
        "liquidity_tier_counts": dict(summary.get("liquidity_tier_counts", {})),
        "high_priority_count": int(summary.get("high_priority_count", 0)),
        "average_review_priority_score": float(summary.get("average_review_priority_score", 0.0)),
        "flagged_low_liquidity_count": int(summary.get("flagged_low_liquidity_count", 0)),
        "flagged_partial_pricing_count": int(summary.get("flagged_partial_pricing_count", 0)),
        "rejected_count": int(summary.get("rejected_count", 0)),
        "rejected_reason_counts": dict(summary.get("rejected_reason_counts", {})),
        "storage_backend": payload.get("storage_backend", "unknown"),
        "last_updated_at": payload.get("last_updated_at"),
        "latest_run_id": payload.get("latest_run_id"),
        "queue_read_ok": bool(payload.get("queue_read_ok", True)),
        "queue_error_category": payload.get("queue_error_category"),
        "queue_read_path": payload.get("queue_read_path"),
        "items_read_count": int(payload.get("items_read_count", summary.get("total_count", payload.get("count", len(top))))),
        "compact_filter_applied": bool(payload.get("compact_filter_applied", False)),
        "count": int(payload.get("count", len(top))),
        "items": top,
    }


def compact_run_once_response(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "ok" if payload.get("ok", True) else "error"),
        "run_id": payload.get("run_id"),
        "report_id": payload.get("report_id") or payload.get("run_id"),
        "dry_run": bool(payload.get("dry_run", True)),
        "human_approval_required": bool(payload.get("human_approval_required", True)),
        "auto_execution_enabled": bool(payload.get("auto_execution_enabled", False)),
        "records_received": int(payload.get("records_received", 0)),
        "records_valid": int(payload.get("records_valid", 0)),
        "records_rejected": int(payload.get("records_rejected", 0)),
        "sharp_records_received": int(payload.get("sharp_records_received", 0)),
        "sharp_records_valid": int(payload.get("sharp_records_valid", 0)),
        "sharp_records_rejected": int(payload.get("sharp_records_rejected", 0)),
        "sharp_candidates_created": int(payload.get("sharp_candidates_created", 0)),
        "sharp_blockers": list(payload.get("sharp_blockers", []))[:10],
        "kalshi_records_received": int(payload.get("kalshi_records_received", 0)),
        "kalshi_records_valid": int(payload.get("kalshi_records_valid", 0)),
        "kalshi_records_rejected": int(payload.get("kalshi_records_rejected", 0)),
        "kalshi_candidates_created": int(payload.get("kalshi_candidates_created", 0)),
        "kalshi_watch_items_created": int(payload.get("kalshi_watch_items_created", 0)),
        "kalshi_flagged_low_liquidity_count": int(payload.get("kalshi_flagged_low_liquidity_count", 0)),
        "kalshi_flagged_partial_pricing_count": int(payload.get("kalshi_flagged_partial_pricing_count", 0)),
        "kalshi_liquidity_tier_counts": dict(payload.get("kalshi_liquidity_tier_counts", {})),
        "kalshi_missing_liquidity_count": int(payload.get("kalshi_missing_liquidity_count", 0)),
        "kalshi_high_priority_count": int(payload.get("kalshi_high_priority_count", 0)),
        "kalshi_average_review_priority_score": float(payload.get("kalshi_average_review_priority_score", 0.0)),
        "kalshi_rejected_reason_counts": dict(payload.get("kalshi_rejected_reason_counts", {})),
        "kalshi_price_field_telemetry": dict(payload.get("kalshi_price_field_telemetry", {})),
        "kalshi_blockers": list(payload.get("kalshi_blockers", []))[:10],
        "candidates_created": int(payload.get("candidates_created", 0)),
        "review_required_count": int(payload.get("review_required_count", 0)),
        "watch_recheck_count": int(payload.get("watch_recheck_count", 0)),
        "review_queue_items_written": int(payload.get("review_queue_items_written", 0)),
        "review_queue_storage_backend": payload.get("review_queue_storage_backend"),
        "review_queue_write_path": payload.get("review_queue_write_path"),
        "review_queue_latest_run_id": payload.get("review_queue_latest_run_id"),
        "review_queue_last_updated_at": payload.get("review_queue_last_updated_at"),
        "paper_decisions_written": int(payload.get("paper_decisions_written", 0)),
        "paper_decisions_count": int(payload.get("paper_decisions_count", 0)),
        "paper_ledger_storage_backend": payload.get("paper_ledger_storage_backend"),
        "paper_ledger_write_path": payload.get("paper_ledger_write_path"),
        "paper_ledger_latest_run_id": payload.get("paper_ledger_latest_run_id"),
        "calibration_status": (payload.get("calibration") or {}).get("status"),
        "calibration_settled_count": int((payload.get("calibration") or {}).get("settled_count", 0)),
        "calibration_coverage_rate": float((payload.get("calibration") or {}).get("coverage_rate", 0.0)),
        "blockers": list(payload.get("blockers", []))[:10],
        "report_path": (payload.get("report") or {}).get("path") or payload.get("report_path"),
    }


def compact_calibration_response(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "insufficient_data"),
        "schema_version": payload.get("schema_version"),
        "created_at": payload.get("created_at"),
        "dry_run": bool(payload.get("dry_run", True)),
        "human_approval_required": bool(payload.get("human_approval_required", True)),
        "auto_execution_enabled": bool(payload.get("auto_execution_enabled", False)),
        "review_items_count": int(payload.get("review_items_count", 0)),
        "paper_decisions_count": int(payload.get("paper_decisions_count", payload.get("paper_ledger_records_count", 0))),
        "outcome_records_count": int(payload.get("outcome_records_count", 0)),
        "matched_outcomes_count": int(payload.get("matched_outcomes_count", payload.get("matched_outcome_count", 0))),
        "unmatched_outcomes_count": int(payload.get("unmatched_outcomes_count", payload.get("unmatched_outcome_count", 0))),
        "ambiguous_matches_count": int(payload.get("ambiguous_matches_count", 0)),
        "settled_count": int(payload.get("settled_count", 0)),
        "pending_count": int(payload.get("pending_count", 0)),
        "void_count": int(payload.get("void_count", 0)),
        "coverage_rate": float(payload.get("coverage_rate", 0.0)),
        "provider_counts": dict(payload.get("provider_counts", {})),
        "market_type_counts": dict(payload.get("market_type_counts", {})),
        "outcome_provider_counts": dict(payload.get("outcome_provider_counts", {})),
        "outcome_status_counts": dict(payload.get("outcome_status_counts", {})),
        "liquidity_tier_counts": dict(payload.get("liquidity_tier_counts", {})),
        "score_bucket_counts": dict(payload.get("score_bucket_counts", {})),
        "score_field_presence_counts": dict(payload.get("score_field_presence_counts", {})),
        "settlement_field_presence_counts": dict(payload.get("settlement_field_presence_counts", {})),
        "records_with_outcome_count": int(payload.get("records_with_outcome_count", 0)),
        "records_without_outcome_count": int(payload.get("records_without_outcome_count", 0)),
        "metrics": dict(payload.get("metrics", {})),
        "warnings": list(payload.get("warnings", []))[:10],
        "next_required_data": list(payload.get("next_required_data", []))[:10],
        "storage_backend": payload.get("storage_backend"),
        "latest_batch_id": payload.get("latest_batch_id"),
        "outcome_read_ok": bool(payload.get("outcome_read_ok", True)),
        "compact_response": True,
        "raw_payload_included": False,
        "execution_allowed_count": 0,
        "report_path": payload.get("report_path"),
    }


def compact_outcome_ingest_response(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "outcomes_validated"),
        "dry_run": bool(payload.get("dry_run", True)),
        "local_persistence": bool(payload.get("local_persistence", False)),
        "persisted": bool(payload.get("persisted", False)),
        "persistence_requested": bool(payload.get("persistence_requested", False)),
        "persistence_blocked_reason": payload.get("persistence_blocked_reason"),
        "provider_write": False,
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "records_received": int(payload.get("records_received", 0)),
        "records_valid": int(payload.get("records_valid", 0)),
        "records_rejected": int(payload.get("records_rejected", 0)),
        "rejected_reason_counts": dict(payload.get("rejected_reason_counts", {})),
        "duplicate_count": int(payload.get("duplicate_count", 0)),
        "outcome_records_written": int(payload.get("outcome_records_written", 0)),
        "storage_backend": payload.get("storage_backend", "file"),
        "latest_batch_id": payload.get("latest_batch_id"),
        "last_updated_at": payload.get("last_updated_at"),
        "outcome_write_path": payload.get("outcome_write_path"),
    }


def compact_outcomes_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 10))
    records = list(payload.get("records", payload.get("items", [])))[:cap]
    compact_records = []
    for row in records:
        compact_records.append(
            {
                "outcome_id": row.get("outcome_id"),
                "provider": row.get("provider"),
                "market_type": row.get("market_type"),
                "ticker": row.get("ticker"),
                "contract_id": row.get("contract_id"),
                "review_item_id": row.get("review_item_id"),
                "decision_id": row.get("decision_id"),
                "run_id": row.get("run_id"),
                "outcome_status": row.get("outcome_status"),
                "final_outcome": row.get("final_outcome"),
                "settled_at": row.get("settled_at"),
                "source": row.get("source"),
                "evidence_type": row.get("evidence_type"),
                "evidence_summary": row.get("evidence_summary"),
                "created_at": row.get("created_at"),
            }
        )
    summary = dict(payload.get("summary", {}))
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "ok"),
        "total_count": int(summary.get("total_count", payload.get("total_count", len(records)))),
        "provider_counts": dict(summary.get("provider_counts", {})),
        "outcome_status_counts": dict(summary.get("outcome_status_counts", {})),
        "final_outcome_counts": dict(summary.get("final_outcome_counts", {})),
        "latest_batch_id": payload.get("latest_batch_id"),
        "storage_backend": payload.get("storage_backend", "file"),
        "last_updated_at": payload.get("last_updated_at"),
        "outcome_read_ok": bool(payload.get("outcome_read_ok", True)),
        "outcome_error_category": payload.get("outcome_error_category"),
        "count": len(compact_records),
        "records": compact_records,
    }


def compact_settlement_discovery_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 10))
    candidates = list(payload.get("completion_candidates", []))[:cap]
    compact_candidates = []
    for row in candidates:
        compact_candidates.append(
            {
                "provider": row.get("provider"),
                "market_type": row.get("market_type"),
                "decision_id": row.get("decision_id"),
                "review_item_id": row.get("review_item_id"),
                "run_id": row.get("run_id"),
                "ticker": row.get("ticker"),
                "contract_id": row.get("contract_id"),
                "outcome_status": row.get("outcome_status"),
                "final_outcome": row.get("final_outcome"),
                "settled_at": row.get("settled_at"),
                "source": row.get("source"),
                "evidence_type": row.get("evidence_type"),
                "evidence_summary": row.get("evidence_summary"),
            }
        )
    kalshi = dict(payload.get("kalshi_discovery", {}))
    imported = dict(payload.get("imported_file", {}))
    pending = dict(payload.get("pending_diagnostics", {}))
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "no_completion_candidates"),
        "provider_write": False,
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "pending_rows_count": int(pending.get("pending_rows_count", 0)),
        "completed_rows_count": int(pending.get("completed_rows_count", 0)),
        "rows_with_decision_id": int(pending.get("rows_with_decision_id", 0)),
        "rows_with_review_item_id": int(pending.get("rows_with_review_item_id", 0)),
        "rows_with_ticker": int(pending.get("rows_with_ticker", 0)),
        "rows_with_contract_id": int(pending.get("rows_with_contract_id", 0)),
        "rows_missing_outcome_status": int(pending.get("rows_missing_outcome_status", 0)),
        "rows_missing_final_outcome": int(pending.get("rows_missing_final_outcome", 0)),
        "rows_missing_settled_at": int(pending.get("rows_missing_settled_at", 0)),
        "pending_kalshi_rows": int(kalshi.get("pending_kalshi_rows", 0)),
        "read_only_records_checked": int(kalshi.get("read_only_records_checked", 0)),
        "read_only_records_matched": int(kalshi.get("read_only_records_matched", 0)),
        "settled_yes_count": int(kalshi.get("settled_yes_count", 0)),
        "settled_no_count": int(kalshi.get("settled_no_count", 0)),
        "not_settled_count": int(kalshi.get("not_settled_count", 0)),
        "unknown_count": int(kalshi.get("unknown_count", 0)),
        "void_cancelled_count": int(kalshi.get("void_cancelled_count", 0)),
        "settlement_field_presence_counts": dict(kalshi.get("settlement_field_presence_counts", {})),
        "rejected_reason_counts": dict(kalshi.get("rejected_reason_counts", {})),
        "import_rows_found": int(imported.get("rows_found", 0)),
        "import_valid_rows": int(imported.get("valid_rows", 0)),
        "import_rejected_rows": int(imported.get("rejected_rows", 0)),
        "import_rejected_reason_counts": dict(imported.get("rejected_reason_counts", {})),
        "completion_candidates_count": int(payload.get("completion_candidates_count", 0)),
        "count": len(compact_candidates),
        "completion_candidates": compact_candidates,
        "completion_candidate_path": payload.get("completion_candidate_path"),
        "compact_response": True,
        "raw_payload_included": False,
    }


def compact_calibration_collector_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    contracts = list(payload.get("selected_contracts", []))[: max(1, min(int(limit or 10), 10))]
    safe_contracts = []
    contract_fields = (
        "ticker",
        "contract_id",
        "event_id",
        "event_name",
        "market_id",
        "market_type",
        "collector_bucket",
        "close_time",
        "status",
        "observed_price",
        "implied_probability",
        "yes_price",
        "no_price",
        "yes_bid",
        "yes_ask",
        "volume",
        "open_interest",
        "liquidity_score",
        "spread_score",
        "pricing_quality_score",
        "close_time_score",
        "market_structure_score",
        "risk_score",
        "confidence_score",
        "review_priority_score",
        "liquidity_tier",
        "reason_codes",
        "recommended_action",
        "paper_only",
        "execution_allowed",
    )
    for row in contracts:
        if not isinstance(row, dict):
            continue
        safe_contracts.append({field: _redact(row.get(field)) for field in contract_fields if field in row})
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "collector_cycle_complete"),
        "cycle_id": payload.get("cycle_id"),
        "dry_run": bool(payload.get("dry_run", True)),
        "persist_outcomes": bool(payload.get("persist_outcomes", False)),
        "lock_acquired": bool(payload.get("lock_acquired", False)),
        "skipped_due_to_lock": bool(payload.get("skipped_due_to_lock", False)),
        "markets_scanned": int(payload.get("markets_scanned", 0)),
        "eligible_contracts_found": int(payload.get("eligible_contracts_found", 0)),
        "selected_short_term": int(payload.get("selected_short_term", 0)),
        "selected_medium_term": int(payload.get("selected_medium_term", 0)),
        "selected_long_term": int(payload.get("selected_long_term", 0)),
        "new_contracts_added": int(payload.get("new_contracts_added", 0)),
        "new_contracts_selected": int(payload.get("new_contracts_selected", 0)),
        "daily_new_contract_limit": int(payload.get("daily_new_contract_limit", 0)),
        "daily_new_contracts_remaining": int(payload.get("daily_new_contracts_remaining", 0)),
        "duplicate_contracts_skipped": int(payload.get("duplicate_contracts_skipped", 0)),
        "duplicate_outcomes_skipped": int(payload.get("duplicate_outcomes_skipped", 0)),
        "records_checked": int(payload.get("records_checked", 0)),
        "read_only_records_matched": int(payload.get("read_only_records_matched", 0)),
        "explicit_settlement_count": int(payload.get("explicit_settlement_count", 0)),
        "settled_yes_count": int(payload.get("settled_yes_count", 0)),
        "settled_no_count": int(payload.get("settled_no_count", 0)),
        "void_cancelled_count": int(payload.get("void_cancelled_count", 0)),
        "unknown_count": int(payload.get("unknown_count", 0)),
        "not_settled_count": int(payload.get("not_settled_count", 0)),
        "no_match_count": int(payload.get("no_match_count", 0)),
        "stale_count": int(payload.get("stale_count", 0)),
        "dry_run_ingest": dict(payload.get("dry_run_ingest", {})),
        "outcomes_persisted": int(payload.get("outcomes_persisted", 0)),
        "total_outcome_records_count": int(payload.get("total_outcome_records_count", 0)),
        "matched_outcomes_count": int(payload.get("matched_outcomes_count", 0)),
        "calibration_status": payload.get("calibration_status"),
        "coverage_rate": float(payload.get("coverage_rate", 0.0)),
        "insufficient_sample": bool(payload.get("insufficient_sample", False)),
        "next_required_data": list(payload.get("next_required_data", []))[:10],
        "deepseek_review_status": payload.get("deepseek_review_status", "not_requested"),
        "provider_write": False,
        "execution_allowed_count": 0,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "human_approval_required": True,
        "paper_only": True,
        "collector_policy": dict(payload.get("collector_policy", {})),
        "sample_targets": dict(payload.get("sample_targets", {})),
        "selection_rejected_reason_counts": dict(payload.get("selection_rejected_reason_counts", {})),
        "provider_blockers": list(payload.get("provider_blockers", []))[:10],
        "cycle_report_path": payload.get("cycle_report_path"),
        "latest_cycle_path": payload.get("latest_cycle_path"),
        "daily_report_path": payload.get("daily_report_path"),
        "daily_markdown_path": payload.get("daily_markdown_path"),
        "count": len(safe_contracts),
        "selected_contracts": safe_contracts,
        "compact_response": True,
        "raw_payload_included": False,
    }


def compact_deepseek_review_response(payload: dict[str, Any]) -> dict[str, Any]:
    review = dict(payload.get("review", {}))
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "disabled"),
        "enabled": bool(payload.get("enabled", False)),
        "local_server_reachable": bool(payload.get("local_server_reachable", False)),
        "json_schema_valid": bool(payload.get("json_schema_valid", False)),
        "rejected_reason": payload.get("rejected_reason"),
        "forbidden_actions_rejected": bool(payload.get("forbidden_actions_rejected", False)),
        "reviewer_side_effects": "none",
        "provider_write": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "review": {
            "summary": review.get("summary"),
            "crosscheck_status": review.get("crosscheck_status"),
            "risk_flags": list(review.get("risk_flags", []))[:50],
            "valuation_mismatches": list(review.get("valuation_mismatches", []))[:50],
            "missing_inputs": list(review.get("missing_inputs", []))[:50],
            "data_quality_notes": list(review.get("data_quality_notes", []))[:50],
            "recommended_action": review.get("recommended_action"),
            "confidence": float(review.get("confidence", 0.0) or 0.0),
            "must_not_execute": True,
        },
        "compact_response": True,
        "raw_payload_included": False,
    }


def compact_governance_inventory(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    items = list(payload.get("inventory", []))[: max(1, min(limit, 10))]
    return {
        "ok": bool(payload.get("ok", True)),
        "status": "ok",
        "timestamp": payload.get("checked_at"),
        "dry_run": True,
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "counts": {"inventory": int(len(payload.get("inventory", [])))},
        "items": [
            {
                "decision": i.get("status_reason", "review_required"),
                "recommended_action": "review_required",
                "opportunity_score": None,
                "confidence": None,
                "risk": None,
                "blockers": [],
            }
            for i in items
        ],
    }


def compact_governance_report(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(payload.get("ok", True)),
        "status": "ok",
        "timestamp": payload.get("created_at") or payload.get("checked_at"),
        "dry_run": True,
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "counts": {
            "blocked_model_count": int(payload.get("blocked_model_count", 0)),
            "eligible_model_count": int(payload.get("eligible_model_count", 0)),
        },
        "top_reasons": list(payload.get("recommended_next_actions", []))[:10],
    }


def compact_validation_response(payload: dict[str, Any]) -> dict[str, Any]:
    v = payload.get("validation", payload)
    return {
        "ok": bool(payload.get("ok", True)),
        "status": "ok",
        "timestamp": None,
        "dry_run": bool(payload.get("dry_run", True)),
        "human_approval_required": bool(v.get("human_approval_required", True)),
        "auto_execution_enabled": False,
        "decision": v.get("promotion_recommendation", "review_required"),
        "blockers": list(v.get("blocked_reasons", []))[:10],
        "top_reasons": list(v.get("blocked_reasons", []))[:10],
    }


def compact_performance_health(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(payload.get("ok", True)),
        "status": "ok" if payload.get("ok", True) else "error",
        "timestamp": payload.get("checked_at"),
        "dry_run": True,
        "human_approval_required": True,
        "auto_execution_enabled": False,
        "counts": {
            "paper_ledger_count": int(payload.get("paper_ledger_count", 0)),
            "settled_paper_count": int(payload.get("settled_paper_count", 0)),
            "clv_sample_size": int(payload.get("clv_sample_size", 0)),
            "models_with_positive_clv": int(payload.get("models_with_positive_clv", 0)),
            "models_needing_revalidation": int(payload.get("models_needing_revalidation", 0)),
        },
        "latest_performance_report_id": payload.get("latest_performance_report_id"),
    }


def compact_performance_report(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "backtest_complete"),
        "report_id": payload.get("report_id"),
        "model_id": payload.get("model_id"),
        "sample_size": int(payload.get("sample_size", 0)),
        "realized_roi_percent": float(payload.get("realized_roi_percent", 0.0)),
        "average_clv_percent": float(payload.get("average_clv_percent", 0.0)),
        "positive_clv_rate": float(payload.get("positive_clv_rate", 0.0)),
        "max_drawdown_percent": float(payload.get("max_drawdown_percent", 0.0)),
        "brier_score": float(payload.get("brier_score", 0.0)),
        "calibration_status": payload.get("calibration_status"),
        "performance_status": payload.get("performance_status"),
        "blocked_reasons": list(payload.get("blocked_reasons", []))[:10],
        "recommended_next_action": payload.get("recommended_next_action", "watch_recheck"),
        "report_path": payload.get("report_path"),
    }


def compact_provider_health_response(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "ok"),
        "timestamp": payload.get("timestamp"),
        "provider_count": int(payload.get("provider_count", 0)),
        "enabled_provider_count": int(payload.get("enabled_provider_count", 0)),
        "live_calls_enabled_count": int(payload.get("live_calls_enabled_count", 0)),
        "blocked_count": int(payload.get("blocked_count", 0)),
        "dry_run": bool(payload.get("dry_run", True)),
        "blockers": list(payload.get("blockers", []))[:10],
        "top_provider_statuses": list(payload.get("top_provider_statuses", []))[:10],
    }


def compact_provider_registry_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    provider_items = list(payload.get("providers", []))[: max(1, min(limit, 10))]
    compact_items = []
    for item in provider_items:
        compact_items.append(
            {
                "provider_id": item.get("provider_id"),
                "provider_type": item.get("provider_type"),
                "enabled": bool(item.get("enabled", False)),
                "dry_run": bool(item.get("dry_run", True)),
                "live_calls_enabled": bool(item.get("live_calls_enabled", False)),
                "supports_streaming": bool(item.get("supports_streaming", False)),
                "supports_polling": bool(item.get("supports_polling", True)),
                "min_poll_seconds": int(item.get("min_poll_seconds", 60)),
                "contract_status": item.get("contract_status", "defined"),
            }
        )
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "ok"),
        "timestamp": payload.get("timestamp"),
        "provider_count": int(payload.get("provider_count", len(payload.get("providers", [])))),
        "enabled_provider_count": int(payload.get("enabled_provider_count", 0)),
        "live_calls_enabled_count": int(payload.get("live_calls_enabled_count", 0)),
        "blocked_count": int(payload.get("blocked_count", 0)),
        "dry_run": True,
        "blockers": list(payload.get("blockers", []))[:10],
        "top_provider_statuses": compact_items,
    }


def compact_provider_status(payload: dict[str, Any]) -> dict[str, Any]:
    diag = payload.get("diagnostic") if isinstance(payload.get("diagnostic"), dict) else {}
    compact_diag = None
    if diag:
        compact_diag = {
            "url_host": diag.get("url_host"),
            "url_path": diag.get("url_path"),
            "method": diag.get("method", "GET"),
            "error_class": diag.get("error_class"),
            "error_category": diag.get("error_category"),
            "timeout_seconds": diag.get("timeout_seconds"),
            "retry_count": diag.get("retry_count"),
            "secret_redacted": True,
        }
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "blocked"),
        "provider_id": payload.get("provider_id"),
        "provider_enabled": bool(payload.get("provider_enabled", False)),
        "dry_run": bool(payload.get("dry_run", True)),
        "live_calls_enabled": bool(payload.get("live_calls_enabled", False)),
        "credential_status": payload.get("credential_status", "missing_credentials"),
        "records_received": int(payload.get("records_received", 0)),
        "records_valid": int(payload.get("records_valid", 0)),
        "records_rejected": int(payload.get("records_rejected", 0)),
        "rejection_reason_counts": dict(payload.get("rejection_reason_counts", {})),
        "http_status": payload.get("http_status"),
        "diagnostic": compact_diag,
        "blockers": list(payload.get("blockers", []))[:10],
        "snapshot_path": payload.get("snapshot_path"),
    }

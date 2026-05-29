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
            elif lk in {"provider_payload", "raw_payload", "external_payload"}:
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
        "blockers": list(payload.get("blockers", []))[:10],
        "report_path": (payload.get("report") or {}).get("path") or payload.get("report_path"),
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

from __future__ import annotations

from typing import Any

from .secret_safety import looks_like_secret_value, redact_string

_SECRET_KEYS = (
    "key",
    "secret",
    "token",
    "password",
    "auth",
    "credential",
    "signature",
    "header",
    "bearer",
    "cookie",
    "private",
)


def _compact_storage_health(payload: dict[str, Any]) -> dict[str, Any]:
    storage = payload.get("storage_health") or payload.get("storage") or {}
    if not isinstance(storage, dict):
        storage = {}
    return {
        "env_var": storage.get("env_var", "AUTOMATION_DATA_DIR"),
        "data_dir": storage.get("data_dir"),
        "backend": storage.get("backend", payload.get("storage_backend", "file")),
        "configured": bool(storage.get("configured", False)),
        "render_persistent_disk_expected": bool(storage.get("render_persistent_disk_expected", False)),
        "persistence_warning": storage.get("persistence_warning") or payload.get("persistence_warning_if_ephemeral"),
        "read_ok": bool(storage.get("read_ok", True)),
        "write_ok": bool(storage.get("write_ok", True)),
    }


def _redact(payload: Any) -> Any:
    if isinstance(payload, dict):
        out: dict[str, Any] = {}
        for k, v in payload.items():
            lk = str(k).lower()
            if any(s in lk for s in _SECRET_KEYS):
                out[k] = "[redacted]"
            elif lk in {
                "provider_payload",
                "raw_payload",
                "external_payload",
                "source_payload",
                "source_payload_redacted",
                "raw_provider_payload",
                "raw_kalshi_payload",
                "raw_sharp_payload",
                "order_payload",
                "broker_order_payload",
                "sportsbook_bet_payload",
                "kalshi_order_payload",
                "crypto_trade_payload",
                "trade_payload",
                "execution_payload",
                "executable_order_payload",
                "raw_request_payload",
                "request_payload",
                "response_payload",
                "bet_slip",
                "wager_payload",
                "order_request",
                "provider_write_payload",
            }:
                out[k] = "[omitted]"
            else:
                out[k] = _redact(v)
        return out
    if isinstance(payload, list):
        return [_redact(v) for v in payload]
    if isinstance(payload, str) and looks_like_secret_value(payload):
        return redact_string(payload)
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


def _compact_manifold_item(item: dict[str, Any]) -> dict[str, Any]:
    source = item.get("source_summary") if isinstance(item.get("source_summary"), dict) else {}
    return {
        "asset_symbol": source.get("asset_symbol"),
        "asset_type": item.get("asset_type"),
        "market_type": item.get("market_type"),
        "manifold_cluster_id": item.get("manifold_cluster_id"),
        "manifold_cluster_name": item.get("manifold_cluster_name"),
        "manifold_family": item.get("manifold_family"),
        "nearest_historical_neighbors": int(item.get("nearest_historical_neighbors", 0) or 0),
        "neighbor_sample_size": int(item.get("neighbor_sample_size", 0) or 0),
        "centroid_distance": item.get("centroid_distance"),
        "nearest_neighbor_distance": item.get("nearest_neighbor_distance"),
        "out_of_distribution_score": item.get("out_of_distribution_score"),
        "out_of_distribution_risk": item.get("out_of_distribution_risk"),
        "historical_win_rate": item.get("historical_win_rate"),
        "historical_roi": item.get("historical_roi"),
        "calibration_status": item.get("calibration_status"),
        "insufficient_sample": bool(item.get("insufficient_sample", True)),
        "liquidity_quality": item.get("liquidity_quality"),
        "cluster_reliability_score": item.get("cluster_reliability_score"),
        "no_bet_trap_score": item.get("no_bet_trap_score"),
        "no_trade_trap_score": item.get("no_trade_trap_score"),
        "review_priority_adjustment": item.get("review_priority_adjustment"),
        "recommended_action": item.get("recommended_action"),
        "execution_allowed": False,
        "provider_write": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
    }


def compact_manifold_map_response(payload: dict[str, Any]) -> dict[str, Any]:
    item = payload.get("item") if isinstance(payload.get("item"), dict) else payload
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "manifold_map_complete"),
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "item": _compact_manifold_item(item),
        "raw_payload_included": False,
        "sensitive_fields_included": False,
        "secrets_included": False,
    }


def compact_manifold_review_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    sample = payload.get("sample_items")
    if not isinstance(sample, list):
        sample = [_compact_manifold_item(item) for item in payload.get("items", []) if isinstance(item, dict)]
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "manifold_review_complete"),
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "items_scanned": int(payload.get("items_scanned", 0) or 0),
        "items_mapped": int(payload.get("items_mapped", 0) or 0),
        "active_review_count": int(payload.get("active_review_count", 0) or 0),
        "watchlist_review_count": int(payload.get("watchlist_review_count", 0) or 0),
        "low_priority_review_count": int(payload.get("low_priority_review_count", 0) or 0),
        "no_review_count": int(payload.get("no_review_count", 0) or 0),
        "data_insufficient_count": int(payload.get("data_insufficient_count", 0) or 0),
        "no_bet_trap_count": int(payload.get("no_bet_trap_count", 0) or 0),
        "no_trade_trap_count": int(payload.get("no_trade_trap_count", 0) or 0),
        "out_of_distribution_count": int(payload.get("out_of_distribution_count", 0) or 0),
        "execution_allowed_count": 0,
        "sample_items": sample[:cap],
        "storage_backend": payload.get("storage_backend", "file"),
        "storage": _compact_storage_health(payload),
        "raw_payload_included": False,
        "sensitive_fields_included": False,
        "secrets_included": False,
    }


def compact_intelligence_readiness_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    safety = payload.get("safety_status") if isinstance(payload.get("safety_status"), dict) else {}
    coverage = payload.get("outcome_coverage_by_asset_type") if isinstance(payload.get("outcome_coverage_by_asset_type"), dict) else {}
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "intelligence_readiness"),
        "active_review_models": list(payload.get("active_review_models") or [])[:cap],
        "active_calibration_models": list(payload.get("active_calibration_models") or [])[:cap],
        "calibration_only_models": list(payload.get("calibration_only_models") or [])[:cap],
        "research_only_models": list(payload.get("research_only_models") or [])[:cap],
        "blocked_models": list(payload.get("blocked_models") or [])[:cap],
        "active_review_count": int(payload.get("active_review_count", 0) or 0),
        "active_calibration_count": int(payload.get("active_calibration_count", 0) or 0),
        "calibration_only_count": int(payload.get("calibration_only_count", 0) or 0),
        "research_only_count": int(payload.get("research_only_count", 0) or 0),
        "blocked_count": int(payload.get("blocked_count", 0) or 0),
        "total_labeled_outcomes": int(payload.get("total_labeled_outcomes", 0) or 0),
        "outcome_coverage_by_asset_type": dict(list(coverage.items())[:cap]),
        "feasible_now": list(payload.get("feasible_now") or [])[:cap],
        "feasible_later": list(payload.get("feasible_later") or [])[:cap],
        "research_only": list(payload.get("research_only") or [])[:cap],
        "next_required_data": list(payload.get("next_required_data") or [])[:cap],
        "safety_status": {
            "status": safety.get("status", "security_readiness"),
            "security_posture": safety.get("security_posture", "locked_read_only"),
            "provider_write_firewall": safety.get("provider_write_firewall", "locked"),
            "kill_switches_active": bool(safety.get("kill_switches_active", True)),
            "ai_execution_authority": safety.get("ai_execution_authority", "blocked"),
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "human_approval_required": True,
            "owner_approval_required": True,
        },
        "storage": _compact_storage_health(payload),
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "owner_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "actual_crypto_swaps_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
        "compact_response": True,
    }


def compact_health_response(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(payload.get("ok", True)),
        "status": "ok" if payload.get("ok", True) else "error",
        "timestamp": payload.get("checked_at") or payload.get("created_at"),
        "dry_run": bool(payload.get("dry_run", True)),
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "human_approval_required": bool(payload.get("human_approval_required", True)),
        "auto_execution_enabled": bool(payload.get("auto_execution_enabled", False)),
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
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
        "storage": _compact_storage_health(payload),
    }


def compact_strategy_readiness_response(payload: dict[str, Any], limit: int = 50) -> dict[str, Any]:
    cap = max(1, min(int(limit or 50), 100))
    strategies = []
    for row in list(payload.get("strategies") or [])[:cap]:
        if not isinstance(row, dict):
            continue
        strategies.append(
            {
                "strategy_id": row.get("strategy_id"),
                "strategy_name": row.get("strategy_name"),
                "strategy_family": row.get("strategy_family"),
                "asset_types_supported": list(row.get("asset_types_supported") or [])[:10],
                "market_types_supported": list(row.get("market_types_supported") or [])[:10],
                "maturity_status": row.get("maturity_status"),
                "enabled": bool(row.get("enabled", False)),
                "affects_review_queue": bool(row.get("affects_review_queue", False)),
                "affects_ranking": bool(row.get("affects_ranking", False)),
                "affects_execution": False,
                "minimum_sample_size": int(row.get("minimum_sample_size", 0) or 0),
                "current_sample_size": int(row.get("current_sample_size", 0) or 0),
                "outcome_coverage": float(row.get("outcome_coverage", 0.0) or 0.0),
                "calibration_status": row.get("calibration_status"),
                "performance_status": row.get("performance_status"),
                "promotion_status": row.get("promotion_status"),
                "demotion_status": row.get("demotion_status"),
                "blocked_reason": row.get("blocked_reason"),
                "safety_review_status": row.get("safety_review_status"),
                "future_execution_eligible": False,
                "provider_write": False,
                "execution_allowed": False,
                "live_execution_enabled": False,
            }
        )
    hard_gate_summary = payload.get("hard_gate_summary") if isinstance(payload.get("hard_gate_summary"), dict) else {}
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "strategy_readiness"),
        "total_strategies": int(payload.get("total_strategies", len(strategies)) or 0),
        "active_review_strategies": list(payload.get("active_review_strategies") or [])[:cap],
        "active_ranking_strategies": list(payload.get("active_ranking_strategies") or [])[:cap],
        "calibration_only_strategies": list(payload.get("calibration_only_strategies") or [])[:cap],
        "research_only_strategies": list(payload.get("research_only_strategies") or [])[:cap],
        "blocked_strategies": list(payload.get("blocked_strategies") or [])[:cap],
        "demoted_strategies": list(payload.get("demoted_strategies") or [])[:cap],
        "promoted_strategies": list(payload.get("promoted_strategies") or [])[:cap],
        "execution_eligible_future_count": int(payload.get("execution_eligible_future_count", 0) or 0),
        "currently_executable_count": 0,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "owner_approval_required": True,
        "hard_gate_status": payload.get("hard_gate_status", "locked"),
        "hard_gate_summary": {
            "status": hard_gate_summary.get("status"),
            "failed_hard_gates": list(hard_gate_summary.get("failed_hard_gates") or [])[:20],
            "required_hard_gates": list(hard_gate_summary.get("required_hard_gates") or [])[:20],
        },
        "next_required_data": list(payload.get("next_required_data") or [])[:20],
        "next_recommended_strategy_to_promote": payload.get("next_recommended_strategy_to_promote"),
        "next_recommended_strategy_to_demote": payload.get("next_recommended_strategy_to_demote"),
        "strategies": _redact(strategies),
        "raw_payload_included": False,
        "raw_payload_exposed": False,
        "secrets_included": False,
        "secrets_detected": False,
        "compact_response": True,
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
        "storage": _compact_storage_health(payload),
        "count": int(payload.get("count", len(top))),
        "items": top,
    }


def _compact_pattern_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "asset_symbol": item.get("asset_symbol"),
        "asset_type": item.get("asset_type"),
        "timeframe": item.get("timeframe"),
        "pattern_name": item.get("pattern_name"),
        "queue_status": item.get("queue_status"),
        "review_priority_score": item.get("review_priority_score"),
        "liquidity_score": item.get("liquidity_score"),
        "liquidity_tier": item.get("liquidity_tier"),
        "pattern_quality_score": item.get("pattern_quality_score"),
        "risk_reward_ratio": item.get("risk_reward_ratio"),
        "breakeven_win_rate": item.get("breakeven_win_rate"),
        "balance_sheet_risk_score": item.get("balance_sheet_risk_score"),
        "micro_calibration_score": item.get("micro_calibration_score"),
        "trade_window_calibration_score": item.get("trade_window_calibration_score"),
        "data_resolution": item.get("data_resolution"),
        "sub_5m_windows_supported": str(item.get("data_resolution") or "").lower() in {"tick", "ticks", "quote", "quotes", "sub_minute", "sub_minute_bars", "1m", "1m_candles", "minute"},
        "unsupported_windows": list(item.get("unsupported_windows") or []),
        "no_trade_reasons": list(item.get("no_trade_reasons") or [])[:10],
        "review_reasons": list(item.get("review_reasons") or [])[:10],
        "risk_warnings": list(item.get("risk_warnings") or [])[:10],
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
    }


def compact_pattern_detection_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    detections = []
    for row in list(payload.get("detections") or [])[:cap]:
        if not isinstance(row, dict):
            continue
        detections.append(
            {
                "detection_id": row.get("detection_id"),
                "asset_symbol": row.get("asset_symbol"),
                "asset_type": row.get("asset_type"),
                "timeframe": row.get("timeframe"),
                "pattern_id": row.get("pattern_id"),
                "pattern_name": row.get("pattern_name"),
                "pattern_family": row.get("pattern_family"),
                "direction": row.get("direction"),
                "detected_at": row.get("detected_at"),
                "trigger_price": row.get("trigger_price"),
                "invalidation_price": row.get("invalidation_price"),
                "target_price": row.get("target_price"),
                "pattern_quality_score": row.get("pattern_quality_score"),
                "pattern_base_priority_score": row.get("pattern_base_priority_score"),
                "volume_confirmation_score": row.get("volume_confirmation_score"),
                "breakout_confirmation_score": row.get("breakout_confirmation_score"),
                "failed_pattern_risk": row.get("failed_pattern_risk"),
                "entry_trigger_price": row.get("entry_trigger_price"),
                "stop_loss_level": row.get("stop_loss_level"),
                "reward_risk_ratio": row.get("reward_risk_ratio"),
            }
        )
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "patterns_detected"),
        "items_scanned": int(payload.get("items_scanned", 0)),
        "detections_created": int(payload.get("detections_created", len(detections))),
        "detections": detections,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
        "compact_response": True,
    }


def compact_pattern_review_queue_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    items = [_compact_pattern_item(item) for item in list(payload.get("items") or [])[:cap] if isinstance(item, dict)]
    summary = dict(payload.get("summary") or {})
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "ok"),
        "count": int(payload.get("count", len(items))),
        "total_count": int(summary.get("total_count", payload.get("count", len(items)))),
        "active_review_count": int(summary.get("active_review_count", 0)),
        "watchlist_review_count": int(summary.get("watchlist_review_count", 0)),
        "low_priority_review_count": int(summary.get("low_priority_review_count", 0)),
        "no_review_count": int(summary.get("no_review_count", 0)),
        "no_trade_count": int(summary.get("no_trade_count", 0)),
        "data_insufficient_count": int(summary.get("data_insufficient_count", 0)),
        "status_counts": dict(summary.get("status_counts") or {}),
        "pattern_counts": dict(summary.get("pattern_counts") or {}),
        "liquidity_tier_counts": dict(summary.get("liquidity_tier_counts") or {}),
        "items": items,
        "storage_backend": payload.get("storage_backend", "file"),
        "last_updated_at": payload.get("last_updated_at"),
        "latest_run_id": payload.get("latest_run_id"),
        "queue_read_ok": bool(payload.get("queue_read_ok", True)),
        "queue_error_category": payload.get("queue_error_category"),
        "storage": _compact_storage_health(payload),
        "provider_write": False,
        "execution_allowed": False,
        "execution_allowed_count": 0,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "broker_order_execution_enabled": False,
        "crypto_trade_execution_enabled": False,
        "stock_trade_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
        "compact_response": True,
    }


def compact_small_account_review_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    items = [_compact_pattern_item(item) for item in list(payload.get("items") or [])[:cap] if isinstance(item, dict)]
    analyst = payload.get("local_analyst_review") if isinstance(payload.get("local_analyst_review"), dict) else {}
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "review_candidates_created"),
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "items_scanned": int(payload.get("items_scanned", 0)),
        "detections_created": int(payload.get("detections_created", 0)),
        "review_queue_count": int(payload.get("review_queue_count", len(items))),
        "active_review_count": int(payload.get("active_review_count", 0)),
        "watchlist_review_count": int(payload.get("watchlist_review_count", 0)),
        "no_review_count": int(payload.get("no_review_count", 0)),
        "sample_items": items,
        "local_analyst_review": {
            "status": analyst.get("status"),
            "enabled": bool(analyst.get("enabled", False)),
            "external_model_called": False,
            "recommended_action": analyst.get("recommended_action"),
            "must_not_execute": True,
            "reviewer_side_effects": "none",
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "auto_execution": False,
            "auto_execution_enabled": False,
            "human_approval_required": True,
            "actual_orders_submitted": 0,
            "actual_bets_submitted": 0,
            "actual_trades_submitted": 0,
        },
        "persisted": bool(payload.get("persisted", False)),
        "storage_backend": payload.get("storage_backend"),
        "queue_write_path": payload.get("queue_write_path"),
        "broker_order_execution_enabled": False,
        "crypto_trade_execution_enabled": False,
        "stock_trade_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
        "compact_response": True,
    }


def compact_pattern_calibration_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    segments = dict(payload.get("segments") or {})
    segment_rows = []
    for key, value in list(segments.items())[:cap]:
        row = dict(value or {})
        row["segment_key"] = key
        segment_rows.append(row)
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "insufficient_data"),
        "created_at": payload.get("created_at"),
        "record_count": int(payload.get("record_count", 0)),
        "settled_count": int(payload.get("settled_count", 0)),
        "sample_size": int(payload.get("sample_size", 0)),
        "insufficient_sample": bool(payload.get("insufficient_sample", True)),
        "performance_metrics": dict(payload.get("performance_metrics") or {}),
        "segments": segment_rows,
        "next_required_data": list(payload.get("next_required_data") or [])[:10],
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
        "compact_response": True,
    }


def compact_micro_outcome_calibration_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    records = []
    for row in list(payload.get("records") or [])[:cap]:
        if not isinstance(row, dict):
            continue
        records.append(
            {
                "detection_id": row.get("detection_id"),
                "asset_symbol": row.get("asset_symbol"),
                "pattern_id": row.get("pattern_id"),
                "outcome_window": row.get("outcome_window"),
                "data_resolution": row.get("data_resolution"),
                "outcome_status": row.get("outcome_status"),
                "final_outcome": row.get("final_outcome"),
                "requested_window_seconds": row.get("requested_window_seconds"),
                "effective_window_seconds": row.get("effective_window_seconds"),
                "delayed_by_seconds": row.get("delayed_by_seconds"),
                "delay_source": row.get("delay_source"),
                "usable_for_calibration": bool(row.get("usable_for_calibration", False)),
                "price_at_window": row.get("price_at_window"),
                "max_favorable_excursion": row.get("max_favorable_excursion"),
                "max_adverse_excursion": row.get("max_adverse_excursion"),
                "data_resolution_insufficient": bool(row.get("data_resolution_insufficient", False)),
            }
        )
    segments = dict(payload.get("segments") or {})
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "insufficient_data"),
        "created_at": payload.get("created_at"),
        "detection_id": payload.get("detection_id"),
        "data_resolution": payload.get("data_resolution"),
        "record_count": int(payload.get("record_count", len(records))),
        "settled_count": int(payload.get("settled_count", 0)),
        "sample_size": int(payload.get("sample_size", 0)),
        "insufficient_sample": bool(payload.get("insufficient_sample", True)),
        "status_counts": dict(payload.get("status_counts") or {}),
        "unsupported_windows": list(payload.get("unsupported_windows") or [])[:10],
        "records": records,
        "segments": dict(list(segments.items())[:cap]),
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
        "compact_response": True,
    }


def compact_broker_quality_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    brokers = []
    for row in list(payload.get("brokers") or [])[:cap]:
        if not isinstance(row, dict):
            continue
        brokers.append(
            {
                "broker_name": row.get("broker_name"),
                "provider_type": row.get("provider_type"),
                "asset_types_supported": list(row.get("asset_types_supported") or [])[:10],
                "broker_quality_score": row.get("broker_quality_score"),
                "broker_status": row.get("broker_status"),
                "paper_or_sandbox_support": bool(row.get("paper_or_sandbox_support", False)),
                "execution_restriction_risk": row.get("execution_restriction_risk"),
                "compliance_risk_score": row.get("compliance_risk_score"),
                "source_access_type": row.get("source_access_type"),
                "current_phase_allowed": bool(row.get("current_phase_allowed", False)),
                "future_paid_candidate": bool(row.get("future_paid_candidate", False)),
                "requires_budget_approval": bool(row.get("requires_budget_approval", False)),
                "approval_status": row.get("approval_status"),
                "enabled": False,
            }
        )
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "ok"),
        "broker_count": int(payload.get("broker_count", len(brokers))),
        "status_counts": dict(payload.get("status_counts") or {}),
        "brokers": brokers,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
        "compact_response": True,
    }


def compact_balance_sheet_risk_response(payload: dict[str, Any]) -> dict[str, Any]:
    risk = dict(payload.get("balance_sheet_risk") or {})
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "DATA_INSUFFICIENT"),
        "symbol": payload.get("symbol"),
        "source": payload.get("source"),
        "data_insufficient": bool(risk.get("data_insufficient", True)),
        "current_ratio": risk.get("current_ratio"),
        "quick_ratio": risk.get("quick_ratio"),
        "debt_to_equity": risk.get("debt_to_equity"),
        "cash_to_debt": risk.get("cash_to_debt"),
        "cash_runway_score": risk.get("cash_runway_score"),
        "dilution_risk_score": risk.get("dilution_risk_score"),
        "offering_risk_score": risk.get("offering_risk_score"),
        "goodwill_risk_score": risk.get("goodwill_risk_score"),
        "preferred_stock_risk_score": risk.get("preferred_stock_risk_score"),
        "balance_sheet_quality_score": risk.get("balance_sheet_quality_score"),
        "fundamental_risk_score": risk.get("fundamental_risk_score"),
        "balance_sheet_risk_bucket": risk.get("balance_sheet_risk_bucket"),
        "risk_blockers": list(risk.get("risk_blockers") or [])[:10],
        "risk_warnings": list(risk.get("risk_warnings") or [])[:10],
        "force_status": risk.get("force_status"),
        "storage": _compact_storage_health(payload),
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "raw_payload_included": False,
        "secrets_included": False,
        "compact_response": True,
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
        "unmatched_reason_counts": dict(payload.get("unmatched_reason_counts", {})),
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
        "storage": _compact_storage_health(payload),
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
        "storage": _compact_storage_health(payload),
        "latest_batch_id": payload.get("latest_batch_id"),
        "last_updated_at": payload.get("last_updated_at"),
        "outcome_write_path": payload.get("outcome_write_path"),
    }


def compact_outcome_import_response(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "outcomes_import_validated"),
        "dry_run": bool(payload.get("dry_run", True)),
        "persist": bool(payload.get("persist", False)),
        "records_received": int(payload.get("records_received", 0)),
        "records_valid": int(payload.get("records_valid", 0)),
        "records_rejected": int(payload.get("records_rejected", 0)),
        "rejected_reason_counts": dict(payload.get("rejected_reason_counts", {})),
        "duplicate_count": int(payload.get("duplicate_count", 0)),
        "would_insert_count": int(payload.get("would_insert_count", 0)),
        "inserted_count": int(payload.get("inserted_count", 0)),
        "matched_paper_decision_count": int(payload.get("matched_paper_decision_count", 0)),
        "unmatched_count": int(payload.get("unmatched_count", 0)),
        "render_existing_outcomes_count": int(payload.get("render_existing_outcomes_count", 0)),
        "render_outcomes_after_import_if_persisted": int(payload.get("render_outcomes_after_import_if_persisted", 0)),
        "render_outcomes_after_import": int(payload.get("render_outcomes_after_import", payload.get("render_outcomes_after_import_if_persisted", 0))),
        "projected_render_outcome_count": int(payload.get("projected_render_outcome_count", payload.get("render_outcomes_after_import_if_persisted", 0))),
        "projected_matched_outcomes_count": int(payload.get("projected_matched_outcomes_count", 0)),
        "projected_unmatched_outcomes_count": int(payload.get("projected_unmatched_outcomes_count", 0)),
        "matched_outcomes_after_import": int(payload.get("matched_outcomes_after_import", payload.get("projected_matched_outcomes_count", 0))),
        "unmatched_outcomes_after_import": int(payload.get("unmatched_outcomes_after_import", payload.get("projected_unmatched_outcomes_count", 0))),
        "migration_version": payload.get("migration_version"),
        "audit_report_path": payload.get("audit_report_path"),
        "persistence_blocked_reason": payload.get("persistence_blocked_reason"),
        "persistence_error_category": payload.get("persistence_error_category"),
        "persistence_error": payload.get("persistence_error"),
        "supporting_paper_decisions_received": int(payload.get("supporting_paper_decisions_received", 0)),
        "supporting_paper_decisions_valid": int(payload.get("supporting_paper_decisions_valid", 0)),
        "supporting_paper_decisions_written": int(payload.get("supporting_paper_decisions_written", 0)),
        "paper_ledger_items_path": payload.get("paper_ledger_items_path"),
        "storage_backend": payload.get("storage_backend", "file"),
        "storage": _compact_storage_health(payload),
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
        "storage": _compact_storage_health(payload),
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
        "exploration_sample",
        "exploration_reason",
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
        "daily_new_contract_target": int(payload.get("daily_new_contract_target", payload.get("daily_new_contract_limit", 0))),
        "daily_new_contract_hard_cap": int(payload.get("daily_new_contract_hard_cap", 0)),
        "daily_new_contract_limit": int(payload.get("daily_new_contract_limit", 0)),
        "daily_new_contracts_remaining": int(payload.get("daily_new_contracts_remaining", 0)),
        "daily_remaining_capacity": int(payload.get("daily_remaining_capacity", payload.get("daily_new_contracts_remaining", 0))),
        "effective_max_new_contracts": int(payload.get("effective_max_new_contracts", 0)),
        "adaptive_throttle_enabled": bool(payload.get("adaptive_throttle_enabled", False)),
        "adaptive_throttle_reasons": list(payload.get("adaptive_throttle_reasons", []))[:10],
        "duplicate_contracts_skipped": int(payload.get("duplicate_contracts_skipped", 0)),
        "duplicate_skipped_count": int(payload.get("duplicate_skipped_count", payload.get("duplicate_contracts_skipped", 0))),
        "duplicate_outcomes_skipped": int(payload.get("duplicate_outcomes_skipped", 0)),
        "records_checked": int(payload.get("records_checked", 0)),
        "records_rechecked_today": int(payload.get("records_rechecked_today", payload.get("records_checked", 0))),
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
        "outcomes_persisted_today": int(payload.get("outcomes_persisted_today", payload.get("outcomes_persisted", 0))),
        "total_outcome_records_count": int(payload.get("total_outcome_records_count", 0)),
        "matched_outcomes_count": int(payload.get("matched_outcomes_count", 0)),
        "progress_to_100": dict(payload.get("progress_to_100", {})),
        "progress_to_300": dict(payload.get("progress_to_300", {})),
        "progress_to_1000": dict(payload.get("progress_to_1000", {})),
        "calibration_status": payload.get("calibration_status"),
        "coverage_rate": float(payload.get("coverage_rate", 0.0)),
        "insufficient_sample": bool(payload.get("insufficient_sample", False)),
        "next_required_data": list(payload.get("next_required_data", []))[:10],
        "deepseek_review_status": payload.get("deepseek_review_status", "not_requested"),
        "watchlist_size": int(payload.get("watchlist_size", 0)),
        "unresolved_open": int(payload.get("unresolved_open", 0)),
        "closed_unknown": int(payload.get("closed_unknown", 0)),
        "stale_unknown": int(payload.get("stale_unknown", 0)),
        "recheck_due_now": int(payload.get("recheck_due_now", 0)),
        "next_suggested_recheck_time": payload.get("next_suggested_recheck_time"),
        "average_liquidity_score": float(payload.get("average_liquidity_score", 0.0)),
        "average_pricing_quality_score": float(payload.get("average_pricing_quality_score", 0.0)),
        "liquidity_tier_counts": dict(payload.get("liquidity_tier_counts", {})),
        "exploration_sample_count": int(payload.get("exploration_sample_count", 0)),
        "quality_gate_rejection_count": int(payload.get("quality_gate_rejection_count", 0)),
        "storage_backend": payload.get("storage_backend"),
        "storage": _compact_storage_health(payload),
        "persistence_warning_if_ephemeral": payload.get("persistence_warning_if_ephemeral"),
        "errors": list(payload.get("errors", []))[:10],
        "provider_write": False,
        "execution_allowed_count": 0,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "live_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
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


def _compact_deepseek_candidate_review(review: dict[str, Any]) -> dict[str, Any]:
    return {
        "deepseek_status": review.get("deepseek_status"),
        "candidate_id": review.get("candidate_id"),
        "asset_type": review.get("asset_type"),
        "market_type": review.get("market_type"),
        "recommended_action": review.get("recommended_action"),
        "confidence_score": float(review.get("confidence_score", 0.0) or 0.0),
        "edge_quality_score": float(review.get("edge_quality_score", 0.0) or 0.0),
        "liquidity_risk_score": float(review.get("liquidity_risk_score", 0.0) or 0.0),
        "trap_risk_score": float(review.get("trap_risk_score", 0.0) or 0.0),
        "calibration_support_score": float(review.get("calibration_support_score", 0.0) or 0.0),
        "out_of_distribution_risk": float(review.get("out_of_distribution_risk", 0.0) or 0.0),
        "agreement_with_core_model": bool(review.get("agreement_with_core_model", False)),
        "disagreement_reasons": list(review.get("disagreement_reasons") or [])[:25],
        "missing_inputs": list(review.get("missing_inputs") or [])[:25],
        "review_reasons": list(review.get("review_reasons") or [])[:25],
        "no_bet_reasons": list(review.get("no_bet_reasons") or [])[:25],
        "no_trade_reasons": list(review.get("no_trade_reasons") or [])[:25],
        "next_data_to_collect": list(review.get("next_data_to_collect") or [])[:25],
        "red_team_only": True,
        "deepseek_used": bool(review.get("deepseek_used", False)),
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "human_approval_required": True,
        "owner_approval_required": True,
    }


def _compact_deepseek_disagreement(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "disagreement_id": record.get("disagreement_id"),
        "candidate_id": record.get("candidate_id"),
        "asset_type": record.get("asset_type"),
        "market_type": record.get("market_type"),
        "provider": record.get("provider"),
        "core_model_action": record.get("core_model_action"),
        "deepseek_action": record.get("deepseek_action"),
        "disagreement_type": record.get("disagreement_type"),
        "disagreement_reasons": list(record.get("disagreement_reasons") or [])[:25],
        "calibration_bucket": record.get("calibration_bucket"),
        "manifold_cluster_id": record.get("manifold_cluster_id"),
        "strategy_ids": list(record.get("strategy_ids") or [])[:25],
        "created_at": record.get("created_at"),
        "redacted": True,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
    }


def _compact_deepseek_daily_report(report: dict[str, Any]) -> dict[str, Any]:
    safety = dict(report.get("safety_status") or {})
    safety.update(
        {
            "red_team_only": True,
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "auto_execution": False,
            "human_approval_required": True,
            "owner_approval_required": True,
        }
    )
    return {
        "report_id": report.get("report_id"),
        "date": report.get("date"),
        "strongest_review_candidates": list(report.get("strongest_review_candidates") or [])[:10],
        "strongest_no_bet_no_trade_traps": list(report.get("strongest_no_bet_no_trade_traps") or [])[:10],
        "calibration_improvements": list(report.get("calibration_improvements") or [])[:25],
        "failing_clusters": list(report.get("failing_clusters") or [])[:10],
        "missing_data": list(report.get("missing_data") or [])[:25],
        "provider_issues": list(report.get("provider_issues") or [])[:25],
        "disagreement_count": int(report.get("disagreement_count", 0) or 0),
        "repeated_model_mistakes": list(report.get("repeated_model_mistakes") or [])[:25],
        "recommended_next_data_to_collect": list(report.get("recommended_next_data_to_collect") or [])[:25],
        "recommended_next_codex_task": report.get("recommended_next_codex_task"),
        "safety_status": safety,
        "red_team_only": True,
        "deepseek_used": bool(report.get("deepseek_used", False)),
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "human_approval_required": True,
        "owner_approval_required": True,
    }


def _compact_deepseek_profit_lab_response(payload: dict[str, Any]) -> dict[str, Any]:
    review = payload.get("candidate_review") or payload.get("review") or {}
    reviews = payload.get("reviews") if isinstance(payload.get("reviews"), list) else None
    report = payload.get("report") if isinstance(payload.get("report"), dict) else None
    disagreement = payload.get("disagreement") if isinstance(payload.get("disagreement"), dict) else None
    out = {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "disabled"),
        "enabled": bool(payload.get("enabled", False)),
        "deepseek_used": bool(payload.get("deepseek_used", False)),
        "red_team_only": True,
        "local_server_reachable": bool(payload.get("local_server_reachable", False)),
        "json_schema_valid": bool(payload.get("json_schema_valid", False)),
        "rejected_reason": payload.get("rejected_reason"),
        "forbidden_actions_rejected": bool(payload.get("forbidden_actions_rejected", False)),
        "reviewer_side_effects": "none",
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "owner_approval_required": True,
        "raw_payload_included": False,
        "secrets_included": False,
        "compact_response": True,
    }
    if isinstance(review, dict) and "candidate_id" in review:
        out["review"] = _compact_deepseek_candidate_review(review)
    if reviews is not None:
        out["reviews"] = [_compact_deepseek_candidate_review(row) for row in reviews if isinstance(row, dict)][:10]
        out["review_count"] = int(payload.get("review_count", len(out["reviews"])))
        out["disagreements_recorded"] = int(payload.get("disagreements_recorded", 0) or 0)
    if report is not None:
        out["report"] = _compact_deepseek_daily_report(report)
    if disagreement is not None:
        record = disagreement.get("record") if isinstance(disagreement.get("record"), dict) else disagreement
        out["disagreement"] = _compact_deepseek_disagreement(record)
    if isinstance(payload.get("items"), list):
        out["count"] = int(payload.get("count", len(payload["items"])))
        out["items"] = [_compact_deepseek_disagreement(row) for row in payload["items"] if isinstance(row, dict)][:100]
    return out


def compact_deepseek_review_response(payload: dict[str, Any]) -> dict[str, Any]:
    if (
        "candidate_review" in payload
        or "reviews" in payload
        or "report" in payload
        or "deepseek_used" in payload
        or "red_team_only" in payload
        or "items" in payload and str(payload.get("schema_version", "")).endswith("deepseek_profit_lab.disagreement_queue.v1")
    ):
        return _compact_deepseek_profit_lab_response(payload)
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
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "human_approval_required": True,
        "owner_approval_required": True,
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


def compact_institutional_lab_health_response(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "ok"),
        "sidecar_status": payload.get("sidecar_status", "ready"),
        "latest_run_id": payload.get("latest_run_id"),
        "latest_status": payload.get("latest_status"),
        "audit_records_count": int(payload.get("audit_records_count", 0)),
        "lock_present": bool(payload.get("lock_present", False)),
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "auto_bet_enabled": False,
        "auto_trade_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "human_approval_required": True,
        "paper_only": True,
        "review_only": True,
        "simulation_only": True,
        "storage_backend": payload.get("storage_backend", "file"),
        "storage": _compact_storage_health(payload),
        "raw_payload_included": False,
    }


def compact_institutional_lab_run_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    records = list(payload.get("records", []))[: max(1, min(int(limit or 10), 10))]
    compact_records = []
    for row in records:
        compact_records.append(
            {
                "sidecar_id": row.get("sidecar_id"),
                "source_record_id": row.get("source_record_id"),
                "asset_class": row.get("asset_class"),
                "provider": row.get("provider"),
                "market_type": row.get("market_type"),
                "symbol_or_ticker": row.get("symbol_or_ticker"),
                "contract_id": row.get("contract_id"),
                "selection": row.get("selection"),
                "observed_at": row.get("observed_at"),
                "observed_price": row.get("observed_price"),
                "bid": row.get("bid"),
                "ask": row.get("ask"),
                "implied_probability": row.get("implied_probability"),
                "liquidity_score": row.get("liquidity_score"),
                "pricing_quality_score": row.get("pricing_quality_score"),
                "valuation_score": row.get("valuation_score"),
                "risk_score": row.get("risk_score"),
                "confidence_score": row.get("confidence_score"),
                "review_priority_score": row.get("review_priority_score"),
                "quality_tier": row.get("quality_tier"),
                "liquidity_tier": row.get("liquidity_tier"),
                "risk_tier": row.get("risk_tier"),
                "outcome_status": row.get("outcome_status"),
                "final_outcome": row.get("final_outcome"),
                "paper_only": True,
                "review_only": True,
                "simulation_only": True,
                "execution_allowed": False,
                "reason_codes": list(row.get("reason_codes", []))[:10],
                "missing_fields": list(row.get("missing_fields", []))[:10],
            }
        )
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "completed"),
        "run_id": payload.get("run_id"),
        "created_at": payload.get("created_at"),
        "dry_run": True,
        "read_existing_outputs_only": True,
        "lock_acquired": bool(payload.get("lock_acquired", False)),
        "skipped_due_to_lock": bool(payload.get("skipped_due_to_lock", False)),
        "records_read": int(payload.get("records_read", 0)),
        "records_normalized": int(payload.get("records_normalized", 0)),
        "records_with_outcomes": int(payload.get("records_with_outcomes", 0)),
        "outcome_records_count": int(payload.get("outcome_records_count", 0)),
        "matched_outcomes_count": int(payload.get("matched_outcomes_count", 0)),
        "duplicate_records_skipped": int(payload.get("duplicate_records_skipped", 0)),
        "duplicate_outcomes_skipped": int(payload.get("duplicate_outcomes_skipped", 0)),
        "duplicate_simulations_skipped": int(payload.get("duplicate_simulations_skipped", 0)),
        "source_counts": dict(payload.get("source_counts", {})),
        "unavailable": dict(payload.get("unavailable", {})),
        "status_by_asset_class": dict(payload.get("status_by_asset_class", {})),
        "calibration_status": (payload.get("calibration") or {}).get("status"),
        "next_required_data": list((payload.get("calibration") or {}).get("next_required_data", []))[:10],
        "risk_summary": dict(payload.get("risk_summary", {})),
        "deepseek_review_status": (payload.get("deepseek_review") or {}).get("status", "disabled"),
        "execution_desk_status": (payload.get("execution_simulation") or {}).get("execution_desk_status", "simulation_only"),
        "simulated_tickets_created": int(bool((payload.get("execution_simulation") or {}).get("simulated_ticket_created", False))),
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "auto_bet_enabled": False,
        "auto_trade_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "human_approval_required": True,
        "paper_only": True,
        "review_only": True,
        "simulation_only": True,
        "latest_path": payload.get("latest_path"),
        "item_path": payload.get("item_path"),
        "report_path": payload.get("report_path"),
        "daily_report_path": payload.get("daily_report_path"),
        "daily_markdown_path": payload.get("daily_markdown_path"),
        "audit_id": payload.get("audit_id"),
        "count": len(compact_records),
        "records": compact_records,
        "compact_response": True,
        "raw_payload_included": False,
    }


def compact_institutional_execution_response(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "simulated"),
        "execution_desk_status": "simulation_only",
        "run_id": payload.get("run_id"),
        "asset_class": payload.get("asset_class"),
        "provider": payload.get("provider"),
        "candidate_id": payload.get("candidate_id"),
        "pre_trade_checks_passed": False,
        "risk_blocks": list(payload.get("risk_blocks", []))[:25],
        "warnings": list(payload.get("warnings", []))[:25],
        "risk_score": payload.get("risk_score"),
        "risk_tier": payload.get("risk_tier"),
        "theoretical_size": payload.get("theoretical_size"),
        "simulated_ticket_created": bool(payload.get("simulated_ticket_created", False)),
        "actual_order_submitted": False,
        "actual_bet_submitted": False,
        "actual_trade_submitted": False,
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "human_command_required": True,
        "requires_human_command": True,
        "audit_id": payload.get("audit_id"),
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "kalshi_order_execution_enabled": False,
        "sportsbook_bet_execution_enabled": False,
        "broker_order_execution_enabled": False,
        "simulation_only": True,
        "raw_payload_included": False,
    }


def compact_institutional_report_response(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "completed"),
        "run_id": payload.get("run_id"),
        "date": payload.get("date"),
        "records_read": int(payload.get("records_read", 0)),
        "records_normalized": int(payload.get("records_normalized", 0)),
        "records_with_outcomes": int(payload.get("records_with_outcomes", 0)),
        "prediction_market_status": payload.get("prediction_market_status") or (payload.get("status_by_asset_class") or {}).get("prediction_market"),
        "stock_status": payload.get("stock_status") or (payload.get("status_by_asset_class") or {}).get("stock"),
        "bond_major_asset_status": payload.get("bond_major_asset_status"),
        "sportsbook_status": payload.get("sportsbook_status") or (payload.get("status_by_asset_class") or {}).get("sportsbook"),
        "calibration_status_by_asset_class": dict(payload.get("calibration_status_by_asset_class", payload.get("status_by_asset_class", {}))),
        "matched_outcomes_by_asset_class": dict(payload.get("matched_outcomes_by_asset_class", {})),
        "insufficient_sample_by_asset_class": dict(payload.get("insufficient_sample_by_asset_class", {})),
        "next_required_data": list(payload.get("next_required_data", []))[:25],
        "execution_desk_status": payload.get("execution_desk_status", "simulation_only"),
        "simulated_tickets_created": int(payload.get("simulated_tickets_created", 0)),
        "actual_orders_submitted": 0,
        "actual_bets_submitted": 0,
        "actual_trades_submitted": 0,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution_enabled": False,
        "deepseek_review_status": payload.get("deepseek_review_status", (payload.get("deepseek_review") or {}).get("status", "disabled")),
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


def _compact_data_source_lane(lane: dict[str, Any]) -> dict[str, Any]:
    return {
        "lane_id": lane.get("lane_id"),
        "module": lane.get("module"),
        "module_lane": lane.get("module_lane"),
        "module_priority": lane.get("module_priority"),
        "module_status": lane.get("module_status"),
        "enabled": bool(lane.get("enabled", False)),
        "sport_or_asset": lane.get("sport_or_asset"),
        "category": lane.get("category"),
        "lane_status": lane.get("lane_status"),
        "assigned_research_lane": bool(lane.get("assigned_research_lane", True)),
        "source_candidate_count": len(lane.get("source_candidates") or []),
        "verified_source_count": len(lane.get("verified_sources") or []),
        "future_source_candidate_count": len(lane.get("future_source_candidates") or []),
        "rejected_source_count": len(lane.get("rejected_sources") or []),
        "required_model_inputs": list(lane.get("required_model_inputs") or [])[:20],
        "outcome_fields_required": list(lane.get("outcome_fields_required") or [])[:20],
        "historical_backfill_fields_required": list(lane.get("historical_backfill_fields_required") or [])[:20],
        "adapter_status": lane.get("adapter_status"),
        "planned_inputs": list(lane.get("planned_inputs") or [])[:30],
        "planned_scores": list(lane.get("planned_scores") or [])[:40],
        "safety_requirements": list(lane.get("safety_requirements") or [])[:30],
        "forbidden_actions": list(lane.get("forbidden_actions") or [])[:30],
        "strategy_language": list(lane.get("strategy_language") or [])[:10],
        "coverage_score": int(lane.get("coverage_score") or 0),
        "freshness_score": int(lane.get("freshness_score") or 0),
        "outcome_availability_score": int(lane.get("outcome_availability_score") or 0),
        "terms_risk_score": int(lane.get("terms_risk_score") or 0),
        "external_research_priority_score": int(lane.get("external_research_priority_score") or 0),
        "needs_external_research": lane.get("lane_status") in {"needs_external_research", "candidate_sources_available", "future_vendor_needed", "blocked_pending_source"},
    }


def _compact_data_source_source(source: dict[str, Any]) -> dict[str, Any]:
    quality = dict(source.get("quality") or {})
    return {
        "source_id": source.get("source_id"),
        "source_name": source.get("source_name"),
        "display_name": source.get("display_name", source.get("source_name")),
        "lane_id": source.get("lane_id"),
        "module_lane": source.get("module_lane", source.get("lane_id")),
        "module": source.get("module"),
        "source_category": source.get("source_category"),
        "source_access_type": source.get("source_access_type"),
        "auth_type": source.get("auth_type"),
        "env_var_name": source.get("env_var_name"),
        "env_var_names": list(source.get("env_var_names") or [])[:10],
        "https_supported": source.get("https_supported"),
        "cors_status": source.get("cors_status"),
        "current_phase_allowed": bool(source.get("current_phase_allowed", False)),
        "future_source_candidate": bool(source.get("future_source_candidate", False)),
        "requires_budget_approval": bool(source.get("requires_budget_approval", False)),
        "verification_phase_allowed": bool(source.get("verification_phase_allowed", False)),
        "call_budget_level": source.get("call_budget_level"),
        "max_provider_calls_default": int(source.get("max_provider_calls_default", 0) or 0),
        "max_provider_calls_hard_cap": int(source.get("max_provider_calls_hard_cap", 0) or 0),
        "paid_upgrade_required": bool(source.get("paid_upgrade_required", False)),
        "paid_upgrade_allowed": False,
        "substantial_usage_allowed": False,
        "requires_account": bool(source.get("requires_account", False)),
        "requires_api_key": bool(source.get("requires_api_key", False)),
        "requires_oauth": bool(source.get("requires_oauth", False)),
        "requires_terms_review": bool(source.get("requires_terms_review", True)),
        "requires_provider_write": bool(source.get("requires_provider_write", False)),
        "requires_execution_account": bool(source.get("requires_execution_account", False)),
        "requires_brokerage_account": bool(source.get("requires_brokerage_account", False)),
        "requires_sportsbook_account": bool(source.get("requires_sportsbook_account", False)),
        "requires_paid_subscription": bool(source.get("requires_paid_subscription", False)),
        "trial_only": bool(source.get("trial_only", False)),
        "credit_card_required": bool(source.get("credit_card_required", False)),
        "approval_status": source.get("approval_status"),
        "enabled": bool(source.get("enabled", False)),
        "provider_write": False,
        "execution_allowed": False,
        "adapter_status": source.get("adapter_status"),
        "adapter_scope": source.get("adapter_scope"),
        "raw_payload_persistence_allowed": bool(source.get("raw_payload_persistence_allowed", False)),
        "forbidden_actions": list(source.get("forbidden_actions") or [])[:30],
        "supported_use_cases": list(source.get("supported_use_cases") or [])[:30],
        "model_input_mapping_status": source.get("model_input_mapping_status"),
        "outcome_mapping_status": source.get("outcome_mapping_status"),
        "backfill_mapping_status": source.get("backfill_mapping_status"),
        "public_reference_url": source.get("public_reference_url"),
        "module_priority": source.get("module_priority"),
        "module_status": source.get("module_status"),
        "scoring_dimensions": list(source.get("scoring_dimensions") or [])[:40],
        "coverage": dict(source.get("coverage") or {}),
        "freshness": dict(source.get("freshness") or {}),
        "limits": dict(source.get("limits") or {}),
        "legal_terms": dict(source.get("legal_terms") or {}),
        "model_mapping": {
            "supported_model_modules": list((source.get("model_mapping") or {}).get("supported_model_modules") or [])[:20],
            "model_inputs_supported": list((source.get("model_mapping") or {}).get("model_inputs_supported") or [])[:30],
            "missing_model_inputs": list((source.get("model_mapping") or {}).get("missing_model_inputs") or [])[:30],
            "join_keys": list((source.get("model_mapping") or {}).get("join_keys") or [])[:20],
            "outcome_fields_available": list((source.get("model_mapping") or {}).get("outcome_fields_available") or [])[:20],
            "historical_backfill_fields_available": list((source.get("model_mapping") or {}).get("historical_backfill_fields_available") or [])[:20],
        },
        "quality": {
            "source_reliability_score": quality.get("source_reliability_score"),
            "freshness_score": quality.get("freshness_score"),
            "coverage_score": quality.get("coverage_score"),
            "completeness_score": quality.get("completeness_score"),
            "join_quality_score": quality.get("join_quality_score"),
            "model_input_fill_rate": quality.get("model_input_fill_rate"),
            "terms_risk_score": quality.get("terms_risk_score"),
            "rate_limit_risk_score": quality.get("rate_limit_risk_score"),
            "historical_depth_score": quality.get("historical_depth_score"),
            "outcome_availability_score": quality.get("outcome_availability_score"),
            "external_research_priority_score": quality.get("external_research_priority_score"),
            "current_phase_usability_score": quality.get("current_phase_usability_score"),
            "future_value_score": quality.get("future_value_score"),
            "adapter_complexity_score": quality.get("adapter_complexity_score"),
            "calibration_value_score": quality.get("calibration_value_score"),
            "stock_signal_value_score": quality.get("stock_signal_value_score"),
            "fundamental_depth_score": quality.get("fundamental_depth_score"),
            "valuation_coverage_score": quality.get("valuation_coverage_score"),
            "earnings_event_score": quality.get("earnings_event_score"),
            "SEC_mapping_score": quality.get("SEC_mapping_score"),
            "liquidity_market_depth_score": quality.get("liquidity_market_depth_score"),
            "crypto_signal_value_score": quality.get("crypto_signal_value_score"),
            "exchange_depth_score": quality.get("exchange_depth_score"),
            "onchain_depth_score": quality.get("onchain_depth_score"),
            "order_book_depth_score": quality.get("order_book_depth_score"),
            "funding_open_interest_score": quality.get("funding_open_interest_score"),
            "dex_liquidity_score": quality.get("dex_liquidity_score"),
            "stablecoin_flow_score": quality.get("stablecoin_flow_score"),
            "quality_tier": quality.get("quality_tier"),
        },
        "verified_at": source.get("verified_at"),
        "verified_by": source.get("verified_by"),
        "raw_payload_included": False,
        "secrets_included": False,
    }


def compact_data_source_registry_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    lanes = list(payload.get("lanes") or [])
    sources = list(payload.get("sources") or [])
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "ok"),
        "schema_version": payload.get("schema_version"),
        "created_at": payload.get("created_at"),
        "module_filter": payload.get("module_filter"),
        "total_lanes": int(payload.get("total_lanes", len(lanes))),
        "lanes_with_verified_sources": int(payload.get("lanes_with_verified_sources", 0)),
        "lanes_with_candidate_sources": int(payload.get("lanes_with_candidate_sources", 0)),
        "lanes_needing_external_research": int(payload.get("lanes_needing_external_research", 0)),
        "lanes_blocked_pending_source": int(payload.get("lanes_blocked_pending_source", 0)),
        "lanes_future_vendor_needed": int(payload.get("lanes_future_vendor_needed", 0)),
        "total_sources": int(payload.get("total_sources", len(sources))),
        "enabled_source_count": int(payload.get("enabled_source_count", 0)),
        "source_counts_by_lane": dict(payload.get("source_counts_by_lane") or {}),
        "source_counts_by_category": dict(payload.get("source_counts_by_category") or {}),
        "key_required_source_count": int(payload.get("key_required_source_count", 0)),
        "oauth_required_source_count": int(payload.get("oauth_required_source_count", 0)),
        "no_auth_source_count": int(payload.get("no_auth_source_count", 0)),
        "trading_capable_disabled_count": int(payload.get("trading_capable_disabled_count", 0)),
        "provider_write_enabled_count": int(payload.get("provider_write_enabled_count", 0)),
        "env_var_names": list(payload.get("env_var_names") or [])[:cap],
        "current_phase_allowed_count": int(payload.get("current_phase_allowed_count", 0)),
        "candidate_count": int(payload.get("candidate_count", 0)),
        "needs_terms_review_count": int(payload.get("needs_terms_review_count", 0)),
        "future_source_candidate_count": int(payload.get("future_source_candidate_count", 0)),
        "rejected_count": int(payload.get("rejected_count", 0)),
        "modules_fully_covered": list(payload.get("modules_fully_covered") or [])[:cap],
        "modules_partially_covered": list(payload.get("modules_partially_covered") or [])[:cap],
        "modules_without_verified_source": list(payload.get("modules_without_verified_source") or [])[:cap],
        "top_missing_fields_by_module": dict(list(dict(payload.get("top_missing_fields_by_module") or {}).items())[:cap]),
        "open_external_research_tasks": int(payload.get("open_external_research_tasks", 0)),
        "recommended_next_adapters": list(payload.get("recommended_next_adapters") or [])[:cap],
        "lanes": [_compact_data_source_lane(lane) for lane in lanes[:cap]],
        "sources": [_compact_data_source_source(source) for source in sources[:cap]],
        "storage": _compact_storage_health(payload),
        "latest_path": payload.get("latest_path"),
        "item_path": payload.get("item_path"),
        "report_path": payload.get("report_path"),
        "daily_path": payload.get("daily_path"),
        "research_lanes_latest_path": payload.get("research_lanes_latest_path"),
        "public_apis_expansion_latest_path": payload.get("public_apis_expansion_latest_path"),
        "public_apis_expansion_item_path": payload.get("public_apis_expansion_item_path"),
        "public_apis_expansion_daily_json_path": payload.get("public_apis_expansion_daily_json_path"),
        "public_apis_expansion_daily_markdown_path": payload.get("public_apis_expansion_daily_markdown_path"),
        "verification_errors": list(payload.get("verification_errors") or [])[:cap],
        "provider_write": False,
        "execution_allowed": False,
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
        "compact_response": True,
    }


def compact_data_source_coverage_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    modules = list(payload.get("modules") or [])
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "ok"),
        "total_modules": int(payload.get("total_modules", len(modules))),
        "modules_fully_covered": list(payload.get("modules_fully_covered") or [])[:cap],
        "modules_partially_covered": list(payload.get("modules_partially_covered") or [])[:cap],
        "modules_without_verified_source": list(payload.get("modules_without_verified_source") or [])[:cap],
        "modules": modules[:cap],
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "raw_payload_included": False,
        "compact_response": True,
    }


def compact_data_availability_tiers_response(payload: dict[str, Any], limit: int = 100) -> dict[str, Any]:
    cap = max(1, min(int(limit or 100), 100))
    modules = list(payload.get("modules") or [])
    rows = []
    for row in modules[:cap]:
        rows.append(
            {
                "module": row.get("module"),
                "current_best_tier": row.get("current_best_tier"),
                "supported_tiers": list(row.get("supported_tiers") or [])[:5],
                "unsupported_tiers": list(row.get("unsupported_tiers") or [])[:5],
                "fields_available": list(row.get("fields_available") or [])[:80],
                "fields_missing": list(row.get("fields_missing") or [])[:80],
                "derived_features_available": list(row.get("derived_features_available") or [])[:30],
                "derived_features_blocked": list(row.get("derived_features_blocked") or [])[:30],
                "calibration_buckets_available": list(row.get("calibration_buckets_available") or [])[:10],
                "calibration_bucket": row.get("calibration_bucket"),
                "missing_critical_inputs": list(row.get("missing_critical_inputs") or [])[:30],
                "missing_advanced_inputs": list(row.get("missing_advanced_inputs") or [])[:30],
                "confidence_cap": float(row.get("confidence_cap", 0.0) or 0.0),
                "confidence_cap_reason": row.get("confidence_cap_reason"),
                "budget_required_for_next_layer": bool(row.get("budget_required_for_next_layer", False)),
                "requires_budget_approval": bool(row.get("requires_budget_approval", False)),
                "next_free_action": row.get("next_free_action"),
                "paid_action_blocked": bool(row.get("paid_action_blocked", True)),
                "recommended_no_spend_next_step": row.get("recommended_no_spend_next_step"),
                "data_not_available_warning": row.get("data_not_available_warning"),
            }
        )
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "ok"),
        "schema_version": payload.get("schema_version"),
        "created_at": payload.get("created_at"),
        "module_filter": payload.get("module_filter"),
        "total_modules": int(payload.get("total_modules", len(modules))),
        "modules": rows,
        "enabled_source_count": int(payload.get("enabled_source_count", 0) or 0),
        "paid_source_enabled_count": int(payload.get("paid_source_enabled_count", 0) or 0),
        "paid_action_blocked": True,
        "recommended_no_spend_next_step": payload.get("recommended_no_spend_next_step", "no-call audit of existing source reports"),
        "latest_path": payload.get("latest_path"),
        "item_path": payload.get("item_path"),
        "daily_json_path": payload.get("daily_json_path"),
        "daily_markdown_path": payload.get("daily_markdown_path"),
        "storage": _compact_storage_health(payload),
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
        "compact_response": True,
    }


def compact_data_source_research_lanes_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "ok"),
        "total_tasks": int(payload.get("total_tasks", 0)),
        "open_tasks": int(payload.get("open_tasks", 0)),
        "priority_counts": dict(payload.get("priority_counts") or {}),
        "tasks": list(payload.get("tasks") or [])[:cap],
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "raw_payload_included": False,
        "compact_response": True,
    }


def compact_data_source_health_response(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "ok"),
        "schema_version": payload.get("schema_version"),
        "total_lanes": int(payload.get("total_lanes", 0)),
        "total_sources": int(payload.get("total_sources", 0)),
        "enabled_source_count": int(payload.get("enabled_source_count", 0)),
        "lanes_with_candidate_sources": int(payload.get("lanes_with_candidate_sources", 0)),
        "lanes_needing_external_research": int(payload.get("lanes_needing_external_research", 0)),
        "needs_terms_review_count": int(payload.get("needs_terms_review_count", 0)),
        "future_source_candidate_count": int(payload.get("future_source_candidate_count", 0)),
        "source_counts_by_category": dict(payload.get("source_counts_by_category") or {}),
        "provider_write_enabled_count": int(payload.get("provider_write_enabled_count", 0)),
        "execution_allowed_count": int(payload.get("execution_allowed_count", 0)),
        "storage": _compact_storage_health(payload),
        "provider_write": False,
        "execution_allowed": False,
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


def compact_cfbd_adapter_verification_response(payload: dict[str, Any]) -> dict[str, Any]:
    quality = dict(payload.get("quality_scores") or {})
    report_paths = dict(payload.get("report_paths") or {})
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", payload.get("adapter_status", "metadata_only_verified")),
        "source_id": payload.get("source_id", "collegefootballdata"),
        "module": payload.get("module", "americanfootball_ncaaf"),
        "adapter_status": payload.get("adapter_status"),
        "source_access_type": payload.get("source_access_type"),
        "current_phase_allowed": bool(payload.get("current_phase_allowed", False)),
        "verification_phase_allowed": bool(payload.get("verification_phase_allowed", True)),
        "requires_budget_approval": bool(payload.get("requires_budget_approval", False)),
        "call_budget_level": payload.get("call_budget_level"),
        "max_provider_calls_default": int(payload.get("max_provider_calls_default", 0) or 0),
        "max_provider_calls_hard_cap": int(payload.get("max_provider_calls_hard_cap", 3) or 3),
        "paid_upgrade_required": bool(payload.get("paid_upgrade_required", False)),
        "paid_upgrade_allowed": False,
        "substantial_usage_allowed": False,
        "approval_status": payload.get("approval_status"),
        "enabled": False,
        "dry_run": bool(payload.get("dry_run", True)),
        "season": payload.get("season"),
        "week": payload.get("week"),
        "sample_profile": payload.get("sample_profile", "games_tiny"),
        "max_records_requested": int(payload.get("max_records_requested", 0) or 0),
        "max_records_effective": int(payload.get("max_records_effective", 0) or 0),
        "max_provider_calls_requested": int(payload.get("max_provider_calls_requested", 1) or 1),
        "max_provider_calls_effective": int(payload.get("max_provider_calls_effective", 1) or 1),
        "include_games": bool(payload.get("include_games", True)),
        "include_team_stats": bool(payload.get("include_team_stats", False)),
        "include_advanced_stats": bool(payload.get("include_advanced_stats", False)),
        "include_rankings": bool(payload.get("include_rankings", False)),
        "include_lines": bool(payload.get("include_lines", False)),
        "fetch_live_sample_requested": bool(payload.get("fetch_live_sample_requested", False)),
        "fetch_live_sample_performed": bool(payload.get("fetch_live_sample_performed", False)),
        "provider_calls_made": int(payload.get("provider_calls_made", 0) or 0),
        "endpoints_called": list(payload.get("endpoints_called") or [])[:10],
        "skipped_endpoints_due_to_call_budget": list(payload.get("skipped_endpoints_due_to_call_budget") or [])[:10],
        "provider_errors": list(payload.get("provider_errors") or [])[:10],
        "missing_api_key": bool(payload.get("missing_api_key", False)),
        "api_key_configured": bool(payload.get("api_key_configured", False)),
        "sample_records_received": int(payload.get("sample_records_received", 0)),
        "sample_records_normalized": int(payload.get("sample_records_normalized", 0)),
        "records_received_by_endpoint": dict(payload.get("records_received_by_endpoint") or {}),
        "records_normalized_by_endpoint": dict(payload.get("records_normalized_by_endpoint") or {}),
        "fields_mapped_by_endpoint": dict(payload.get("fields_mapped_by_endpoint") or {}),
        "model_inputs_supported": list(payload.get("model_inputs_supported") or [])[:100],
        "covered_model_inputs": list(payload.get("covered_model_inputs") or [])[:100],
        "newly_supported_model_inputs": list(payload.get("newly_supported_model_inputs") or [])[:100],
        "missing_model_inputs": list(payload.get("missing_model_inputs") or [])[:100],
        "missing_required_inputs": list(payload.get("missing_required_inputs") or [])[:100],
        "missing_optional_inputs": list(payload.get("missing_optional_inputs") or [])[:100],
        "outcome_fields_available": list(payload.get("outcome_fields_available") or [])[:50],
        "historical_backfill_fields_available": list(payload.get("historical_backfill_fields_available") or payload.get("backfill_fields_available") or [])[:50],
        "backfill_fields_available": list(payload.get("backfill_fields_available") or [])[:50],
        "join_keys": list(payload.get("join_keys") or [])[:50],
        "coverage_score_before": float(payload.get("coverage_score_before", 0.0) or 0.0),
        "coverage_score_after": float(payload.get("coverage_score_after", payload.get("coverage_score", 0.0)) or 0.0),
        "coverage_score": float(payload.get("coverage_score", 0.0) or 0.0),
        "calibration_readiness_before": float(payload.get("calibration_readiness_before", 0.0) or 0.0),
        "calibration_readiness_after": float(payload.get("calibration_readiness_after", payload.get("calibration_readiness_score", 0.0)) or 0.0),
        "calibration_readiness_score": float(payload.get("calibration_readiness_score", quality.get("calibration_readiness_score", 0.0)) or 0.0),
        "cfbd_alone_supports_ncaaf_calibration": bool(payload.get("cfbd_alone_supports_ncaaf_calibration", False)),
        "sportsdataverse_cfb_still_needed": bool(payload.get("sportsdataverse_cfb_still_needed", True)),
        "quality_scores": {
            "source_reliability_score": quality.get("source_reliability_score"),
            "freshness_score": quality.get("freshness_score"),
            "coverage_score": quality.get("coverage_score"),
            "completeness_score": quality.get("completeness_score"),
            "join_quality_score": quality.get("join_quality_score"),
            "model_input_fill_rate": quality.get("model_input_fill_rate"),
            "terms_risk_score": quality.get("terms_risk_score"),
            "rate_limit_risk_score": quality.get("rate_limit_risk_score"),
            "historical_depth_score": quality.get("historical_depth_score"),
            "outcome_availability_score": quality.get("outcome_availability_score"),
            "current_phase_usability_score": quality.get("current_phase_usability_score"),
            "future_value_score": quality.get("future_value_score"),
            "calibration_readiness_score": quality.get("calibration_readiness_score"),
            "calibration_value_score": quality.get("calibration_value_score"),
            "live_sample_required": bool(quality.get("live_sample_required", True)),
            "metadata_only": bool(quality.get("metadata_only", False)),
            "quality_tier": quality.get("quality_tier"),
        },
        "terms_review_required": bool(payload.get("terms_review_required", True)),
        "live_sample_required": bool(payload.get("live_sample_required", True)),
        "metadata_only_supported": bool(payload.get("metadata_only_supported", True)),
        "production_ingestion_enabled": False,
        "bulk_ingest_enabled": False,
        "report_paths": {
            "latest_path": report_paths.get("latest_path") or payload.get("latest_path"),
            "item_path": report_paths.get("item_path") or payload.get("item_path"),
            "daily_json_path": report_paths.get("daily_json_path") or payload.get("daily_json_path"),
            "daily_markdown_path": report_paths.get("daily_markdown_path") or payload.get("daily_markdown_path"),
        },
        "storage": _compact_storage_health(payload),
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
        "compact_response": True,
    }


def compact_data_source_env_vars_response(payload: dict[str, Any], limit: int = 100) -> dict[str, Any]:
    cap = max(1, min(int(limit or 100), 500))
    rows = []
    for row in list(payload.get("env_vars") or [])[:cap]:
        rows.append(
            {
                "source_id": row.get("source_id"),
                "display_name": row.get("display_name"),
                "module_lane": row.get("module_lane"),
                "source_category": row.get("source_category"),
                "env_var_name": row.get("env_var_name"),
                "required_for_live_fetch": bool(row.get("required_for_live_fetch", False)),
                "optional_for_metadata_only": bool(row.get("optional_for_metadata_only", True)),
                "key_is_configured": bool(row.get("key_is_configured", False)),
                "secret_value_redacted": True,
            }
        )
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "ok"),
        "module_filter": payload.get("module_filter"),
        "env_var_count": int(payload.get("env_var_count", len(rows))),
        "env_vars": rows,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "raw_payload_included": False,
        "secrets_included": False,
        "compact_response": True,
    }


def compact_data_source_priorities_response(payload: dict[str, Any], limit: int = 50) -> dict[str, Any]:
    cap = max(1, min(int(limit or 50), 100))
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "ok"),
        "module_filter": payload.get("module_filter"),
        "priority_count": int(payload.get("priority_count", 0)),
        "priorities": list(payload.get("priorities") or [])[:cap],
        "top_stock_analyst_priorities": list(payload.get("top_stock_analyst_priorities") or [])[:20],
        "top_crypto_edge_priorities": list(payload.get("top_crypto_edge_priorities") or [])[:20],
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "raw_payload_included": False,
        "secrets_included": False,
        "compact_response": True,
    }


def compact_public_apis_expansion_report_response(payload: dict[str, Any], limit: int = 50) -> dict[str, Any]:
    cap = max(1, min(int(limit or 50), 100))
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "ok"),
        "created_at": payload.get("created_at"),
        "module_filter": payload.get("module_filter"),
        "total_sources_before": int(payload.get("total_sources_before", 0)),
        "total_sources_after": int(payload.get("total_sources_after", 0)),
        "sources_added": int(payload.get("sources_added", 0)),
        "sources_updated": int(payload.get("sources_updated", 0)),
        "enabled_source_count": int(payload.get("enabled_source_count", 0)),
        "source_counts_by_lane": dict(payload.get("source_counts_by_lane") or {}),
        "source_counts_by_category": dict(payload.get("source_counts_by_category") or {}),
        "key_required_source_count": int(payload.get("key_required_source_count", 0)),
        "oauth_required_source_count": int(payload.get("oauth_required_source_count", 0)),
        "no_auth_source_count": int(payload.get("no_auth_source_count", 0)),
        "terms_review_required_count": int(payload.get("terms_review_required_count", 0)),
        "trading_capable_disabled_count": int(payload.get("trading_capable_disabled_count", 0)),
        "provider_write_enabled_count": int(payload.get("provider_write_enabled_count", 0)),
        "execution_allowed_count": int(payload.get("execution_allowed_count", 0)),
        "top_20_adapter_priorities": list(payload.get("top_20_adapter_priorities") or [])[:20],
        "top_stock_analyst_priorities": list(payload.get("top_stock_analyst_priorities") or [])[:20],
        "top_crypto_edge_priorities": list(payload.get("top_crypto_edge_priorities") or [])[:20],
        "env_var_names_required": list(payload.get("env_var_names_required") or [])[:cap],
        "public_apis_expansion_latest_path": payload.get("public_apis_expansion_latest_path"),
        "public_apis_expansion_item_path": payload.get("public_apis_expansion_item_path"),
        "public_apis_expansion_daily_json_path": payload.get("public_apis_expansion_daily_json_path"),
        "public_apis_expansion_daily_markdown_path": payload.get("public_apis_expansion_daily_markdown_path"),
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "raw_payload_included": False,
        "secrets_included": False,
        "compact_response": True,
    }

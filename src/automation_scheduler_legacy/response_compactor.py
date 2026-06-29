from __future__ import annotations

from typing import Any

from src.security.secret_safety import looks_like_secret_value, redact_string

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
            if lk in {"new_api_keys_required", "api_keys_required", "paid_provider_required"}:
                out[k] = _redact(v)
            elif any(s in lk for s in _SECRET_KEYS):
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
                "raw_response",
                "bet_slip",
                "wager_payload",
                "order_request",
                "broker_order",
                "sportsbook_wager",
                "sportsbook_bet",
                "sportsbook_ticket",
                "kalshi_order",
                "crypto_order",
                "provider_write_payload",
                "ticket_payload",
                "slip_payload",
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


def _compact_extreme_randomness_sample_item(item: dict[str, Any] | None) -> dict[str, Any]:
    row = item if isinstance(item, dict) else {}
    return {
        "asset_type": row.get("asset_type"),
        "market_type": row.get("market_type"),
        "extreme_signal_score": float(row.get("extreme_signal_score", 0.0) or 0.0),
        "random_baseline_percentile": float(row.get("random_baseline_percentile", 0.0) or 0.0),
        "tail_event_type": row.get("tail_event_type", "normal_noise"),
        "tail_event_risk_score": float(row.get("tail_event_risk_score", 0.0) or 0.0),
        "rmt_status": row.get("rmt_status", "not_applicable"),
        "tracy_widom_status": row.get("tracy_widom_status", "not_applicable"),
        "edge_survives_random_baseline": bool(row.get("edge_survives_random_baseline", False)),
        "fake_edge_risk": row.get("fake_edge_risk", "low"),
        "recommended_action_adjustment": row.get("recommended_action_adjustment", "none"),
        "no_bet_reasons": list(row.get("no_bet_reasons") or [])[:10],
        "no_trade_reasons": list(row.get("no_trade_reasons") or [])[:10],
        "missing_inputs": list(row.get("missing_inputs") or [])[:20],
        "edge_vs_random_baseline": row.get("edge_vs_random_baseline"),
        "outlier_status": row.get("outlier_status"),
        "red_team_warning": row.get("red_team_warning"),
        "insufficient_sample": bool(row.get("insufficient_sample", True)),
        "blocked_reason": row.get("blocked_reason"),
    }


def compact_extreme_randomness_diagnostics_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    baseline = payload.get("random_baseline") if isinstance(payload.get("random_baseline"), dict) else {}
    tail = payload.get("tail_event") if isinstance(payload.get("tail_event"), dict) else {}
    rmt = payload.get("random_matrix") if isinstance(payload.get("random_matrix"), dict) else {}
    tw = payload.get("tracy_widom") if isinstance(payload.get("tracy_widom"), dict) else {}
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "extreme_randomness_diagnostics_complete"),
        "red_team_only": True,
        "research_only": True,
        "calibration_only": bool(payload.get("calibration_only", True)),
        "sample_item": _compact_extreme_randomness_sample_item(payload.get("sample_item") if isinstance(payload.get("sample_item"), dict) else {}),
        "random_baseline": {
            "baseline_method": baseline.get("baseline_method"),
            "baseline_sample_size": int(baseline.get("baseline_sample_size", 0) or 0),
            "observed_signal": baseline.get("observed_signal"),
            "baseline_mean": baseline.get("baseline_mean"),
            "baseline_std": baseline.get("baseline_std"),
            "observed_vs_baseline_z_score": baseline.get("observed_vs_baseline_z_score"),
            "observed_vs_baseline_percentile": baseline.get("observed_vs_baseline_percentile"),
            "baseline_support_status": baseline.get("baseline_support_status"),
            "edge_survives_random_baseline": bool(baseline.get("edge_survives_random_baseline", False)),
            "random_baseline_warning": baseline.get("random_baseline_warning"),
        },
        "tail_event": {
            "tail_event_type": tail.get("tail_event_type"),
            "tail_event_confidence": tail.get("tail_event_confidence"),
            "tail_event_risk_score": tail.get("tail_event_risk_score"),
            "volatility_adjusted_signal": tail.get("volatility_adjusted_signal"),
            "liquidity_adjusted_signal": tail.get("liquidity_adjusted_signal"),
            "correlation_adjusted_signal": tail.get("correlation_adjusted_signal"),
            "random_extreme_probability": tail.get("random_extreme_probability"),
            "data_error_risk": tail.get("data_error_risk"),
            "no_trade_no_bet_reason": tail.get("no_trade_no_bet_reason"),
        },
        "random_matrix": {
            "rmt_status": rmt.get("rmt_status", "not_applicable"),
            "dimension_count": int(rmt.get("dimension_count", 0) or 0),
            "sample_size": int(rmt.get("sample_size", 0) or 0),
            "matrix_condition_status": rmt.get("matrix_condition_status"),
            "largest_eigenvalue": rmt.get("largest_eigenvalue"),
            "bulk_edge_estimate": rmt.get("bulk_edge_estimate"),
            "largest_eigenvalue_exceeds_random_bulk": bool(rmt.get("largest_eigenvalue_exceeds_random_bulk", False)),
            "correlation_shock_score": rmt.get("correlation_shock_score"),
            "systemwide_noise_risk": rmt.get("systemwide_noise_risk"),
            "market_mode_detected": bool(rmt.get("market_mode_detected", False)),
            "idiosyncratic_signal_risk": rmt.get("idiosyncratic_signal_risk"),
            "insufficient_matrix_data": bool(rmt.get("insufficient_matrix_data", True)),
        },
        "tracy_widom": {
            "tracy_widom_status": tw.get("tracy_widom_status", "not_applicable"),
            "tw_applicable": bool(tw.get("tw_applicable", False)),
            "tw_score": tw.get("tw_score"),
            "tw_tail_probability": tw.get("tw_tail_probability"),
            "edge_exceeds_tw_threshold": bool(tw.get("edge_exceeds_tw_threshold", False)),
            "random_extreme_warning": tw.get("random_extreme_warning"),
            "extreme_value_confidence": tw.get("extreme_value_confidence"),
            "blocked_reason": tw.get("blocked_reason"),
        },
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
        "raw_payload_included": False,
        "secrets_included": False,
        "compact_response": True,
    }


def compact_extreme_randomness_report_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    advanced = payload.get("advanced_math_status") if isinstance(payload.get("advanced_math_status"), dict) else {}
    universality = payload.get("universality") if isinstance(payload.get("universality"), dict) else {}
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "extreme_randomness_report"),
        "major_lesson": payload.get("major_lesson"),
        "red_team_only": True,
        "research_only": True,
        "calibration_only": True,
        "advanced_math_status": advanced,
        "allowed_uses": list(payload.get("allowed_uses") or [])[:20],
        "forbidden_uses": list(payload.get("forbidden_uses") or [])[:20],
        "recent_event_count": int(payload.get("recent_event_count", 0) or 0),
        "universality": {
            "universality_status": universality.get("universality_status", "research_only"),
            "cross_asset_pattern_detected": bool(universality.get("cross_asset_pattern_detected", False)),
            "similar_tail_events_by_asset_type": dict(universality.get("similar_tail_events_by_asset_type") or {}),
            "shared_structure_hypothesis": universality.get("shared_structure_hypothesis"),
            "universality_confidence": universality.get("universality_confidence"),
            "research_only": True,
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
        "raw_payload_included": False,
        "secrets_included": False,
        "compact_response": True,
    }


def _compact_football_section(section: Any, keys: list[str], limit: int = 10) -> dict[str, Any]:
    row = section if isinstance(section, dict) else {}
    out: dict[str, Any] = {}
    for key in keys:
        value = row.get(key)
        if isinstance(value, list):
            out[key] = value[:limit]
        elif isinstance(value, dict):
            out[key] = redact_and_limit_payload(value, limit=limit)
        else:
            out[key] = value
    return out


def compact_football_impact_readiness_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "football_impact_readiness"),
        "supported_sports": list(payload.get("supported_sports") or [])[:cap],
        "supported_roles": list(payload.get("supported_roles") or [])[:cap],
        "supported_markets": list(payload.get("supported_markets") or [])[:cap],
        "data_tier_requirements": redact_and_limit_payload(payload.get("data_tier_requirements") or {}, limit=cap),
        "nfl_readiness": redact_and_limit_payload(payload.get("nfl_readiness") or {}, limit=cap),
        "ncaaf_readiness": redact_and_limit_payload(payload.get("ncaaf_readiness") or {}, limit=cap),
        "missing_data_by_sport": redact_and_limit_payload(payload.get("missing_data_by_sport") or {}, limit=cap),
        "calibration_requirements": list(payload.get("calibration_requirements") or [])[:cap],
        "no_spend_policy": redact_and_limit_payload(payload.get("no_spend_policy") or {}, limit=cap),
        "forbidden_features": list(payload.get("forbidden_features") or [])[:cap],
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
        "raw_payload_included": False,
        "raw_payload_exposed": False,
        "secrets_included": False,
        "compact_response": True,
    }


def compact_football_impact_diagnostics_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    data = payload.get("data_availability") if isinstance(payload.get("data_availability"), dict) else {}
    play = payload.get("play_drive_impact") if isinstance(payload.get("play_drive_impact"), dict) else {}
    role = payload.get("role_impact") if isinstance(payload.get("role_impact"), dict) else {}
    personnel = payload.get("personnel_context") if isinstance(payload.get("personnel_context"), dict) else {}
    matchup = payload.get("matchup_context") if isinstance(payload.get("matchup_context"), dict) else {}
    availability = payload.get("availability_context") if isinstance(payload.get("availability_context"), dict) else {}
    incentive = payload.get("incentive_context") if isinstance(payload.get("incentive_context"), dict) else {}
    market = payload.get("market_relevance") if isinstance(payload.get("market_relevance"), dict) else {}
    calibration = payload.get("calibration") if isinstance(payload.get("calibration"), dict) else {}
    red_team = payload.get("red_team") if isinstance(payload.get("red_team"), dict) else {}
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "football_player_impact_complete"),
        "sport": payload.get("sport"),
        "market_type": payload.get("market_type"),
        "data_tier": int(payload.get("data_tier", 0) or 0),
        "tier_name": payload.get("tier_name"),
        "player_level_allowed": bool(payload.get("player_level_allowed", False)),
        "tracking_level_allowed": bool(payload.get("tracking_level_allowed", False)),
        "football_impact_score": payload.get("football_impact_score", 0.0),
        "recommended_review_status": payload.get("recommended_review_status", payload.get("recommended_action_adjustment")),
        "play_drive_impact": _compact_football_section(
            play,
            [
                "status",
                "play_impact_score",
                "drive_impact_score",
                "efficiency_score",
                "explosiveness_score",
                "leverage_score",
                "red_zone_score",
                "pace_volume_score",
                "turnover_penalty",
                "penalty_penalty",
                "insufficient_sample",
                "confidence_cap_reason",
                "limited_proxy_used",
                "epa_fabricated",
                "missing_inputs",
            ],
            cap,
        ),
        "role_impact": _compact_football_section(
            role,
            [
                "role",
                "role_impact_score",
                "role_usage_score",
                "role_efficiency_score",
                "role_volatility_score",
                "role_confidence_cap",
                "player_level_allowed",
                "tracking_metrics_inferred",
                "confidence_cap_reason",
                "player_market_relevance",
                "missing_role_inputs",
            ],
            cap,
        ),
        "personnel_context": _compact_football_section(
            personnel,
            ["personnel_fit_score", "formation_fit_score", "matchup_stress_score", "defensive_structure_risk", "offensive_tendency_risk", "volatility_flags", "missing_inputs"],
            cap,
        ),
        "matchup_context": _compact_football_section(
            matchup,
            ["matchup_advantage_score", "matchup_risk_score", "mismatch_reasons", "no_bet_reasons", "market_specific_matchup_notes", "qb_pressure_risk_score", "wr_cb_matchup_score", "ol_dl_run_matchup_score", "missing_inputs"],
            cap,
        ),
        "availability_context": _compact_football_section(
            availability,
            ["availability_score", "snap_stability_score", "role_stability_score", "injury_risk_score", "rest_travel_risk_score", "weather_adjustment_score", "wind_risk_score", "starting_qb_market_risk_score", "confidence_cap_reason", "market_wide_risk_flags", "missing_inputs"],
            cap,
        ),
        "incentive_context": _compact_football_section(
            incentive,
            ["incentive_context_status", "incentive_behavior_score", "stat_chase_risk", "team_alignment_score", "narrative_overfit_risk", "confidence_modifier", "no_bet_reasons", "incentive_is_standalone_edge", "bonus_threshold_fabricated", "missing_inputs"],
            cap,
        ),
        "market_relevance": _compact_football_section(
            market,
            ["market_relevance_scores", "strongest_market_links", "weak_market_links", "no_bet_market_reasons", "player_prop_relevance", "team_market_relevance", "market_confidence_caps", "selected_market_type", "selected_market_relevance_score", "weather_adjusted_markets", "pressure_adjusted_markets"],
            cap,
        ),
        "calibration_status": payload.get("calibration_status", "insufficient_data"),
        "calibration": _compact_football_section(
            calibration,
            ["calibration_status", "sample_size", "matched_outcomes_count", "false_positive_rate", "hit_rate", "confidence_cap", "insufficient_sample", "next_required_data", "calibration_buckets"],
            cap,
        ),
        "data_availability": _compact_football_section(
            data,
            ["status", "sport", "data_tier", "tier_name", "available_field_groups", "missing_field_groups", "player_level_allowed", "team_level_allowed", "tracking_level_allowed", "calibration_allowed", "confidence_cap", "confidence_cap_reason", "no_fabrication", "next_data_to_collect", "ncaaf_tracking_not_assumed"],
            cap,
        ),
        "red_team": _compact_football_section(
            red_team,
            ["red_team_status", "downgrade_score", "recommended_action_adjustment", "no_bet_reasons", "red_team_reasons", "missing_inputs", "confidence_cap_reason", "red_team_only"],
            cap,
        ),
        "recommended_action_adjustment": payload.get("recommended_action_adjustment"),
        "markets_to_review": list(payload.get("markets_to_review") or [])[:cap],
        "no_bet_reasons": list(payload.get("no_bet_reasons") or [])[:cap],
        "missing_inputs": list(payload.get("missing_inputs") or [])[:cap],
        "next_data_to_collect": list(payload.get("next_data_to_collect") or [])[:cap],
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
        "raw_payload_included": False,
        "raw_payload_exposed": False,
        "secrets_included": False,
        "compact_response": True,
    }


def _compact_soccer_section(section: Any, keys: list[str], limit: int = 10) -> dict[str, Any]:
    row = section if isinstance(section, dict) else {}
    out: dict[str, Any] = {}
    for key in keys:
        value = row.get(key)
        if isinstance(value, list):
            out[key] = value[:limit]
        elif isinstance(value, dict):
            out[key] = redact_and_limit_payload(value, limit=limit)
        else:
            out[key] = value
    return out


def compact_soccer_impact_readiness_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "soccer_impact_readiness"),
        "supported_sports": list(payload.get("supported_sports") or [])[:cap],
        "supported_roles": list(payload.get("supported_roles") or [])[:cap],
        "supported_markets": list(payload.get("supported_markets") or [])[:cap],
        "data_tier_requirements": redact_and_limit_payload(payload.get("data_tier_requirements") or {}, limit=cap),
        "soccer_readiness": redact_and_limit_payload(payload.get("soccer_readiness") or {}, limit=cap),
        "missing_data_by_market": redact_and_limit_payload(payload.get("missing_data_by_market") or {}, limit=cap),
        "calibration_requirements": list(payload.get("calibration_requirements") or [])[:cap],
        "no_spend_policy": redact_and_limit_payload(payload.get("no_spend_policy") or {}, limit=cap),
        "forbidden_features": list(payload.get("forbidden_features") or [])[:cap],
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
        "raw_payload_included": False,
        "raw_payload_exposed": False,
        "secrets_included": False,
        "compact_response": True,
    }


def compact_soccer_impact_diagnostics_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    data = payload.get("data_availability") if isinstance(payload.get("data_availability"), dict) else {}
    possession = payload.get("possession_value_impact") if isinstance(payload.get("possession_value_impact"), dict) else {}
    tactical = payload.get("tactical_context") if isinstance(payload.get("tactical_context"), dict) else {}
    pressing = payload.get("pressing_transition_context") if isinstance(payload.get("pressing_transition_context"), dict) else {}
    player = payload.get("player_role_impact") if isinstance(payload.get("player_role_impact"), dict) else {}
    lineup = payload.get("lineup_availability_context") if isinstance(payload.get("lineup_availability_context"), dict) else {}
    set_piece = payload.get("set_piece_context") if isinstance(payload.get("set_piece_context"), dict) else {}
    keeper = payload.get("goalkeeper_context") if isinstance(payload.get("goalkeeper_context"), dict) else {}
    referee = payload.get("referee_context") if isinstance(payload.get("referee_context"), dict) else {}
    matchup = payload.get("matchup_context") if isinstance(payload.get("matchup_context"), dict) else {}
    incentive = payload.get("incentive_context") if isinstance(payload.get("incentive_context"), dict) else {}
    market = payload.get("market_relevance") if isinstance(payload.get("market_relevance"), dict) else {}
    calibration = payload.get("calibration") if isinstance(payload.get("calibration"), dict) else {}
    red_team = payload.get("red_team") if isinstance(payload.get("red_team"), dict) else {}
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "soccer_possession_value_impact_complete"),
        "sport": payload.get("sport"),
        "market_type": payload.get("market_type"),
        "data_tier": int(payload.get("data_tier", 0) or 0),
        "tier_name": payload.get("tier_name"),
        "team_level_allowed": bool(payload.get("team_level_allowed", False)),
        "player_level_allowed": bool(payload.get("player_level_allowed", False)),
        "tactical_level_allowed": bool(payload.get("tactical_level_allowed", False)),
        "tracking_level_allowed": bool(payload.get("tracking_level_allowed", False)),
        "soccer_impact_score": payload.get("soccer_impact_score", 0.0),
        "recommended_review_status": payload.get("recommended_review_status"),
        "possession_value_impact": _compact_soccer_section(
            possession,
            ["possession_value_score", "chance_quality_score", "territorial_dominance_score", "progression_score", "final_third_pressure_score", "box_entry_score", "xg_quality_score", "first_half_pressure_score", "open_play_attack_score", "defensive_suppression_score", "total_signal_score", "team_total_signal_score", "btts_signal_score", "confidence_cap_reason", "insufficient_sample", "limited_proxy", "xg_fabricated", "xt_fabricated", "obv_vaep_fabricated", "missing_inputs"],
            cap,
        ),
        "tactical_context": _compact_soccer_section(
            tactical,
            ["tactical_fit_score", "tactical_stability_score", "pressing_score", "counter_pressing_score", "directness_score", "formation_stability_score", "tactical_mismatch_risk", "style_market_relevance", "formation", "formation_fabricated", "tactical_context_standalone_edge", "missing_inputs", "no_bet_reasons"],
            cap,
        ),
        "pressing_transition_context": _compact_soccer_section(
            pressing,
            ["pressing_impact_score", "high_turnover_score", "counterpress_score", "transition_attack_score", "transition_defense_risk", "rest_defense_score", "market_relevance_modifier", "pressing_fabricated", "missing_inputs", "no_bet_reasons"],
            cap,
        ),
        "player_role_impact": _compact_soccer_section(
            player,
            ["role", "player_impact_score", "attacking_threat_score", "creative_value_score", "defensive_work_score", "pressing_value_score", "set_piece_role_score", "card_risk_score", "minutes_role_stability_score", "player_market_relevance", "penalty_taker_fabricated", "set_piece_role_fabricated", "post_shot_xg_fabricated", "missing_player_inputs", "no_bet_reasons"],
            cap,
        ),
        "lineup_availability_context": _compact_soccer_section(
            lineup,
            ["lineup_certainty_score", "availability_score", "rotation_risk_score", "minutes_projection_confidence", "tactical_continuity_score", "rest_travel_risk_score", "competition_priority_risk", "confidence_cap_reason", "lineup_fabricated", "injury_status_fabricated", "confirmed_goalkeeper_fabricated", "missing_inputs", "no_bet_reasons"],
            cap,
        ),
        "set_piece_context": _compact_soccer_section(
            set_piece,
            ["set_piece_attack_score", "set_piece_defense_score", "penalty_context_score", "corner_context_score", "aerial_mismatch_score", "player_goal_prop_modifier", "total_market_modifier", "team_total_modifier", "set_piece_xg_separated", "penalty_taker_fabricated", "set_piece_role_fabricated", "referee_penalty_tendency_fabricated", "missing_inputs", "no_bet_reasons"],
            cap,
        ),
        "goalkeeper_context": _compact_soccer_section(
            keeper,
            ["goalkeeper_impact_score", "starter_certainty_score", "shot_stopping_score", "cross_claim_score", "sweeping_score", "distribution_score", "goalkeeper_prop_relevance", "team_market_goalkeeper_modifier", "total_market_goalkeeper_modifier", "confirmed_starter", "post_shot_xg_fabricated", "missing_goalkeeper_inputs", "no_bet_reasons"],
            cap,
        ),
        "referee_context": _compact_soccer_section(
            referee,
            ["referee_environment_score", "card_market_relevance", "penalty_market_relevance", "foul_market_relevance", "game_flow_modifier", "total_market_modifier", "red_card_volatility_risk", "referee_context_standalone_edge", "referee_tendency_fabricated", "missing_inputs", "no_bet_reasons"],
            cap,
        ),
        "matchup_context": _compact_soccer_section(
            matchup,
            ["matchup_advantage_score", "matchup_risk_score", "tactical_mismatch_reasons", "no_bet_reasons", "market_specific_matchup_notes", "three_way_relevance", "asian_handicap_relevance", "total_relevance", "btts_relevance", "team_total_relevance", "player_prop_relevance", "card_prop_relevance", "tactical_mismatch_fabricated"],
            cap,
        ),
        "incentive_context": _compact_soccer_section(
            incentive,
            ["incentive_context_status", "incentive_behavior_score", "stat_chase_risk", "team_alignment_score", "rotation_motivation_risk", "narrative_overfit_risk", "confidence_modifier", "market_relevance_modifier", "incentive_is_standalone_edge", "bonus_threshold_fabricated", "no_bet_reasons"],
            cap,
        ),
        "market_relevance": _compact_soccer_section(
            market,
            ["market_relevance_scores", "strongest_market_links", "weak_market_links", "no_bet_market_reasons", "player_prop_relevance", "team_market_relevance", "tactical_market_relevance", "referee_market_relevance", "set_piece_market_relevance", "market_confidence_caps", "selected_market_type", "selected_market_relevance_score"],
            cap,
        ),
        "calibration_status": payload.get("calibration_status", calibration.get("calibration_status", "insufficient_data")),
        "calibration": _compact_soccer_section(calibration, ["calibration_status", "sample_size", "matched_outcomes_count", "insufficient_sample", "hit_rate", "false_positive_rate", "confidence_cap", "next_required_data", "calibration_buckets", "correct_score_extra_conservative"], cap),
        "data_availability": _compact_soccer_section(
            data,
            ["status", "sport", "data_tier", "tier_name", "team_level_allowed", "player_level_allowed", "tactical_level_allowed", "tracking_level_allowed", "calibration_allowed", "available_field_groups", "missing_field_groups", "confidence_cap", "confidence_cap_reason", "no_fabrication", "xt_not_fabricated", "obv_vaep_not_fabricated", "tracking_not_required", "formation_not_fabricated", "referee_tendency_not_fabricated", "next_data_to_collect"],
            cap,
        ),
        "red_team": _compact_soccer_section(red_team, ["red_team_status", "downgrade_score", "recommended_action_adjustment", "no_bet_reasons", "red_team_reasons", "missing_inputs", "confidence_cap_reason", "red_team_only"], cap),
        "recommended_action_adjustment": payload.get("recommended_action_adjustment"),
        "markets_to_review": list(payload.get("markets_to_review") or [])[:cap],
        "no_bet_reasons": list(payload.get("no_bet_reasons") or [])[:cap],
        "missing_inputs": list(payload.get("missing_inputs") or [])[:cap],
        "next_data_to_collect": list(payload.get("next_data_to_collect") or [])[:cap],
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
        "raw_payload_included": False,
        "raw_payload_exposed": False,
        "secrets_included": False,
        "compact_response": True,
    }


def _compact_hockey_section(section: Any, keys: list[str], limit: int = 10) -> dict[str, Any]:
    row = section if isinstance(section, dict) else {}
    out: dict[str, Any] = {}
    for key in keys:
        value = row.get(key)
        if isinstance(value, list):
            out[key] = value[:limit]
        elif isinstance(value, dict):
            out[key] = redact_and_limit_payload(value, limit=limit)
        else:
            out[key] = value
    return out


def compact_hockey_impact_readiness_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "hockey_impact_readiness"),
        "supported_sports": list(payload.get("supported_sports") or [])[:cap],
        "supported_roles": list(payload.get("supported_roles") or [])[:cap],
        "supported_markets": list(payload.get("supported_markets") or [])[:cap],
        "data_tier_requirements": redact_and_limit_payload(payload.get("data_tier_requirements") or {}, limit=cap),
        "nhl_readiness": redact_and_limit_payload(payload.get("nhl_readiness") or {}, limit=cap),
        "missing_data_by_market": redact_and_limit_payload(payload.get("missing_data_by_market") or {}, limit=cap),
        "calibration_requirements": list(payload.get("calibration_requirements") or [])[:cap],
        "no_spend_policy": redact_and_limit_payload(payload.get("no_spend_policy") or {}, limit=cap),
        "forbidden_features": list(payload.get("forbidden_features") or [])[:cap],
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
        "raw_payload_included": False,
        "raw_payload_exposed": False,
        "secrets_included": False,
        "compact_response": True,
    }


def compact_hockey_impact_diagnostics_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    data = payload.get("data_availability") if isinstance(payload.get("data_availability"), dict) else {}
    possession = payload.get("possession_impact") if isinstance(payload.get("possession_impact"), dict) else {}
    skater = payload.get("skater_impact") if isinstance(payload.get("skater_impact"), dict) else {}
    goalie = payload.get("goalie_impact") if isinstance(payload.get("goalie_impact"), dict) else {}
    line_pair = payload.get("line_pair_context") if isinstance(payload.get("line_pair_context"), dict) else {}
    special = payload.get("special_teams_context") if isinstance(payload.get("special_teams_context"), dict) else {}
    transition = payload.get("transition_context") if isinstance(payload.get("transition_context"), dict) else {}
    matchup = payload.get("matchup_context") if isinstance(payload.get("matchup_context"), dict) else {}
    availability = payload.get("availability_context") if isinstance(payload.get("availability_context"), dict) else {}
    incentive = payload.get("incentive_context") if isinstance(payload.get("incentive_context"), dict) else {}
    market = payload.get("market_relevance") if isinstance(payload.get("market_relevance"), dict) else {}
    calibration = payload.get("calibration") if isinstance(payload.get("calibration"), dict) else {}
    red_team = payload.get("red_team") if isinstance(payload.get("red_team"), dict) else {}
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "hockey_player_impact_complete"),
        "sport": payload.get("sport"),
        "market_type": payload.get("market_type"),
        "data_tier": int(payload.get("data_tier", 0) or 0),
        "tier_name": payload.get("tier_name"),
        "team_level_allowed": bool(payload.get("team_level_allowed", False)),
        "skater_level_allowed": bool(payload.get("skater_level_allowed", False)),
        "goalie_level_allowed": bool(payload.get("goalie_level_allowed", False)),
        "line_level_allowed": bool(payload.get("line_level_allowed", False)),
        "tracking_level_allowed": bool(payload.get("tracking_level_allowed", False)),
        "hockey_impact_score": payload.get("hockey_impact_score", 0.0),
        "recommended_review_status": payload.get("recommended_review_status"),
        "possession_impact": _compact_hockey_section(
            possession,
            [
                "possession_score",
                "shot_volume_score",
                "xg_quality_score",
                "high_danger_score",
                "rush_rebound_score",
                "first_period_pressure_score",
                "pace_volume_score",
                "team_market_signal_score",
                "total_signal_score",
                "team_total_signal_score",
                "confidence_cap_reason",
                "insufficient_sample",
                "limited_proxy",
                "xg_fabricated",
                "missing_inputs",
            ],
            cap,
        ),
        "skater_impact": _compact_hockey_section(
            skater,
            [
                "skater_role",
                "skater_impact_score",
                "shot_generation_score",
                "scoring_quality_score",
                "playmaking_score",
                "special_teams_role_score",
                "transition_score",
                "defensive_impact_score",
                "blocked_shot_relevance_score",
                "skater_market_relevance",
                "individual_xg_fabricated",
                "line_role_fabricated",
                "missing_skater_inputs",
                "no_bet_reasons",
            ],
            cap,
        ),
        "goalie_impact": _compact_hockey_section(
            goalie,
            [
                "goalie_impact_score",
                "starter_certainty_score",
                "shot_quality_adjusted_score",
                "workload_fatigue_score",
                "high_danger_resilience_score",
                "rebound_control_score",
                "goalie_prop_relevance",
                "team_market_goalie_modifier",
                "total_market_goalie_modifier",
                "confirmed_starter",
                "gsax_fabricated",
                "missing_goalie_inputs",
                "no_bet_reasons",
            ],
            cap,
        ),
        "line_pair_context": _compact_hockey_section(
            line_pair,
            ["line_quality_score", "line_stability_score", "pair_quality_score", "pair_stability_score", "matchup_deployment_score", "last_change_context_score", "prop_volume_modifier", "team_market_modifier", "confirmed_lines", "line_role_fabricated", "defensive_pair_fabricated", "missing_inputs", "no_bet_reasons"],
            cap,
        ),
        "special_teams_context": _compact_hockey_section(
            special,
            ["power_play_score", "penalty_kill_score", "special_teams_edge_score", "special_teams_volatility_score", "player_power_play_prop_relevance", "total_market_modifier", "team_total_modifier", "penalty_environment_fabricated", "missing_inputs", "no_bet_reasons"],
            cap,
        ),
        "transition_context": _compact_hockey_section(
            transition,
            ["transition_score", "controlled_entry_score", "zone_exit_score", "rush_attack_score", "rush_defense_risk", "forecheck_score", "turnover_risk_score", "market_relevance_modifier", "zone_entry_fabricated", "zone_exit_fabricated", "missing_inputs", "no_bet_reasons"],
            cap,
        ),
        "matchup_context": _compact_hockey_section(
            matchup,
            ["matchup_advantage_score", "matchup_risk_score", "mismatch_reasons", "no_bet_reasons", "market_specific_matchup_notes", "moneyline_relevance", "puckline_relevance", "total_relevance", "team_total_relevance", "player_prop_relevance", "goalie_prop_relevance", "deployment_fabricated"],
            cap,
        ),
        "availability_context": _compact_hockey_section(
            availability,
            ["availability_score", "lineup_certainty_score", "goalie_certainty_score", "rest_travel_risk_score", "fatigue_risk_score", "injury_risk_score", "role_stability_score", "confidence_cap_reason", "missing_inputs", "no_bet_reasons", "confirmed_goalie_fabricated", "confirmed_lines_fabricated"],
            cap,
        ),
        "incentive_context": _compact_hockey_section(
            incentive,
            ["incentive_context_status", "incentive_behavior_score", "stat_chase_risk", "team_alignment_score", "narrative_overfit_risk", "confidence_modifier", "market_relevance_modifier", "incentive_is_standalone_edge", "bonus_threshold_fabricated", "no_bet_reasons"],
            cap,
        ),
        "market_relevance": _compact_hockey_section(
            market,
            ["market_relevance_scores", "strongest_market_links", "weak_market_links", "no_bet_market_reasons", "skater_prop_relevance", "goalie_prop_relevance", "team_market_relevance", "special_teams_market_relevance", "market_confidence_caps", "selected_market_type", "selected_market_relevance_score"],
            cap,
        ),
        "calibration_status": payload.get("calibration_status", calibration.get("calibration_status", "insufficient_data")),
        "calibration": _compact_hockey_section(
            calibration,
            ["calibration_status", "sample_size", "matched_outcomes_count", "insufficient_sample", "hit_rate", "false_positive_rate", "confidence_cap", "next_required_data", "calibration_buckets"],
            cap,
        ),
        "data_availability": _compact_hockey_section(
            data,
            ["status", "sport", "data_tier", "tier_name", "team_level_allowed", "skater_level_allowed", "goalie_level_allowed", "line_level_allowed", "tracking_level_allowed", "calibration_allowed", "available_field_groups", "missing_field_groups", "confidence_cap", "confidence_cap_reason", "no_fabrication", "tracking_not_required", "zone_entry_exit_not_assumed", "gsax_not_inferred_from_save_percentage", "next_data_to_collect"],
            cap,
        ),
        "red_team": _compact_hockey_section(
            red_team,
            ["red_team_status", "downgrade_score", "recommended_action_adjustment", "no_bet_reasons", "red_team_reasons", "missing_inputs", "confidence_cap_reason", "red_team_only"],
            cap,
        ),
        "recommended_action_adjustment": payload.get("recommended_action_adjustment"),
        "markets_to_review": list(payload.get("markets_to_review") or [])[:cap],
        "no_bet_reasons": list(payload.get("no_bet_reasons") or [])[:cap],
        "missing_inputs": list(payload.get("missing_inputs") or [])[:cap],
        "next_data_to_collect": list(payload.get("next_data_to_collect") or [])[:cap],
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
        "raw_payload_included": False,
        "raw_payload_exposed": False,
        "secrets_included": False,
        "compact_response": True,
    }


def _compact_baseball_section(section: Any, keys: list[str], limit: int = 10) -> dict[str, Any]:
    row = section if isinstance(section, dict) else {}
    out: dict[str, Any] = {}
    for key in keys:
        value = row.get(key)
        if isinstance(value, list):
            out[key] = value[:limit]
        elif isinstance(value, dict):
            out[key] = redact_and_limit_payload(value, limit=limit)
        else:
            out[key] = value
    return out


def _safe_policy_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return False


def compact_baseball_impact_readiness_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    no_spend = payload.get("no_spend_policy") if isinstance(payload.get("no_spend_policy"), dict) else {}
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "baseball_impact_readiness"),
        "supported_sports": list(payload.get("supported_sports") or [])[:cap],
        "supported_roles": list(payload.get("supported_roles") or [])[:cap],
        "supported_markets": list(payload.get("supported_markets") or [])[:cap],
        "data_tier_requirements": redact_and_limit_payload(payload.get("data_tier_requirements") or {}, limit=cap),
        "mlb_readiness": redact_and_limit_payload(payload.get("mlb_readiness") or {}, limit=cap),
        "missing_data_by_market": redact_and_limit_payload(payload.get("missing_data_by_market") or {}, limit=cap),
        "calibration_requirements": list(payload.get("calibration_requirements") or [])[:cap],
        "no_spend_policy": {
            "paid_provider_required": _safe_policy_bool(no_spend.get("paid_provider_required", False)),
            "new_provider_calls_added": _safe_policy_bool(no_spend.get("new_provider_calls_added", False)),
            "mandatory_api_key_required": _safe_policy_bool(no_spend.get("mandatory_api_key_required", False)),
            "heavy_ml_training_added": _safe_policy_bool(no_spend.get("heavy_ml_training_added", False)),
        },
        "forbidden_features": list(payload.get("forbidden_features") or [])[:cap],
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
        "raw_payload_included": False,
        "raw_payload_exposed": False,
        "secrets_included": False,
        "compact_response": True,
    }


def compact_baseball_impact_diagnostics_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    data = payload.get("data_availability") if isinstance(payload.get("data_availability"), dict) else {}
    run_value = payload.get("run_value_impact") if isinstance(payload.get("run_value_impact"), dict) else {}
    pitcher = payload.get("pitcher_impact") if isinstance(payload.get("pitcher_impact"), dict) else {}
    batter = payload.get("batter_impact") if isinstance(payload.get("batter_impact"), dict) else {}
    matchup = payload.get("matchup_context") if isinstance(payload.get("matchup_context"), dict) else {}
    lineup = payload.get("lineup_context") if isinstance(payload.get("lineup_context"), dict) else {}
    bullpen = payload.get("bullpen_context") if isinstance(payload.get("bullpen_context"), dict) else {}
    park = payload.get("park_weather_umpire_context") if isinstance(payload.get("park_weather_umpire_context"), dict) else {}
    defense = payload.get("defense_baserunning_context") if isinstance(payload.get("defense_baserunning_context"), dict) else {}
    availability = payload.get("availability_context") if isinstance(payload.get("availability_context"), dict) else {}
    incentive = payload.get("incentive_context") if isinstance(payload.get("incentive_context"), dict) else {}
    market = payload.get("market_relevance") if isinstance(payload.get("market_relevance"), dict) else {}
    calibration = payload.get("calibration") if isinstance(payload.get("calibration"), dict) else {}
    red_team = payload.get("red_team") if isinstance(payload.get("red_team"), dict) else {}
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "baseball_player_impact_complete"),
        "sport": payload.get("sport"),
        "market_type": payload.get("market_type"),
        "data_tier": int(payload.get("data_tier", 0) or 0),
        "tier_name": payload.get("tier_name"),
        "team_level_allowed": bool(payload.get("team_level_allowed", False)),
        "pitcher_level_allowed": bool(payload.get("pitcher_level_allowed", False)),
        "batter_level_allowed": bool(payload.get("batter_level_allowed", False)),
        "tracking_level_allowed": bool(payload.get("tracking_level_allowed", False)),
        "baseball_impact_score": payload.get("baseball_impact_score", 0.0),
        "recommended_review_status": payload.get("recommended_review_status"),
        "run_value_impact": _compact_baseball_section(
            run_value,
            [
                "run_value_score",
                "pitch_level_score",
                "plate_appearance_score",
                "team_offense_score",
                "team_pitching_score",
                "first_five_signal_score",
                "full_game_signal_score",
                "total_signal_score",
                "team_total_signal_score",
                "confidence_cap_reason",
                "insufficient_sample",
                "limited_proxy",
                "run_value_fabricated",
                "missing_inputs",
            ],
            cap,
        ),
        "pitcher_impact": _compact_baseball_section(
            pitcher,
            [
                "pitcher_role",
                "pitcher_impact_score",
                "strikeout_skill_score",
                "command_score",
                "contact_suppression_score",
                "home_run_risk_score",
                "pitch_mix_quality_score",
                "workload_fatigue_score",
                "times_through_order_risk",
                "pitcher_market_relevance",
                "confidence_cap_reason",
                "pitch_tracking_inferred",
                "missing_pitcher_inputs",
                "no_bet_reasons",
            ],
            cap,
        ),
        "batter_impact": _compact_baseball_section(
            batter,
            [
                "batter_impact_score",
                "contact_quality_score",
                "plate_discipline_score",
                "power_score",
                "hit_probability_proxy",
                "total_bases_relevance_score",
                "home_run_relevance_score",
                "stolen_base_relevance_score",
                "strikeout_risk_score",
                "batter_market_relevance",
                "confidence_cap_reason",
                "bat_tracking_inferred",
                "missing_batter_inputs",
                "no_bet_reasons",
            ],
            cap,
        ),
        "matchup_context": _compact_baseball_section(
            matchup,
            [
                "matchup_advantage_score",
                "matchup_risk_score",
                "pitcher_matchup_score",
                "batter_matchup_score",
                "team_matchup_score",
                "mismatch_reasons",
                "no_bet_reasons",
                "market_specific_matchup_notes",
                "first_five_relevance",
                "full_game_relevance",
                "player_prop_relevance",
                "batter_vs_pitcher_history_weight",
                "missing_inputs",
            ],
            cap,
        ),
        "lineup_context": _compact_baseball_section(
            lineup,
            ["lineup_quality_score", "lineup_stability_score", "plate_appearance_projection_confidence", "run_environment_modifier", "prop_volume_modifier", "confidence_cap_reason", "missing_inputs", "no_bet_reasons"],
            cap,
        ),
        "bullpen_context": _compact_baseball_section(
            bullpen,
            ["bullpen_quality_score", "bullpen_fatigue_score", "high_leverage_availability_score", "full_game_market_modifier", "first_five_vs_full_game_split", "total_risk_modifier", "confidence_cap_reason", "missing_inputs", "no_bet_reasons"],
            cap,
        ),
        "park_weather_umpire_context": _compact_baseball_section(
            park,
            ["park_run_environment_score", "home_run_environment_score", "weather_run_modifier", "pitcher_prop_weather_modifier", "batter_prop_weather_modifier", "umpire_zone_modifier", "total_market_modifier", "roof_uncertainty_reduced", "confidence_cap_reason", "missing_inputs", "no_bet_reasons"],
            cap,
        ),
        "defense_baserunning_context": _compact_baseball_section(
            defense,
            ["defense_impact_score", "baserunning_impact_score", "catcher_run_prevention_score", "stolen_base_relevance_score", "pitcher_support_modifier", "total_market_modifier", "confidence_cap_reason", "missing_inputs", "no_bet_reasons"],
            cap,
        ),
        "availability_context": _compact_baseball_section(
            availability,
            ["availability_score", "role_stability_score", "starter_certainty_score", "workload_fatigue_score", "lineup_rest_risk_score", "travel_schedule_risk_score", "weather_delay_risk_score", "confidence_cap_reason", "missing_inputs", "no_bet_reasons"],
            cap,
        ),
        "incentive_context": _compact_baseball_section(
            incentive,
            ["incentive_context_status", "incentive_behavior_score", "stat_chase_risk", "team_alignment_score", "narrative_overfit_risk", "confidence_modifier", "market_relevance_modifier", "bonus_threshold_fabricated", "incentive_is_standalone_edge", "no_bet_reasons", "missing_inputs"],
            cap,
        ),
        "market_relevance": _compact_baseball_section(
            market,
            ["market_relevance_scores", "strongest_market_links", "weak_market_links", "no_bet_market_reasons", "pitcher_prop_relevance", "batter_prop_relevance", "team_market_relevance", "market_confidence_caps", "selected_market_type", "selected_market_relevance_score"],
            cap,
        ),
        "calibration_status": payload.get("calibration_status", calibration.get("calibration_status", "insufficient_data")),
        "calibration": _compact_baseball_section(
            calibration,
            ["calibration_status", "sample_size", "matched_outcomes_count", "insufficient_sample", "hit_rate", "false_positive_rate", "confidence_cap", "next_required_data", "calibration_buckets"],
            cap,
        ),
        "data_availability": _compact_baseball_section(
            data,
            ["status", "sport", "data_tier", "tier_name", "team_level_allowed", "pitcher_level_allowed", "batter_level_allowed", "tracking_level_allowed", "calibration_allowed", "available_field_groups", "missing_field_groups", "confidence_cap", "confidence_cap_reason", "no_fabrication", "next_data_to_collect"],
            cap,
        ),
        "red_team": _compact_baseball_section(
            red_team,
            ["red_team_status", "downgrade_score", "recommended_action_adjustment", "no_bet_reasons", "red_team_reasons", "missing_inputs", "confidence_cap_reason", "red_team_only"],
            cap,
        ),
        "recommended_action_adjustment": payload.get("recommended_action_adjustment"),
        "markets_to_review": list(payload.get("markets_to_review") or [])[:cap],
        "no_bet_reasons": list(payload.get("no_bet_reasons") or [])[:cap],
        "missing_inputs": list(payload.get("missing_inputs") or [])[:cap],
        "next_data_to_collect": list(payload.get("next_data_to_collect") or [])[:cap],
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
        "raw_payload_included": False,
        "raw_payload_exposed": False,
        "secrets_included": False,
        "compact_response": True,
    }


def _compact_golf_section(section: Any, keys: list[str], limit: int = 10) -> dict[str, Any]:
    row = section if isinstance(section, dict) else {}
    out: dict[str, Any] = {}
    for key in keys:
        value = row.get(key)
        if isinstance(value, list):
            out[key] = value[:limit]
        elif isinstance(value, dict):
            out[key] = redact_and_limit_payload(value, limit=limit)
        else:
            out[key] = value
    return out


def compact_golf_impact_readiness_response(payload: dict[str, Any], limit: int = 50) -> dict[str, Any]:
    cap = max(1, min(int(limit or 50), 100))
    no_spend = payload.get("no_spend_policy") if isinstance(payload.get("no_spend_policy"), dict) else {}
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "golf_impact_readiness"),
        "supported_sports": list(payload.get("supported_sports") or [])[:cap],
        "supported_skill_groups": list(payload.get("supported_skill_groups") or [])[:cap],
        "supported_markets": list(payload.get("supported_markets") or [])[:cap],
        "data_tier_requirements": redact_and_limit_payload(payload.get("data_tier_requirements") or {}, limit=cap),
        "golf_readiness": redact_and_limit_payload(payload.get("golf_readiness") or {}, limit=cap),
        "missing_data_by_market": redact_and_limit_payload(payload.get("missing_data_by_market") or {}, limit=cap),
        "calibration_requirements": list(payload.get("calibration_requirements") or [])[:cap],
        "no_spend_policy": {
            "paid_provider_required": _safe_policy_bool(no_spend.get("paid_provider_required", False)),
            "new_provider_calls_added": _safe_policy_bool(no_spend.get("new_provider_calls_added", False)),
            "mandatory_api_key_required": _safe_policy_bool(no_spend.get("mandatory_api_key_required", False)),
            "heavy_ml_training_added": _safe_policy_bool(no_spend.get("heavy_ml_training_added", False)),
            "model_training_added": _safe_policy_bool(no_spend.get("model_training_added", False)),
        },
        "forbidden_features": list(payload.get("forbidden_features") or [])[:cap],
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
        "raw_payload_included": False,
        "raw_payload_exposed": False,
        "secrets_included": False,
        "compact_response": True,
    }


def compact_golf_impact_diagnostics_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    data = payload.get("data_availability") if isinstance(payload.get("data_availability"), dict) else {}
    sg = payload.get("strokes_gained_impact") if isinstance(payload.get("strokes_gained_impact"), dict) else {}
    off_tee = payload.get("off_tee_impact") if isinstance(payload.get("off_tee_impact"), dict) else {}
    approach = payload.get("approach_impact") if isinstance(payload.get("approach_impact"), dict) else {}
    short_game = payload.get("short_game_putting_context") if isinstance(payload.get("short_game_putting_context"), dict) else {}
    course = payload.get("course_fit_context") if isinstance(payload.get("course_fit_context"), dict) else {}
    weather = payload.get("weather_wave_context") if isinstance(payload.get("weather_wave_context"), dict) else {}
    field = payload.get("field_tournament_context") if isinstance(payload.get("field_tournament_context"), dict) else {}
    availability = payload.get("availability_context") if isinstance(payload.get("availability_context"), dict) else {}
    incentive = payload.get("incentive_context") if isinstance(payload.get("incentive_context"), dict) else {}
    market = payload.get("market_relevance") if isinstance(payload.get("market_relevance"), dict) else {}
    calibration = payload.get("calibration") if isinstance(payload.get("calibration"), dict) else {}
    red_team = payload.get("red_team") if isinstance(payload.get("red_team"), dict) else {}
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "golf_strokes_gained_impact_complete"),
        "sport": payload.get("sport"),
        "market_type": payload.get("market_type"),
        "data_tier": int(payload.get("data_tier", 0) or 0),
        "tier_name": payload.get("tier_name"),
        "player_level_allowed": bool(payload.get("player_level_allowed", False)),
        "course_fit_allowed": bool(payload.get("course_fit_allowed", False)),
        "weather_wave_allowed": bool(payload.get("weather_wave_allowed", False)),
        "simulation_allowed": bool(payload.get("simulation_allowed", False)),
        "golf_impact_score": payload.get("golf_impact_score", 0.0),
        "recommended_review_status": payload.get("recommended_review_status"),
        "strokes_gained_impact": _compact_golf_section(
            sg,
            [
                "strokes_gained_score",
                "tee_to_green_score",
                "ball_striking_score",
                "short_game_score",
                "putting_score",
                "scoring_score",
                "birdie_bogey_score",
                "cut_made_profile_score",
                "volatility_score",
                "recent_vs_baseline_delta",
                "confidence_cap_reason",
                "insufficient_sample",
                "limited_proxy",
                "sg_splits_fabricated",
                "missing_inputs",
            ],
            cap,
        ),
        "off_tee_impact": _compact_golf_section(
            off_tee,
            [
                "off_tee_score",
                "distance_advantage_score",
                "accuracy_score",
                "dispersion_risk_score",
                "penalty_avoidance_score",
                "course_off_tee_fit_score",
                "driving_prop_relevance",
                "course_fit_confidence_capped",
                "dispersion_inferred",
                "missing_inputs",
                "no_bet_reasons",
            ],
            cap,
        ),
        "approach_impact": _compact_golf_section(
            approach,
            [
                "approach_score",
                "distance_bucket_fit_score",
                "proximity_score",
                "gir_relevance_score",
                "scoring_opportunity_score",
                "course_approach_fit_score",
                "approach_prop_relevance",
                "distance_bucket_fit_supported",
                "sg_approach_fabricated",
                "missing_inputs",
                "no_bet_reasons",
            ],
            cap,
        ),
        "short_game_putting_context": _compact_golf_section(
            short_game,
            [
                "short_game_score",
                "scrambling_score",
                "bunker_score",
                "putting_score",
                "grass_fit_score",
                "three_putt_risk_score",
                "putting_volatility_score",
                "score_save_modifier",
                "sg_putting_fabricated",
                "grass_fit_fabricated",
                "missing_inputs",
                "no_bet_reasons",
            ],
            cap,
        ),
        "course_fit_context": _compact_golf_section(
            course,
            [
                "course_fit_score",
                "architecture_fit_score",
                "distance_bucket_fit_score",
                "grass_surface_fit_score",
                "hazard_risk_score",
                "comp_course_fit_score",
                "course_history_relevance",
                "course_architecture_fabricated",
                "grass_type_fabricated",
                "missing_inputs",
                "no_bet_reasons",
            ],
            cap,
        ),
        "weather_wave_context": _compact_golf_section(
            weather,
            [
                "weather_impact_score",
                "wave_draw_score",
                "wind_fit_score",
                "delay_risk_score",
                "scoring_condition_modifier",
                "round_score_modifier",
                "market_confidence_modifier",
                "tee_time_wave_fabricated",
                "weather_wave_edge_fabricated",
                "missing_inputs",
                "no_bet_reasons",
            ],
            cap,
        ),
        "field_tournament_context": _compact_golf_section(
            field,
            [
                "field_strength_score",
                "tournament_format_score",
                "cut_rule_context_score",
                "cut_risk_modifier",
                "top_finish_market_modifier",
                "outright_market_modifier",
                "travel_fatigue_risk_score",
                "unsupported_format",
                "missing_inputs",
                "no_bet_reasons",
            ],
            cap,
        ),
        "availability_context": _compact_golf_section(
            availability,
            [
                "availability_score",
                "withdrawal_risk_score",
                "injury_risk_score",
                "travel_fatigue_score",
                "schedule_load_score",
                "change_uncertainty_score",
                "confidence_cap_reason",
                "injury_status_fabricated",
                "missing_inputs",
                "no_bet_reasons",
            ],
            cap,
        ),
        "incentive_context": _compact_golf_section(
            incentive,
            [
                "incentive_context_status",
                "incentive_behavior_score",
                "motivation_alignment_score",
                "narrative_overfit_risk",
                "withdrawal_or_tuneup_risk",
                "confidence_modifier",
                "market_relevance_modifier",
                "incentive_is_standalone_edge",
                "motivation_fabricated",
                "missing_inputs",
                "no_bet_reasons",
            ],
            cap,
        ),
        "market_relevance": _compact_golf_section(
            market,
            [
                "market_relevance_scores",
                "strongest_market_links",
                "weak_market_links",
                "no_bet_market_reasons",
                "outright_relevance",
                "top_finish_relevance",
                "cut_market_relevance",
                "matchup_relevance",
                "round_market_relevance",
                "player_prop_relevance",
                "market_confidence_caps",
                "selected_market_type",
                "selected_market_relevance_score",
            ],
            cap,
        ),
        "calibration_status": payload.get("calibration_status", calibration.get("calibration_status", "insufficient_data")),
        "calibration": _compact_golf_section(
            calibration,
            ["calibration_status", "sample_size", "matched_outcomes_count", "insufficient_sample", "hit_rate", "false_positive_rate", "confidence_cap", "next_required_data", "calibration_buckets", "outright_extra_conservative"],
            cap,
        ),
        "data_availability": _compact_golf_section(
            data,
            ["status", "sport", "data_tier", "tier_name", "player_level_allowed", "course_fit_allowed", "weather_wave_allowed", "simulation_allowed", "calibration_allowed", "available_field_groups", "missing_field_groups", "confidence_cap", "confidence_cap_reason", "no_fabrication", "next_data_to_collect"],
            cap,
        ),
        "red_team": _compact_golf_section(
            red_team,
            ["red_team_status", "downgrade_score", "recommended_action_adjustment", "no_bet_reasons", "red_team_reasons", "missing_inputs", "confidence_cap_reason", "red_team_only"],
            cap,
        ),
        "recommended_action_adjustment": payload.get("recommended_action_adjustment"),
        "markets_to_review": list(payload.get("markets_to_review") or [])[:cap],
        "no_bet_reasons": list(payload.get("no_bet_reasons") or [])[:cap],
        "missing_inputs": list(payload.get("missing_inputs") or [])[:cap],
        "next_data_to_collect": list(payload.get("next_data_to_collect") or [])[:cap],
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
        "raw_payload_included": False,
        "raw_payload_exposed": False,
        "secrets_included": False,
        "compact_response": True,
    }


def _compact_combat_section(section: Any, keys: list[str], limit: int = 10) -> dict[str, Any]:
    row = section if isinstance(section, dict) else {}
    out: dict[str, Any] = {}
    for key in keys:
        value = row.get(key)
        if isinstance(value, list):
            out[key] = value[:limit]
        elif isinstance(value, dict):
            out[key] = redact_and_limit_payload(value, limit=limit)
        else:
            out[key] = value
    return out


def compact_combat_impact_readiness_response(payload: dict[str, Any], limit: int = 50) -> dict[str, Any]:
    cap = max(1, min(int(limit or 50), 100))
    no_spend = payload.get("no_spend_policy") if isinstance(payload.get("no_spend_policy"), dict) else {}
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "combat_impact_readiness"),
        "supported_sports": list(payload.get("supported_sports") or [])[:cap],
        "supported_markets": list(payload.get("supported_markets") or [])[:cap],
        "supported_phases": list(payload.get("supported_phases") or [])[:cap],
        "data_tier_requirements": redact_and_limit_payload(payload.get("data_tier_requirements") or {}, limit=cap),
        "mma_readiness": redact_and_limit_payload(payload.get("mma_readiness") or {}, limit=cap),
        "ufc_readiness": redact_and_limit_payload(payload.get("ufc_readiness") or {}, limit=cap),
        "boxing_readiness": redact_and_limit_payload(payload.get("boxing_readiness") or {}, limit=cap),
        "missing_data_by_market": redact_and_limit_payload(payload.get("missing_data_by_market") or {}, limit=cap),
        "calibration_requirements": list(payload.get("calibration_requirements") or [])[:cap],
        "no_spend_policy": {
            "paid_provider_required": _safe_policy_bool(no_spend.get("paid_provider_required", False)),
            "new_api_keys_required": _safe_policy_bool(no_spend.get("new_api_keys_required", False)),
            "film_tracking_optional": _safe_policy_bool(no_spend.get("film_tracking_optional", True)),
            "external_provider_calls_in_tests": _safe_policy_bool(no_spend.get("external_provider_calls_in_tests", False)),
        },
        "forbidden_features": list(payload.get("forbidden_features") or [])[:cap],
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
        "raw_payload_included": False,
        "raw_payload_exposed": False,
        "secrets_included": False,
        "compact_response": True,
    }


def compact_combat_impact_diagnostics_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    data = payload.get("data_availability") if isinstance(payload.get("data_availability"), dict) else {}
    market = payload.get("market_relevance") if isinstance(payload.get("market_relevance"), dict) else {}
    calibration = payload.get("calibration") if isinstance(payload.get("calibration"), dict) else {}
    red_team = payload.get("red_team") if isinstance(payload.get("red_team"), dict) else {}
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "combat_phase_control_impact_complete"),
        "sport": payload.get("sport"),
        "market_type": payload.get("market_type"),
        "data_tier": int(payload.get("data_tier", 0) or 0),
        "tier_name": payload.get("tier_name"),
        "fighter_level_allowed": bool(payload.get("fighter_level_allowed", False)),
        "phase_control_allowed": bool(payload.get("phase_control_allowed", False)),
        "damage_durability_allowed": bool(payload.get("damage_durability_allowed", False)),
        "judging_referee_allowed": bool(payload.get("judging_referee_allowed", False)),
        "combat_impact_score": payload.get("combat_impact_score", 0.0),
        "recommended_review_status": payload.get("recommended_review_status"),
        "striking_impact": _compact_combat_section(payload.get("striking_impact"), ["striking_impact_score", "volume_score", "accuracy_score", "defense_score", "power_score", "knockdown_threat_score", "damage_absorption_risk_score", "boxing_punch_profile_score", "striking_prop_relevance", "ko_tko_relevance_modifier", "over_under_rounds_modifier", "insufficient_sample", "limited_proxy", "punch_tracking_fabricated", "missing_inputs", "no_bet_reasons"], cap),
        "grappling_control_impact": _compact_combat_section(payload.get("grappling_control_impact"), ["grappling_impact_score", "takedown_threat_score", "takedown_defense_score", "control_time_score", "top_control_score", "bottom_survival_score", "scramble_score", "submission_threat_score", "submission_defense_score", "ground_damage_score", "grappling_prop_relevance", "submission_relevance_modifier", "decision_relevance_modifier", "control_time_fabricated", "submission_quality_fabricated", "missing_inputs", "no_bet_reasons"], cap),
        "phase_control_context": _compact_combat_section(payload.get("phase_control_context"), ["phase_control_score", "preferred_phase", "fighter_a_phase_edges", "fighter_b_phase_edges", "phase_volatility_score", "phase_mismatch_reasons", "market_relevance_modifier", "phase_control_fabricated", "missing_inputs", "no_bet_reasons"], cap),
        "damage_durability_context": _compact_combat_section(payload.get("damage_durability_context"), ["damage_threat_score", "durability_risk_score", "chin_risk_score", "body_damage_risk_score", "leg_damage_risk_score", "cut_stoppage_risk_score", "doctor_stoppage_risk_score", "attritional_damage_score", "finish_volatility_score", "durability_fabricated", "medical_suspension_fabricated", "missing_inputs", "no_bet_reasons"], cap),
        "pace_cardio_context": _compact_combat_section(payload.get("pace_cardio_context"), ["pace_score", "cardio_score", "round_progression_score", "late_fight_risk_score", "five_round_readiness_score", "gas_tank_warning_score", "over_under_rounds_modifier", "late_finish_relevance", "round_decline_fabricated", "weight_cut_fabricated", "missing_inputs", "no_bet_reasons"], cap),
        "matchup_context": _compact_combat_section(payload.get("matchup_context"), ["matchup_advantage_score", "matchup_risk_score", "striking_matchup_score", "grappling_matchup_score", "phase_matchup_score", "durability_matchup_score", "cardio_matchup_score", "tactical_mismatch_reasons", "market_specific_matchup_notes", "stance_fabricated", "reach_fabricated", "no_bet_reasons"], cap),
        "availability_context": _compact_combat_section(payload.get("availability_context"), ["availability_score", "injury_risk_score", "weight_cut_risk_score", "short_notice_risk_score", "layoff_risk_score", "camp_stability_score", "age_curve_risk_score", "fight_week_stability_score", "confidence_cap_reason", "injury_status_fabricated", "weight_cut_fabricated", "camp_context_fabricated", "health_fabricated", "missing_inputs", "no_bet_reasons"], cap),
        "ruleset_referee_judging_context": _compact_combat_section(payload.get("ruleset_referee_judging_context"), ["ruleset_context_score", "five_round_context_score", "referee_stoppage_modifier", "referee_standup_modifier", "judging_volatility_score", "decision_market_risk_score", "draw_or_split_decision_risk_score", "ruleset", "referee_tendency_fabricated", "judge_tendency_fabricated", "missing_inputs", "no_bet_reasons"], cap),
        "incentive_context": _compact_combat_section(payload.get("incentive_context"), ["incentive_context_status", "incentive_behavior_score", "motivation_alignment_score", "finish_chase_risk", "narrative_overfit_risk", "retirement_or_shutdown_risk", "confidence_modifier", "market_relevance_modifier", "incentive_is_standalone_edge", "no_bet_reasons"], cap),
        "market_relevance": _compact_combat_section(market, ["market_relevance_scores", "strongest_market_links", "weak_market_links", "no_bet_market_reasons", "moneyline_relevance", "method_relevance", "round_total_relevance", "distance_relevance", "fighter_prop_relevance", "boxing_prop_relevance", "market_confidence_caps", "selected_market_type", "selected_market_relevance_score"], cap),
        "calibration_status": payload.get("calibration_status", calibration.get("calibration_status", "insufficient_data")),
        "calibration": _compact_combat_section(calibration, ["calibration_status", "sample_size", "matched_outcomes_count", "insufficient_sample", "hit_rate", "false_positive_rate", "confidence_cap", "exact_round_extra_conservative", "split_decision_extra_conservative", "next_required_data", "calibration_buckets"], cap),
        "data_availability": _compact_combat_section(data, ["status", "sport", "data_tier", "tier_name", "fighter_level_allowed", "striking_level_allowed", "grappling_level_allowed", "phase_control_allowed", "damage_durability_allowed", "judging_referee_allowed", "calibration_allowed", "available_field_groups", "missing_field_groups", "confidence_cap", "confidence_cap_reason", "no_fabrication", "phase_control_not_fabricated", "punch_tracking_not_fabricated", "grappling_control_not_fabricated", "durability_not_fabricated", "injury_status_not_fabricated", "weight_cut_not_fabricated", "camp_context_not_fabricated", "referee_tendency_not_fabricated", "judge_tendency_not_fabricated", "next_data_to_collect"], cap),
        "red_team": _compact_combat_section(red_team, ["red_team_status", "downgrade_score", "recommended_action_adjustment", "no_bet_reasons", "red_team_reasons", "missing_inputs", "confidence_cap_reason", "red_team_only"], cap),
        "markets_to_review": list(payload.get("markets_to_review") or [])[:cap],
        "no_bet_reasons": list(payload.get("no_bet_reasons") or [])[:cap],
        "missing_inputs": list(payload.get("missing_inputs") or [])[:cap],
        "next_data_to_collect": list(payload.get("next_data_to_collect") or [])[:cap],
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
        "raw_payload_included": False,
        "raw_payload_exposed": False,
        "secrets_included": False,
        "compact_response": True,
    }


def _compact_tennis_section(section: Any, keys: list[str], limit: int = 10) -> dict[str, Any]:
    row = section if isinstance(section, dict) else {}
    out: dict[str, Any] = {}
    for key in keys:
        value = row.get(key)
        if isinstance(value, list):
            out[key] = value[:limit]
        elif isinstance(value, dict):
            out[key] = redact_and_limit_payload(value, limit=limit)
        else:
            out[key] = value
    return out


def compact_tennis_impact_readiness_response(payload: dict[str, Any], limit: int = 50) -> dict[str, Any]:
    cap = max(1, min(int(limit or 50), 100))
    no_spend = payload.get("no_spend_policy") if isinstance(payload.get("no_spend_policy"), dict) else {}
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "tennis_impact_readiness"),
        "supported_sports": list(payload.get("supported_sports") or [])[:cap],
        "supported_markets": list(payload.get("supported_markets") or [])[:cap],
        "supported_contexts": list(payload.get("supported_contexts") or [])[:cap],
        "data_tier_requirements": redact_and_limit_payload(payload.get("data_tier_requirements") or {}, limit=cap),
        "tennis_readiness": redact_and_limit_payload(payload.get("tennis_readiness") or {}, limit=cap),
        "atp_readiness": redact_and_limit_payload(payload.get("atp_readiness") or {}, limit=cap),
        "wta_readiness": redact_and_limit_payload(payload.get("wta_readiness") or {}, limit=cap),
        "missing_data_by_market": redact_and_limit_payload(payload.get("missing_data_by_market") or {}, limit=cap),
        "calibration_requirements": list(payload.get("calibration_requirements") or [])[:cap],
        "no_spend_policy": {
            "paid_provider_required": _safe_policy_bool(no_spend.get("paid_provider_required", False)),
            "new_provider_calls_added": _safe_policy_bool(no_spend.get("new_provider_calls_added", False)),
            "mandatory_api_key_required": _safe_policy_bool(no_spend.get("mandatory_api_key_required", False)),
            "heavy_ml_training_added": _safe_policy_bool(no_spend.get("heavy_ml_training_added", False)),
            "model_training_added": _safe_policy_bool(no_spend.get("model_training_added", False)),
        },
        "forbidden_features": list(payload.get("forbidden_features") or [])[:cap],
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
        "raw_payload_included": False,
        "raw_payload_exposed": False,
        "secrets_included": False,
        "compact_response": True,
    }


def compact_tennis_impact_diagnostics_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    data = payload.get("data_availability") if isinstance(payload.get("data_availability"), dict) else {}
    serve = payload.get("serve_impact") if isinstance(payload.get("serve_impact"), dict) else {}
    ret = payload.get("return_impact") if isinstance(payload.get("return_impact"), dict) else {}
    surface = payload.get("surface_context") if isinstance(payload.get("surface_context"), dict) else {}
    fmt = payload.get("format_markov_context") if isinstance(payload.get("format_markov_context"), dict) else {}
    matchup = payload.get("matchup_context") if isinstance(payload.get("matchup_context"), dict) else {}
    pressure = payload.get("pressure_tiebreak_context") if isinstance(payload.get("pressure_tiebreak_context"), dict) else {}
    availability = payload.get("availability_context") if isinstance(payload.get("availability_context"), dict) else {}
    incentive = payload.get("incentive_context") if isinstance(payload.get("incentive_context"), dict) else {}
    market = payload.get("market_relevance") if isinstance(payload.get("market_relevance"), dict) else {}
    calibration = payload.get("calibration") if isinstance(payload.get("calibration"), dict) else {}
    red_team = payload.get("red_team") if isinstance(payload.get("red_team"), dict) else {}
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "tennis_serve_return_impact_complete"),
        "sport": payload.get("sport"),
        "market_type": payload.get("market_type"),
        "data_tier": int(payload.get("data_tier", 0) or 0),
        "tier_name": payload.get("tier_name"),
        "player_level_allowed": bool(payload.get("player_level_allowed", False)),
        "serve_return_allowed": bool(payload.get("serve_return_allowed", False)),
        "surface_matchup_allowed": bool(payload.get("surface_matchup_allowed", False)),
        "point_level_allowed": bool(payload.get("point_level_allowed", False)),
        "tracking_level_allowed": bool(payload.get("tracking_level_allowed", False)),
        "tennis_impact_score": payload.get("tennis_impact_score", 0.0),
        "recommended_review_status": payload.get("recommended_review_status"),
        "serve_impact": _compact_tennis_section(
            serve,
            ["serve_impact_score", "hold_stability_score", "first_serve_score", "second_serve_resilience_score", "ace_pressure_score", "double_fault_risk_score", "break_point_save_score", "service_game_volatility_score", "surface_adjusted_serve_score", "ace_prop_relevance", "double_fault_prop_relevance", "total_games_modifier", "serve_placement_fabricated", "serve_speed_fabricated", "confidence_cap_reason", "insufficient_sample", "limited_proxy", "missing_inputs", "no_bet_reasons"],
            cap,
        ),
        "return_impact": _compact_tennis_section(
            ret,
            ["return_impact_score", "break_threat_score", "first_serve_return_score", "second_serve_attack_score", "break_point_conversion_score", "return_pressure_score", "return_game_volatility_score", "surface_adjusted_return_score", "break_prop_relevance", "under_total_modifier", "game_handicap_modifier", "return_depth_fabricated", "confidence_cap_reason", "insufficient_sample", "limited_proxy", "missing_inputs", "no_bet_reasons"],
            cap,
        ),
        "surface_context": _compact_tennis_section(
            surface,
            ["surface_fit_score", "court_speed_fit_score", "indoor_outdoor_fit_score", "altitude_conditions_score", "surface_hold_break_modifier", "total_games_surface_modifier", "tiebreak_surface_modifier", "court_speed_fabricated", "ball_type_fabricated", "weather_conditions_fabricated", "missing_inputs", "no_bet_reasons"],
            cap,
        ),
        "format_markov_context": _compact_tennis_section(
            fmt,
            ["markov_context_score", "hold_break_balance_score", "match_win_relevance_score", "set_market_relevance_score", "total_games_relevance_score", "tiebreak_relevance_score", "correct_score_relevance_score", "game_handicap_relevance_score", "format_confidence_cap", "best_of", "markov_distribution_fabricated", "limited_proxy", "insufficient_sample", "missing_inputs", "no_bet_reasons"],
            cap,
        ),
        "matchup_context": _compact_tennis_section(
            matchup,
            ["matchup_advantage_score", "matchup_risk_score", "serve_matchup_score", "return_matchup_score", "rally_matchup_score", "handedness_matchup_score", "handedness_fabricated", "shot_pattern_fabricated", "head_to_head_weight", "tactical_mismatch_reasons", "no_bet_reasons", "market_specific_matchup_notes", "moneyline_relevance", "total_games_relevance", "handicap_relevance", "player_prop_relevance", "missing_inputs"],
            cap,
        ),
        "pressure_tiebreak_context": _compact_tennis_section(
            pressure,
            ["pressure_score", "break_point_pressure_score", "tiebreak_skill_score", "tiebreak_likelihood_modifier", "first_set_pressure_score", "close_set_volatility_score", "pressure_confidence_cap", "clutch_is_standalone_edge", "missing_inputs", "no_bet_reasons"],
            cap,
        ),
        "availability_context": _compact_tennis_section(
            availability,
            ["availability_score", "injury_risk_score", "retirement_risk_score", "fatigue_score", "schedule_load_score", "travel_adjustment_score", "surface_transition_risk_score", "confidence_cap_reason", "injury_status_fabricated", "retirement_risk_fabricated", "missing_inputs", "no_bet_reasons"],
            cap,
        ),
        "incentive_context": _compact_tennis_section(
            incentive,
            ["incentive_context_status", "incentive_behavior_score", "motivation_alignment_score", "narrative_overfit_risk", "retirement_or_shutdown_risk", "confidence_modifier", "market_relevance_modifier", "incentive_is_standalone_edge", "motivation_fabricated", "missing_inputs", "no_bet_reasons"],
            cap,
        ),
        "market_relevance": _compact_tennis_section(
            market,
            ["market_relevance_scores", "strongest_market_links", "weak_market_links", "no_bet_market_reasons", "moneyline_relevance", "handicap_relevance", "total_games_relevance", "set_market_relevance", "tiebreak_relevance", "player_prop_relevance", "selected_market_type", "selected_market_relevance_score", "market_confidence_caps"],
            cap,
        ),
        "calibration_status": payload.get("calibration_status", calibration.get("calibration_status", "insufficient_data")),
        "calibration": _compact_tennis_section(
            calibration,
            ["calibration_status", "sample_size", "matched_outcomes_count", "insufficient_sample", "hit_rate", "false_positive_rate", "confidence_cap", "next_required_data", "calibration_buckets", "correct_score_extra_conservative", "tiebreak_extra_conservative"],
            cap,
        ),
        "data_availability": _compact_tennis_section(
            data,
            ["status", "sport", "data_tier", "tier_name", "player_level_allowed", "serve_return_allowed", "surface_matchup_allowed", "point_level_allowed", "tracking_level_allowed", "calibration_allowed", "available_field_groups", "missing_field_groups", "confidence_cap", "confidence_cap_reason", "no_fabrication", "next_data_to_collect"],
            cap,
        ),
        "red_team": _compact_tennis_section(
            red_team,
            ["red_team_status", "downgrade_score", "recommended_action_adjustment", "no_bet_reasons", "red_team_reasons", "missing_inputs", "confidence_cap_reason", "red_team_only"],
            cap,
        ),
        "markets_to_review": list(payload.get("markets_to_review") or [])[:cap],
        "no_bet_reasons": list(payload.get("no_bet_reasons") or [])[:cap],
        "missing_inputs": list(payload.get("missing_inputs") or [])[:cap],
        "next_data_to_collect": list(payload.get("next_data_to_collect") or [])[:cap],
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
        "raw_payload_included": False,
        "raw_payload_exposed": False,
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
                "review_queue_effect": row.get("review_queue_effect"),
                "ranking_effect": row.get("ranking_effect"),
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


def compact_basketball_player_impact_readiness_response(payload: dict[str, Any], limit: int = 20) -> dict[str, Any]:
    cap = max(1, min(int(limit or 20), 100))
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "basketball_player_impact_readiness"),
        "supported_sports": list(payload.get("supported_sports") or [])[:cap],
        "feasible_now": list(payload.get("feasible_now") or [])[:cap],
        "not_implemented": list(payload.get("not_implemented") or [])[:cap],
        "possession_impact_ready": bool(payload.get("possession_impact_ready", False)),
        "tracking_opportunity_ready": bool(payload.get("tracking_opportunity_ready", False)),
        "role_context_ready": bool(payload.get("role_context_ready", False)),
        "lineup_matchup_ready": bool(payload.get("lineup_matchup_ready", False)),
        "availability_minutes_ready": bool(payload.get("availability_minutes_ready", False)),
        "incentive_context_ready": bool(payload.get("incentive_context_ready", False)),
        "market_relevance_ready": bool(payload.get("market_relevance_ready", False)),
        "calibration_ready": bool(payload.get("calibration_ready", False)),
        "red_team_ready": bool(payload.get("red_team_ready", False)),
        "sport_contracts": _redact(payload.get("sport_contracts") if isinstance(payload.get("sport_contracts"), dict) else {}),
        "next_required_data": list(payload.get("next_required_data") or [])[:cap],
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "owner_approval_required": True,
        "sportsbook_bet_execution_enabled": False,
        "raw_payload_included": False,
        "raw_payload_exposed": False,
        "secrets_included": False,
        "secrets_detected": False,
        "compact_response": True,
    }


def _compact_basketball_submodule(payload: dict[str, Any] | None, keys: list[str]) -> dict[str, Any]:
    row = payload if isinstance(payload, dict) else {}
    out = {key: row.get(key) for key in keys if key in row}
    for key in list(out):
        if isinstance(out[key], list):
            out[key] = out[key][:20]
    out.update(
        {
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "auto_execution": False,
            "human_approval_required": True,
            "owner_approval_required": True,
        }
    )
    return _redact(out)


def compact_basketball_player_impact_response(payload: dict[str, Any], limit: int = 20) -> dict[str, Any]:
    cap = max(1, min(int(limit or 20), 100))
    market_scores = payload.get("market_relevance_scores") if isinstance(payload.get("market_relevance_scores"), dict) else {}
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "basketball_player_impact_complete"),
        "sport": payload.get("sport"),
        "league": payload.get("league"),
        "sport_contract_id": payload.get("sport_contract_id"),
        "calibration_bucket_prefix": payload.get("calibration_bucket_prefix"),
        "legacy_sport_alias": payload.get("legacy_sport_alias"),
        "player_id": payload.get("player_id"),
        "player_name_optional_redacted": payload.get("player_name_optional_redacted"),
        "team_id": payload.get("team_id"),
        "opponent_id": payload.get("opponent_id"),
        "player_impact_score": payload.get("player_impact_score", 0.0),
        "possession_impact_score": payload.get("possession_impact_score", 0.0),
        "tracking_opportunity_score": payload.get("tracking_opportunity_score", 0.0),
        "role_adjusted_efficiency_score": payload.get("role_adjusted_efficiency_score", 0.0),
        "lineup_fit_score": payload.get("lineup_fit_score", 0.0),
        "matchup_fit_score": payload.get("matchup_fit_score", 0.0),
        "availability_score": payload.get("availability_score", 0.0),
        "minutes_stability_score": payload.get("minutes_stability_score", 0.0),
        "incentive_context_score": payload.get("incentive_context_score", 0.0),
        "market_relevance_scores": dict(list(market_scores.items())[:cap]),
        "calibration_status": payload.get("calibration_status"),
        "insufficient_sample": bool(payload.get("insufficient_sample", True)),
        "recommended_review_status": payload.get("recommended_review_status"),
        "markets_to_review": list(payload.get("markets_to_review") or [])[:cap],
        "markets_to_avoid": list(payload.get("markets_to_avoid") or [])[:cap],
        "missing_inputs": list(payload.get("missing_inputs") or [])[:cap],
        "fatal_safety_violations": list(payload.get("fatal_safety_violations") or [])[:cap],
        "possession_impact": _compact_basketball_submodule(
            payload.get("possession_impact"),
            [
                "possession_impact_score",
                "offensive_possession_impact",
                "defensive_possession_impact",
                "possession_impact_confidence",
                "possession_impact_status",
                "possession_impact_missing_inputs",
            ],
        ),
        "tracking_opportunity": _compact_basketball_submodule(
            payload.get("tracking_opportunity"),
            [
                "tracking_opportunity_score",
                "touch_opportunity_score",
                "creation_opportunity_score",
                "assist_opportunity_score",
                "rebound_opportunity_score",
                "shooting_opportunity_score",
                "tracking_status",
                "tracking_missing_inputs",
            ],
        ),
        "role_context": _compact_basketball_submodule(
            payload.get("role_context"),
            [
                "player_role",
                "role_confidence",
                "role_adjusted_efficiency_score",
                "role_fit_score",
                "role_stability_score",
                "role_change_detected",
            ],
        ),
        "lineup_matchup_context": _compact_basketball_submodule(
            payload.get("lineup_matchup_context"),
            [
                "lineup_fit_score",
                "matchup_fit_score",
                "projected_minutes_context",
                "closing_lineup_probability",
                "teammate_absence_usage_shift",
                "blowout_minutes_risk",
                "pace_context_score",
                "lineup_matchup_status",
            ],
        ),
        "availability_minutes": _compact_basketball_submodule(
            payload.get("availability_minutes"),
            [
                "availability_score",
                "minutes_stability_score",
                "projected_minutes_confidence",
                "rotation_trust_score",
                "load_management_risk",
                "foul_trouble_risk",
                "injury_risk_score",
                "availability_status",
            ],
        ),
        "incentive_context": _compact_basketball_submodule(
            payload.get("incentive_context"),
            [
                "incentive_context_score",
                "incentive_usage_pressure",
                "incentive_minutes_pressure",
                "incentive_stat_chase_risk",
                "incentive_team_alignment_score",
                "incentive_market_relevance",
                "incentive_warning_flags",
                "incentive_status",
            ],
        ),
        "red_team": _compact_basketball_submodule(
            payload.get("red_team"),
            [
                "player_impact_red_team_status",
                "red_team_provider",
                "red_team_only",
                "red_team_reasons",
                "red_team_downgrade",
                "missing_data_requested",
                "approval_granted",
                "bet_slip_created",
            ],
        ),
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "owner_approval_required": True,
        "sportsbook_bet_execution_enabled": False,
        "raw_payload_included": False,
        "raw_payload_exposed": False,
        "secrets_included": False,
        "secrets_detected": False,
        "compact_response": True,
    }


def _compact_advanced_diagnostic_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": item.get("candidate_id"),
        "status": item.get("status", item.get("advanced_red_team_status")),
        "advanced_red_team_status": item.get("advanced_red_team_status"),
        "recommended_action_adjustment": item.get("recommended_action_adjustment"),
        "topological_risk": item.get("topological_risk"),
        "manifold_density": item.get("manifold_density"),
        "conformal_interval_width": item.get("conformal_interval_width"),
        "transfer_entropy_score": item.get("transfer_entropy_score"),
        "mutual_information_score": item.get("mutual_information_score"),
        "causal_graph_support": item.get("causal_graph_support"),
        "dynamical_predictability": item.get("dynamical_predictability"),
        "contrastive_edge_signal": item.get("contrastive_edge_signal"),
        "graph_cluster_density": item.get("graph_cluster_density"),
        "sparse_region_risk": item.get("sparse_region_risk"),
        "counterfactual_significance": item.get("counterfactual_significance"),
        "no_bet_reasons": list(item.get("no_bet_reasons") or [])[:20],
        "no_trade_reasons": list(item.get("no_trade_reasons") or [])[:20],
        "missing_inputs": list(item.get("missing_inputs") or [])[:20],
        "insufficient_sample": bool(item.get("insufficient_sample", False)),
        "blocked_reason": item.get("blocked_reason"),
        "deepseek_used": bool(item.get("deepseek_used", False)),
        "openai_used": bool(item.get("openai_used", False)),
        "external_ai_call_performed": bool(item.get("external_ai_call_performed", False)),
        "red_team_only": True,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "human_approval_required": True,
        "owner_approval_required": True,
        "raw_payload_included": False,
        "secrets_included": False,
    }


def compact_advanced_red_team_response(payload: dict[str, Any], limit: int = 10) -> dict[str, Any]:
    cap = max(1, min(int(limit or 10), 100))
    if not bool(payload.get("ok", True)) and payload.get("status") == "provider_not_allowed_for_red_team":
        return {
            "ok": False,
            "status": "provider_not_allowed_for_red_team",
            "allowed_ai_providers": list(payload.get("allowed_ai_providers") or ["deepseek", "openai"]),
            "default_provider": payload.get("default_provider", "deepseek"),
            "provider_write": False,
            "execution_allowed": False,
            "live_execution_enabled": False,
            "auto_execution": False,
            "human_approval_required": True,
            "owner_approval_required": True,
            "red_team_only": True,
            "raw_payload_included": False,
            "secrets_included": False,
        }
    items = [_compact_advanced_diagnostic_item(row) for row in list(payload.get("items") or []) if isinstance(row, dict)][:cap]
    if not items and ("advanced_red_team_status" in payload or "topological_risk" in payload or "provider_policy" in payload):
        items = [_compact_advanced_diagnostic_item(payload)]
    return {
        "ok": bool(payload.get("ok", True)),
        "status": payload.get("status", "advanced_red_team_report"),
        "report_id": payload.get("report_id"),
        "date": payload.get("date"),
        "candidate_count": int(payload.get("candidate_count", len(items)) or 0),
        "fake_edge_warning_count": int(payload.get("fake_edge_warning_count", 0) or 0),
        "data_insufficient_count": int(payload.get("data_insufficient_count", 0) or 0),
        "fatal_safety_blocker_count": int(payload.get("fatal_safety_blocker_count", 0) or 0),
        "recommended_action_adjustment_counts": dict(payload.get("recommended_action_adjustment_counts") or {}),
        "no_bet_reason_counts": dict(payload.get("no_bet_reason_counts") or {}),
        "no_trade_reason_counts": dict(payload.get("no_trade_reason_counts") or {}),
        "missing_input_counts": dict(payload.get("missing_input_counts") or {}),
        "items": items,
        "deepseek_used": bool(payload.get("deepseek_used", False)),
        "openai_used": bool(payload.get("openai_used", False)),
        "external_ai_call_performed": bool(payload.get("external_ai_call_performed", False)),
        "red_team_only": True,
        "provider_write": False,
        "execution_allowed": False,
        "live_execution_enabled": False,
        "auto_execution": False,
        "auto_execution_enabled": False,
        "human_approval_required": True,
        "owner_approval_required": True,
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

from __future__ import annotations

from typing import Any

from .random_baseline_comparison import compare_to_random_baseline
from .random_matrix_risk import evaluate_random_matrix_risk
from .security_policy import locked_safety_flags
from .tail_event_classifier import classify_tail_event
from .tracy_widom_research import evaluate_tracy_widom_research


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if abs(parsed) <= 1.0:
        return parsed * 100.0
    return parsed


def _asset_type(row: dict[str, Any]) -> str:
    text = str(row.get("asset_type") or row.get("asset_class") or "unknown").strip().lower()
    aliases = {"bond": "bond_rate", "rate": "bond_rate", "rates": "bond_rate", "sports": "sportsbook"}
    return aliases.get(text, text)


def _candidate_score(row: dict[str, Any]) -> float:
    values = [
        abs(_num(row.get("estimated_edge"))),
        abs(_num(row.get("edge_z_score"))) * 12.5,
        abs(_num(row.get("price_move"))),
        abs(_num(row.get("odds_move"))),
        abs(_num(row.get("line_move"))),
        _num(row.get("volume_spike")) * 10.0,
        _num(row.get("relative_volume")) * 10.0,
        _num(row.get("volatility_score")),
    ]
    return round(max(0.0, min(100.0, max(values))), 2)


def _calibration_supported(row: dict[str, Any], baseline: dict[str, Any]) -> bool:
    status = str(row.get("calibration_status") or "").lower()
    sample = int(_num(row.get("historical_sample_size"), 0.0))
    baseline_ready = baseline.get("baseline_support_status") == "ready"
    return bool(baseline_ready and sample >= 30 and status in {"partial_calibration", "calibrated", "active_calibration", "ready"})


def _risk_label(score: float) -> str:
    if score >= 80:
        return "extreme"
    if score >= 60:
        return "high"
    if score >= 35:
        return "moderate"
    return "low"


def _missing_inputs(row: dict[str, Any], baseline: dict[str, Any], rmt: dict[str, Any]) -> list[str]:
    missing = []
    if baseline.get("baseline_support_status") != "ready":
        missing.append("random_baseline_distribution")
    if row.get("historical_sample_size") in (None, ""):
        missing.append("historical_sample_size")
    if row.get("calibration_bucket") in (None, "") and row.get("calibration_status") in (None, ""):
        missing.append("calibration_bucket_or_status")
    if rmt.get("insufficient_matrix_data"):
        missing.append("correlation_or_feature_matrix")
    return missing


def diagnose_extreme_randomness(
    candidate: dict[str, Any] | None = None,
    *,
    baseline_values: list[Any] | None = None,
    matrix_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = dict(candidate or {})
    asset_type = _asset_type(row)
    market_type = str(row.get("market_type") or asset_type)
    baseline = compare_to_random_baseline(row, baseline_values=baseline_values)
    tail = classify_tail_event(row)
    rmt_input = dict(matrix_payload or {})
    if not rmt_input:
        rmt_input = {
            key: row.get(key)
            for key in ("correlation_matrix", "covariance_matrix", "asset_return_matrix", "feature_matrix", "sample_size", "dimension_count")
            if key in row
        }
    rmt = evaluate_random_matrix_risk(rmt_input)
    tw = evaluate_tracy_widom_research(rmt)
    score = _candidate_score(row)
    baseline_percentile = baseline.get("observed_vs_baseline_percentile")
    if baseline_percentile is None:
        random_baseline_percentile = 0.0
        extreme_percentile = 0.0
    else:
        random_baseline_percentile = round(float(baseline_percentile), 6)
        extreme_percentile = random_baseline_percentile
    calibration_supported = _calibration_supported(row, baseline)
    insufficient = baseline.get("baseline_support_status") != "ready"
    edge_survives = bool(baseline.get("edge_survives_random_baseline", False))
    if insufficient:
        action = "request_more_data"
        warning = "baseline_missing_do_not_trust_extreme_signal"
        edge_vs_random = "blocked_insufficient_data"
        blocked_reason = baseline.get("blocked_reason") or "baseline_missing"
    elif not edge_survives:
        action = "downgrade_review"
        warning = "observed_signal_does_not_survive_random_baseline"
        edge_vs_random = "does_not_survive_random_baseline"
        blocked_reason = None
    elif edge_survives and not calibration_supported:
        action = "request_more_data"
        warning = "extreme_signal_without_calibration_increases_caution_not_confidence"
        edge_vs_random = "survives_baseline_but_calibration_missing"
        blocked_reason = "calibration_not_supported"
    else:
        action = "none"
        warning = "baseline_supported_extreme_signal_still_red_team_only"
        edge_vs_random = "survives_random_baseline"
        blocked_reason = None
    tail_type = str(tail.get("tail_event_type") or "normal_noise")
    if tail_type == "fake_edge_tail_event":
        action = "no_bet" if asset_type in {"prediction_market", "sportsbook"} else "no_trade"
        warning = "fake_edge_tail_event_detected"
    elif tail_type in {"data_error_or_stale_feed", "market_structure_break"} and action == "none":
        action = "request_more_data"
        warning = "tail_event_requires_data_recheck"
    elif tail_type in {"liquidity_tail_event", "volatility_tail_event", "correlation_tail_event", "possible_regime_change", "random_extreme"} and action == "none":
        action = "downgrade_review"
        warning = "tail_event_detected_red_team_penalty_only"

    fake_edge_score = max(
        _num(row.get("estimated_edge")),
        100.0 - _num(row.get("liquidity_score"), 50.0),
        100.0 - _num(row.get("spread_score"), 50.0),
        float(tail.get("tail_event_risk_score", 0.0) or 0.0) if tail_type == "fake_edge_tail_event" else 0.0,
    )
    missing = _missing_inputs(row, baseline, rmt)
    outlier_status = "blocked_insufficient_data" if insufficient else "outlier" if random_baseline_percentile >= 0.95 else "within_random_baseline"
    sample_item = {
        "asset_type": asset_type,
        "market_type": market_type,
        "extreme_signal_score": score,
        "extreme_signal_percentile": extreme_percentile,
        "random_baseline_percentile": random_baseline_percentile,
        "tail_event_risk": tail.get("tail_event_risk_score", 0.0),
        "edge_vs_random_baseline": edge_vs_random,
        "fake_edge_risk": _risk_label(fake_edge_score),
        "outlier_status": outlier_status,
        "red_team_warning": warning,
        "recommended_action_adjustment": action,
        "insufficient_sample": bool(insufficient),
        "blocked_reason": blocked_reason,
        "tail_event_type": tail_type,
        "tail_event_risk_score": tail.get("tail_event_risk_score", 0.0),
        "rmt_status": rmt.get("rmt_status", "not_applicable"),
        "tracy_widom_status": tw.get("tracy_widom_status", "not_applicable"),
        "edge_survives_random_baseline": edge_survives,
        "no_bet_reasons": list(tail.get("no_bet_reasons") or [])[:10],
        "no_trade_reasons": list(tail.get("no_trade_reasons") or [])[:10],
        "missing_inputs": missing[:20],
    }
    payload = {
        "ok": True,
        "status": "extreme_randomness_diagnostics_complete",
        "red_team_only": True,
        "research_only": True,
        "calibration_only": True,
        "sample_item": sample_item,
        "random_baseline": baseline,
        "tail_event": tail,
        "random_matrix": rmt,
        "tracy_widom": tw,
        "allowed_effects": ["red_team_warnings", "fake_edge_detection", "tail_risk_classification", "downgrade_review", "request_more_data"],
        "forbidden_effects": ["automatic_approval", "automatic_execution", "order_creation", "bet_creation", "provider_write"],
        "raw_payload_included": False,
        "secrets_included": False,
    }
    payload.update(locked_safety_flags())
    payload["provider_write"] = False
    payload["execution_allowed"] = False
    payload["live_execution_enabled"] = False
    payload["auto_execution"] = False
    payload["human_approval_required"] = True
    payload["owner_approval_required"] = True
    return payload

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .data_paths import get_storage_health, resolve_base_data_dir
from .scheduler_config import SCHEMA_VERSION, sanitize_filename, utc_now_iso


MANIFOLD_TRAP_SCHEMA_VERSION = f"{SCHEMA_VERSION}.market_state_manifold.no_bet_traps.v1"
MIN_TRAP_STATS_SAMPLE = 30


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, float(value)))


def _unit(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if 0.0 <= parsed <= 1.0:
        return parsed
    return _clamp(parsed, 0.0, 100.0) / 100.0


def _score(value: Any, default: float = 0.0) -> float:
    return _unit(value, default=default) * 100.0


def _negative_metric(value: Any) -> bool:
    try:
        if value is None:
            return False
        return float(value) < 0.0
    except (TypeError, ValueError):
        return False


def _execution_action(asset_type: str) -> str:
    if asset_type in {"stock", "crypto", "etf", "bond_rate", "major_asset"}:
        return "NO_TRADE"
    return "NO_BET"


def detect_manifold_trap(
    *,
    asset_type: str,
    cluster_id: str | None,
    cluster_name: str | None,
    normalized_features: dict[str, float] | None = None,
    cluster_stats: dict[str, Any] | None = None,
    source_item: dict[str, Any] | None = None,
) -> dict[str, Any]:
    features = normalized_features or {}
    stats = cluster_stats or {}
    item = source_item or {}
    reasons: list[str] = []
    score = 0.0

    confidence = _score(features.get("confidence_score", item.get("confidence_score")), default=0.0)
    edge = _score(features.get("estimated_edge", item.get("estimated_edge")), default=50.0)
    liquidity = _score(features.get("liquidity_score", item.get("liquidity_score")), default=50.0)
    spread_quality = _score(features.get("spread_score", item.get("spread_score")), default=50.0)
    stale = _score(features.get("stale_data_risk", item.get("stale_data_risk")), default=0.0)
    settlement_uncertainty = _score(features.get("settlement_uncertainty_score", item.get("settlement_uncertainty_score")), default=0.0)
    pricing_quality = _score(features.get("pricing_quality_score", item.get("pricing_quality_score")), default=50.0)
    pattern_failure = _score(features.get("breakout_failure_score", item.get("breakout_failure_score")), default=0.0)
    dilution = _score(features.get("dilution_risk_score", item.get("dilution_risk_score")), default=0.0)
    liquidation = _score(features.get("liquidation_cluster_risk", item.get("liquidation_cluster_risk")), default=0.0)
    correlation = _score(features.get("correlation_score", item.get("correlation_score")), default=0.0)
    live_latency = _score(features.get("live_latency_score", item.get("live_latency_score")), default=0.0)

    stats_sample = int(stats.get("sample_size", 0) or 0)
    stats_usable = stats_sample >= MIN_TRAP_STATS_SAMPLE and not bool(stats.get("insufficient_sample", True))
    win_rate = stats.get("win_rate") if stats_usable else None
    roi = stats.get("historical_roi", stats.get("average_return")) if stats_usable else None
    false_positive_rate = stats.get("false_positive_rate") if stats_usable else None
    false_breakout_rate = stats.get("false_breakout_rate") if stats_usable else None
    negative_ev_rate = stats.get("historical_negative_ev_rate") if stats_usable else None

    if confidence >= 70.0 and (win_rate is not None and float(win_rate) < 0.48 or _negative_metric(roi)):
        score += 28.0
        reasons.append("high_confidence_poor_realized_outcomes")
    if edge >= 70.0 and liquidity < 40.0:
        score += 20.0
        reasons.append("high_estimated_edge_low_liquidity")
    if edge >= 65.0 and spread_quality < 35.0:
        score += 20.0
        reasons.append("wide_spread_fake_edge")
    if stale >= 65.0:
        score += 16.0
        reasons.append("stale_line_or_price")
    if settlement_uncertainty >= 65.0:
        score += 16.0
        reasons.append("settlement_uncertainty_high")
    if pricing_quality < 35.0:
        score += 10.0
        reasons.append("poor_pricing_quality")
    if false_positive_rate is not None and float(false_positive_rate) >= 0.45:
        score += 20.0
        reasons.append("historical_false_positive_cluster")
    if negative_ev_rate is not None and float(negative_ev_rate) >= 0.55:
        score += 18.0
        reasons.append("historical_negative_ev_cluster")
    if false_breakout_rate is not None and float(false_breakout_rate) >= 0.35:
        score += 16.0
        reasons.append("historical_false_breakout_cluster")
    if pattern_failure >= 70.0:
        score += 14.0
        reasons.append("breakout_failure_context")
    if dilution >= 70.0:
        score += 16.0
        reasons.append("dilution_risk_momentum_trap")
    if liquidation >= 70.0:
        score += 14.0
        reasons.append("liquidation_cluster_risk")
    if asset_type == "sportsbook" and correlation >= 80.0 and live_latency >= 70.0:
        score += 12.0
        reasons.append("sports_correlation_latency_trap")
    if bool(item.get("stale_market")):
        score += 10.0
        if "stale_line_or_price" not in reasons:
            reasons.append("stale_line_or_price")

    score = round(_clamp(score), 2)
    action = _execution_action(asset_type) if score >= 80.0 else "LOW_PRIORITY_REVIEW" if score >= 65.0 else "WATCHLIST_REVIEW"
    no_bet_score = score if asset_type in {"prediction_market", "sportsbook"} else min(score, 35.0)
    no_trade_score = score if asset_type in {"stock", "crypto", "etf", "bond_rate", "major_asset"} else min(score, 35.0)
    return {
        "trap_cluster_detected": score >= 65.0,
        "trap_cluster_id": cluster_id if score >= 65.0 else None,
        "trap_cluster_name": cluster_name if score >= 65.0 else None,
        "no_bet_trap_score": round(no_bet_score, 2),
        "no_trade_trap_score": round(no_trade_score, 2),
        "historical_false_positive_rate": false_positive_rate,
        "historical_negative_ev_rate": negative_ev_rate,
        "trap_reasons": reasons[:10],
        "recommended_action": action,
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
    }


def _traps_dir(base_data_dir: str = "data") -> Path:
    path = resolve_base_data_dir(base_data_dir) / "manifold" / "no_bet_traps"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _latest_path(base_data_dir: str = "data") -> Path:
    return _traps_dir(base_data_dir) / "latest.json"


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


def _project_relative_path(base_data_dir: str, path: Path) -> str:
    root = resolve_base_data_dir(base_data_dir)
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return path.name


def write_trap_report(traps: list[dict[str, Any]], *, base_data_dir: str = "data") -> dict[str, Any]:
    safe_traps = [
        {
            "trap_cluster_detected": bool(row.get("trap_cluster_detected")),
            "trap_cluster_id": row.get("trap_cluster_id"),
            "trap_cluster_name": row.get("trap_cluster_name"),
            "no_bet_trap_score": row.get("no_bet_trap_score"),
            "no_trade_trap_score": row.get("no_trade_trap_score"),
            "historical_false_positive_rate": row.get("historical_false_positive_rate"),
            "historical_negative_ev_rate": row.get("historical_negative_ev_rate"),
            "trap_reasons": list(row.get("trap_reasons") or [])[:10],
            "recommended_action": row.get("recommended_action"),
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
        }
        for row in traps
        if isinstance(row, dict)
    ]
    payload = {
        "ok": True,
        "schema_version": MANIFOLD_TRAP_SCHEMA_VERSION,
        "created_at": utc_now_iso(),
        "trap_count": len([row for row in safe_traps if row.get("trap_cluster_detected")]),
        "items": safe_traps,
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
        "storage_backend": "file",
    }
    latest = _latest_path(base_data_dir)
    history = _traps_dir(base_data_dir) / f"{sanitize_filename(utc_now_iso()[:10])}.json"
    _atomic_write_json(latest, payload)
    _atomic_write_json(history, payload)
    return {
        "storage_backend": "file",
        "trap_report_path": _project_relative_path(base_data_dir, latest),
        "trap_report_history_path": _project_relative_path(base_data_dir, history),
        "trap_count": payload["trap_count"],
    }


def load_trap_report(*, base_data_dir: str = "data") -> dict[str, Any]:
    payload = _read_json(_latest_path(base_data_dir))
    if isinstance(payload, dict):
        payload["storage_health"] = get_storage_health()
        return payload
    return {
        "ok": True,
        "schema_version": MANIFOLD_TRAP_SCHEMA_VERSION,
        "status": "empty",
        "trap_count": 0,
        "items": [],
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
        "storage_backend": "file",
        "storage_health": get_storage_health(),
    }


def compact_trap_report(report: dict[str, Any], *, limit: int = 25) -> dict[str, Any]:
    cap = max(1, min(int(limit or 25), 100))
    items = []
    for row in [item for item in report.get("items", []) if isinstance(item, dict)][:cap]:
        items.append(
            {
                "trap_cluster_detected": bool(row.get("trap_cluster_detected")),
                "trap_cluster_id": row.get("trap_cluster_id"),
                "no_bet_trap_score": row.get("no_bet_trap_score"),
                "no_trade_trap_score": row.get("no_trade_trap_score"),
                "historical_false_positive_rate": row.get("historical_false_positive_rate"),
                "historical_negative_ev_rate": row.get("historical_negative_ev_rate"),
                "trap_reasons": list(row.get("trap_reasons") or [])[:5],
                "recommended_action": row.get("recommended_action"),
                "execution_allowed": False,
                "provider_write": False,
                "live_execution_enabled": False,
                "auto_execution": False,
                "auto_execution_enabled": False,
                "human_approval_required": True,
                "actual_orders_submitted": 0,
                "actual_bets_submitted": 0,
                "actual_trades_submitted": 0,
                "raw_payload_included": False,
                "secrets_included": False,
            }
        )
    return {
        "ok": bool(report.get("ok", True)),
        "status": report.get("status", "ok"),
        "schema_version": report.get("schema_version", MANIFOLD_TRAP_SCHEMA_VERSION),
        "trap_count": int(report.get("trap_count", len(items))),
        "items": items,
        "storage_backend": report.get("storage_backend", "file"),
        "storage": report.get("storage_health"),
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
    }

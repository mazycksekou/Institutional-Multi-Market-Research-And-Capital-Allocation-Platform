from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .data_paths import get_storage_health, resolve_base_data_dir
from .scheduler_config import SCHEMA_VERSION, redact_secrets, safe_run_id, sanitize_filename, utc_now_iso


QUEUE_SCHEMA_VERSION = f"{SCHEMA_VERSION}.small_account_pattern_review.v1"
QUEUE_STATUSES = {
    "ACTIVE_REVIEW",
    "WATCHLIST_REVIEW",
    "LOW_PRIORITY_REVIEW",
    "NO_REVIEW",
    "NO_TRADE",
    "NO_TRADE_SESSION_LOCK",
    "DATA_INSUFFICIENT",
}


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, float(value)))


def _score_or_prior(value: Any, prior: float = 50.0) -> float:
    return _clamp(_num(value, prior))


def _queue_dir(base_data_dir: str | None = None) -> Path:
    path = resolve_base_data_dir(base_data_dir) / "small_account_review" / "pattern_review_queue"
    path.mkdir(parents=True, exist_ok=True)
    return path


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


def _project_relative_path(base_data_dir: str | None, path: Path) -> str:
    root = resolve_base_data_dir(base_data_dir)
    try:
        return str(path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return path.name


def _sanitize_item(item: dict[str, Any]) -> dict[str, Any]:
    redacted = redact_secrets(dict(item))
    for key in ("provider_payload", "raw_payload", "external_payload", "source_payload", "raw_provider_payload"):
        redacted.pop(key, None)
    redacted["provider_write"] = False
    redacted["execution_allowed"] = False
    redacted["live_execution_enabled"] = False
    redacted["auto_execution"] = False
    redacted["auto_execution_enabled"] = False
    redacted["human_approval_required"] = True
    redacted["actual_orders_submitted"] = 0
    redacted["actual_bets_submitted"] = 0
    redacted["actual_trades_submitted"] = 0
    return redacted


def calculate_review_priority_score(
    *,
    pattern_quality_score: Any,
    liquidity_score: Any,
    volume_confirmation_score: Any,
    catalyst_score: Any,
    time_of_day_score: Any,
    risk_reward_score: Any,
    balance_sheet_quality_score: Any,
    historical_calibration_score: Any = None,
    micro_calibration_score: Any = None,
    trade_window_calibration_score: Any = None,
    spread_slippage_score: Any = None,
    session_risk_score: Any = None,
) -> float:
    score = (
        _score_or_prior(pattern_quality_score, 50.0) * 0.16
        + _score_or_prior(liquidity_score, 45.0) * 0.16
        + _score_or_prior(volume_confirmation_score, 45.0) * 0.10
        + _score_or_prior(catalyst_score, 35.0) * 0.10
        + _score_or_prior(time_of_day_score, 50.0) * 0.10
        + _score_or_prior(risk_reward_score, 45.0) * 0.10
        + _score_or_prior(balance_sheet_quality_score, 50.0) * 0.08
        + _score_or_prior(historical_calibration_score, 50.0) * 0.05
        + _score_or_prior(micro_calibration_score, 50.0) * 0.05
        + _score_or_prior(trade_window_calibration_score, 50.0) * 0.05
        + _score_or_prior(spread_slippage_score, 45.0) * 0.03
        + _score_or_prior(session_risk_score, 75.0) * 0.02
    )
    return round(_clamp(score), 2)


def queue_status_for_score(score: Any) -> str:
    parsed = _num(score)
    if parsed >= 85:
        return "ACTIVE_REVIEW"
    if parsed >= 70:
        return "WATCHLIST_REVIEW"
    if parsed >= 55:
        return "LOW_PRIORITY_REVIEW"
    return "NO_REVIEW"


def build_pattern_review_item(
    *,
    detection: dict[str, Any],
    liquidity: dict[str, Any],
    catalyst: dict[str, Any],
    time_context: dict[str, Any],
    risk_reward: dict[str, Any],
    balance_sheet: dict[str, Any],
    price_band: dict[str, Any],
    session_risk: dict[str, Any],
    quality: dict[str, Any] | None = None,
    historical_calibration_score: Any = None,
    micro_calibration_score: Any = None,
    trade_window_calibration_score: Any = None,
    special_catalyst: bool = False,
) -> dict[str, Any]:
    quality = quality or {}
    liquidity_score = _score_or_prior(liquidity.get("liquidity_score"), 0.0)
    balance_quality = _score_or_prior(balance_sheet.get("balance_sheet_quality_score"), 50.0)
    catalyst_score = _score_or_prior(catalyst.get("catalyst_quality_score"), 0.0)
    priority = calculate_review_priority_score(
        pattern_quality_score=detection.get("pattern_quality_score"),
        liquidity_score=liquidity_score,
        volume_confirmation_score=detection.get("volume_confirmation_score"),
        catalyst_score=catalyst_score,
        time_of_day_score=time_context.get("time_of_day_edge_score"),
        risk_reward_score=risk_reward.get("risk_reward_score"),
        balance_sheet_quality_score=balance_quality,
        historical_calibration_score=historical_calibration_score,
        micro_calibration_score=micro_calibration_score,
        trade_window_calibration_score=trade_window_calibration_score,
        spread_slippage_score=liquidity.get("spread_slippage_score"),
        session_risk_score=session_risk.get("session_risk_score"),
    )

    no_trade_reasons: list[str] = []
    review_reasons: list[str] = []
    warnings: list[str] = []
    data_resolution = detection.get("data_resolution") or "unknown"
    if detection:
        review_reasons.append("pattern_detected")
    if liquidity_score >= 40:
        review_reasons.append("liquidity_confirmed")
    if risk_reward.get("risk_reward_permission_status") in {"VALID", "REVIEW_ALLOWED_WITH_CAUTION"}:
        review_reasons.append("risk_reward_valid")
    if catalyst.get("catalyst_detected"):
        review_reasons.append("catalyst_context_present")

    if session_risk.get("session_permission_status") == "NO_TRADE_SESSION_LOCK":
        no_trade_reasons.extend(session_risk.get("walk_away_reasons") or ["session_locked"])
        status = "NO_TRADE_SESSION_LOCK"
    elif liquidity_score < 40 and not special_catalyst:
        no_trade_reasons.extend(liquidity.get("liquidity_blockers") or ["liquidity_score_below_40"])
        status = "NO_TRADE"
    else:
        status = queue_status_for_score(priority)

    if liquidity_score < 40 and special_catalyst:
        warnings.append("special_catalyst_with_low_liquidity_requires_explicit_risk_review")
        priority = min(priority, 69.0)
        status = "LOW_PRIORITY_REVIEW" if status not in {"NO_TRADE_SESSION_LOCK"} else status
    if risk_reward.get("risk_reward_permission_status") in {"BLOCKED", "DATA_INSUFFICIENT"}:
        no_trade_reasons.extend(risk_reward.get("risk_reward_blockers") or ["risk_reward_invalid"])
        if status not in {"NO_TRADE_SESSION_LOCK", "NO_TRADE"}:
            status = "DATA_INSUFFICIENT" if risk_reward.get("risk_reward_permission_status") == "DATA_INSUFFICIENT" else "NO_REVIEW"
    if balance_sheet.get("data_insufficient"):
        warnings.append("balance_sheet_data_insufficient")
    if balance_sheet.get("force_status") == "NO_REVIEW":
        no_trade_reasons.extend(balance_sheet.get("risk_blockers") or ["balance_sheet_extreme_risk"])
        if status not in {"NO_TRADE_SESSION_LOCK", "NO_TRADE"}:
            status = "NO_REVIEW"
    elif balance_sheet.get("force_status") == "HIGH_RISK_REVIEW":
        warnings.append("balance_sheet_high_risk_review")
        priority = min(priority, 69.0)
        if status in {"ACTIVE_REVIEW", "WATCHLIST_REVIEW"}:
            status = "LOW_PRIORITY_REVIEW"
    if price_band.get("no_review_reasons"):
        warnings.extend(price_band.get("no_review_reasons") or [])
        if price_band.get("price_band") == "below_2_caution" and status in {"ACTIVE_REVIEW", "WATCHLIST_REVIEW"}:
            status = "LOW_PRIORITY_REVIEW"
            priority = min(priority, 69.0)
    if time_context.get("session_time_bucket") == "MIDDAY_CHOP" and liquidity_score < 65:
        warnings.append("midday_weak_volume_watchlist_only")
        if status in {"ACTIVE_REVIEW", "WATCHLIST_REVIEW"}:
            status = "LOW_PRIORITY_REVIEW"
            priority = min(priority, 69.0)

    status = status if status in QUEUE_STATUSES else "NO_REVIEW"
    symbol = str(detection.get("asset_symbol") or "UNKNOWN").upper()
    item_id = safe_run_id(
        "small_account_pattern_queue",
        f"{symbol}|{detection.get('detection_id')}|{detection.get('pattern_id')}|{detection.get('detected_at')}",
    )
    return {
        "schema_version": QUEUE_SCHEMA_VERSION,
        "id": item_id,
        "detection_id": detection.get("detection_id"),
        "created_at": utc_now_iso(),
        "updated_at": utc_now_iso(),
        "asset_symbol": symbol,
        "asset_type": detection.get("asset_type"),
        "timeframe": detection.get("timeframe"),
        "pattern_id": detection.get("pattern_id"),
        "pattern_name": detection.get("pattern_name"),
        "pattern_family": detection.get("pattern_family"),
        "direction": detection.get("direction"),
        "detected_at": detection.get("detected_at"),
        "queue_status": status,
        "review_priority_score": round(priority, 2),
        "liquidity_score": liquidity.get("liquidity_score"),
        "liquidity_tier": liquidity.get("liquidity_tier"),
        "pattern_quality_score": detection.get("pattern_quality_score"),
        "volume_confirmation_score": detection.get("volume_confirmation_score"),
        "breakout_confirmation_score": detection.get("breakout_confirmation_score"),
        "catalyst_score": catalyst_score,
        "catalyst_detected": bool(catalyst.get("catalyst_detected", False)),
        "catalyst_type": catalyst.get("catalyst_type"),
        "time_of_day_score": time_context.get("time_of_day_edge_score"),
        "session_time_bucket": time_context.get("session_time_bucket"),
        "risk_reward_score": risk_reward.get("risk_reward_score"),
        "risk_reward_ratio": risk_reward.get("reward_risk_ratio"),
        "breakeven_win_rate": risk_reward.get("breakeven_win_rate"),
        "balance_sheet_quality_score": balance_sheet.get("balance_sheet_quality_score"),
        "balance_sheet_risk_score": balance_sheet.get("fundamental_risk_score"),
        "balance_sheet_risk_bucket": balance_sheet.get("balance_sheet_risk_bucket"),
        "historical_calibration_score": historical_calibration_score,
        "micro_calibration_score": micro_calibration_score,
        "trade_window_calibration_score": trade_window_calibration_score,
        "spread_slippage_score": liquidity.get("spread_slippage_score"),
        "session_risk_score": session_risk.get("session_risk_score"),
        "entry_trigger_price": detection.get("entry_trigger_price"),
        "stop_loss_level": detection.get("stop_loss_level"),
        "target_price": detection.get("target_price"),
        "price": price_band.get("price"),
        "price_band": price_band.get("price_band"),
        "price_range_quality_score": price_band.get("price_range_quality_score"),
        "small_account_fit_score": price_band.get("small_account_fit_score"),
        "overextension_risk": price_band.get("overextension_risk"),
        "stock_quality_score": quality.get("stock_quality_score"),
        "a_quality_candidate": bool(quality.get("a_quality_candidate", False)),
        "data_resolution": data_resolution,
        "no_trade_reasons": sorted(set(str(reason) for reason in no_trade_reasons if reason)),
        "review_reasons": sorted(set(str(reason) for reason in review_reasons if reason)),
        "risk_warnings": sorted(set(str(warning) for warning in warnings if warning)),
        "human_review_required": status not in {"NO_REVIEW", "NO_TRADE", "NO_TRADE_SESSION_LOCK", "DATA_INSUFFICIENT"},
        "paper_calibration_allowed": status in {"ACTIVE_REVIEW", "WATCHLIST_REVIEW", "LOW_PRIORITY_REVIEW"},
        "recommendation_status": "review_only",
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


def summarize_pattern_review_queue(items: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    pattern_counts: dict[str, int] = {}
    liquidity_tier_counts: dict[str, int] = {}
    for item in items:
        status = str(item.get("queue_status") or "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1
        pattern = str(item.get("pattern_id") or "unknown")
        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        tier = str(item.get("liquidity_tier") or "unknown")
        liquidity_tier_counts[tier] = liquidity_tier_counts.get(tier, 0) + 1
    return {
        "total_count": len(items),
        "status_counts": status_counts,
        "pattern_counts": pattern_counts,
        "liquidity_tier_counts": liquidity_tier_counts,
        "active_review_count": status_counts.get("ACTIVE_REVIEW", 0),
        "watchlist_review_count": status_counts.get("WATCHLIST_REVIEW", 0),
        "low_priority_review_count": status_counts.get("LOW_PRIORITY_REVIEW", 0),
        "no_review_count": status_counts.get("NO_REVIEW", 0),
        "no_trade_count": status_counts.get("NO_TRADE", 0) + status_counts.get("NO_TRADE_SESSION_LOCK", 0),
        "data_insufficient_count": status_counts.get("DATA_INSUFFICIENT", 0),
        "execution_allowed_count": 0,
    }


def persist_pattern_review_queue(items: list[dict[str, Any]], *, base_data_dir: str | None = None) -> dict[str, Any]:
    safe_items = [_sanitize_item(item) for item in items if isinstance(item, dict)]
    now = utc_now_iso()
    run_id = safe_run_id("small_account_pattern_queue_run", now + str(len(safe_items)))
    payload = {
        "schema_version": QUEUE_SCHEMA_VERSION,
        "storage_backend": "file",
        "latest_run_id": run_id,
        "last_updated_at": now,
        "items_written_count": len(safe_items),
        "summary": summarize_pattern_review_queue(safe_items),
        "items": safe_items,
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
    qdir = _queue_dir(base_data_dir)
    latest = qdir / "latest.json"
    run_path = qdir / "items" / f"{sanitize_filename(run_id)}.json"
    _atomic_write_json(latest, payload)
    _atomic_write_json(run_path, payload)
    return {
        "storage_backend": "file",
        "latest_run_id": run_id,
        "last_updated_at": now,
        "queue_write_path": _project_relative_path(base_data_dir, latest),
        "queue_items_run_path": _project_relative_path(base_data_dir, run_path),
        "items_written_count": len(safe_items),
    }


def load_pattern_review_queue(*, base_data_dir: str | None = None, limit: int | None = None) -> dict[str, Any]:
    latest = _queue_dir(base_data_dir) / "latest.json"
    payload = _read_json(latest)
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        items = [item for item in payload["items"] if isinstance(item, dict)]
        if limit and limit > 0:
            items = items[:limit]
        return {
            "ok": True,
            "status": "ok",
            "count": len(items),
            "items": items,
            "summary": payload.get("summary") or summarize_pattern_review_queue(items),
            "storage_backend": payload.get("storage_backend", "file"),
            "last_updated_at": payload.get("last_updated_at"),
            "latest_run_id": payload.get("latest_run_id"),
            "queue_read_ok": True,
            "queue_error_category": None,
            "queue_read_path": _project_relative_path(base_data_dir, latest),
            "items_read_count": len(items),
            "storage_health": get_storage_health(),
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
    malformed = latest.exists() and payload is None
    return {
        "ok": True,
        "status": "empty" if not malformed else "storage_read_error",
        "count": 0,
        "items": [],
        "summary": summarize_pattern_review_queue([]),
        "storage_backend": "file",
        "last_updated_at": None,
        "latest_run_id": None,
        "queue_read_ok": not malformed,
        "queue_error_category": "malformed_latest_queue_file" if malformed else None,
        "queue_read_path": _project_relative_path(base_data_dir, latest) if latest.exists() else None,
        "items_read_count": 0,
        "storage_health": get_storage_health(),
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

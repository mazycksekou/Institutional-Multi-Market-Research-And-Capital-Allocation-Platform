from __future__ import annotations

from datetime import datetime
from typing import Any

from .scheduler_config import safe_run_id, utc_now_iso


MICRO_OUTCOME_WINDOWS = ("15s", "30s", "1m", "2m", "3m")
SUB_MINUTE_RESOLUTIONS = {"tick", "ticks", "quote", "quotes", "sub_second", "sub_minute", "sub_minute_bars"}
ONE_MINUTE_RESOLUTIONS = SUB_MINUTE_RESOLUTIONS | {"1m", "1m_candles", "one_minute", "minute"}


def _num(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _window_seconds(window: str) -> int | None:
    key = str(window).strip().lower().replace(" ", "")
    aliases = {
        "15seconds": "15s",
        "30seconds": "30s",
        "1minute": "1m",
        "2minutes": "2m",
        "3minutes": "3m",
        "5minutes": "5m",
        "15minutes": "15m",
        "30minutes": "30m",
        "60minutes": "60m",
    }
    key = aliases.get(key, key)
    if key.endswith("s"):
        return int(key[:-1])
    if key.endswith("m"):
        return int(key[:-1]) * 60
    return None


def supports_outcome_window(data_resolution: str | None, outcome_window: str) -> bool:
    resolution = str(data_resolution or "").strip().lower()
    window = str(outcome_window).strip().lower()
    if window in {"15s", "30s"}:
        return resolution in SUB_MINUTE_RESOLUTIONS
    if window in {"1m", "2m", "3m"}:
        return resolution in ONE_MINUTE_RESOLUTIONS
    if window in {"5m", "15m", "30m", "60m", "end_of_day"}:
        return resolution in ONE_MINUTE_RESOLUTIONS | {"5m", "5m_candles", "five_minute", "daily", "eod"}
    return False


def unsupported_windows_for_resolution(data_resolution: str | None, windows: list[str] | tuple[str, ...]) -> list[str]:
    return [window for window in windows if not supports_outcome_window(data_resolution, window)]


def _offset_seconds(row: dict[str, Any], detected_at: Any) -> float | None:
    direct = _num(row.get("seconds_since_detection", row.get("offset_seconds")))
    if direct is not None:
        return direct
    timestamp = row.get("timestamp") or row.get("time")
    if not timestamp or not detected_at:
        return None
    try:
        start = detected_at if isinstance(detected_at, datetime) else datetime.fromisoformat(str(detected_at).replace("Z", "+00:00"))
        current = timestamp if isinstance(timestamp, datetime) else datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        return (current - start).total_seconds()
    except Exception:
        return None


def _price(row: dict[str, Any], key: str, default_key: str = "price") -> float | None:
    return _num(row.get(key, row.get(default_key)))


def settle_outcome_window(
    detection: dict[str, Any],
    price_history: list[dict[str, Any]] | None,
    *,
    outcome_window: str,
    data_resolution: str,
) -> dict[str, Any]:
    detected_at = detection.get("detected_at")
    entry = _num(detection.get("entry_reference_price", detection.get("entry_trigger_price", detection.get("trigger_price"))))
    trigger = _num(detection.get("entry_trigger_price", detection.get("trigger_price")), entry)
    target = _num(detection.get("target_price"))
    stop = _num(detection.get("stop_loss_level", detection.get("invalidation_price")))
    direction = str(detection.get("direction") or "bullish").lower()
    seconds = _window_seconds(outcome_window)
    base = {
        "outcome_record_id": safe_run_id("small_account_outcome_window", f"{detection.get('detection_id')}|{outcome_window}|{data_resolution}"),
        "detection_id": detection.get("detection_id"),
        "asset_symbol": detection.get("asset_symbol"),
        "asset_type": detection.get("asset_type"),
        "timeframe": detection.get("timeframe"),
        "pattern_id": detection.get("pattern_id"),
        "detected_at": detected_at,
        "entry_reference_price": entry,
        "outcome_window": outcome_window,
        "data_resolution": data_resolution,
        "requested_window_seconds": seconds,
        "effective_window_seconds": None,
        "delayed_by_seconds": None,
        "delay_source": None,
        "usable_for_calibration": False,
        "profit_factor_by_pattern": None,
        "win_rate_by_pattern": None,
        "expectancy_by_pattern": None,
        "best_time_of_day": None,
        "best_asset_type": None,
        "best_liquidity_bucket": None,
        "sample_size": 0,
        "insufficient_sample": True,
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
    if not supports_outcome_window(data_resolution, outcome_window):
        return {
            **base,
            "price_at_window": None,
            "high_since_detection": None,
            "low_since_detection": None,
            "max_favorable_excursion": None,
            "max_adverse_excursion": None,
            "follow_through_percent": None,
            "reversal_percent": None,
            "hit_trigger": False,
            "hit_target": False,
            "hit_stop": False,
            "failed_breakout": False,
            "liquidity_deteriorated": False,
            "spread_widened": False,
            "volume_confirmed": False,
            "outcome_status": "data_insufficient",
            "final_outcome": "data_resolution_insufficient",
            "data_resolution_insufficient": True,
            "delay_source": "unsupported_data_resolution",
        }
    if entry is None or entry <= 0:
        return {
            **base,
            "price_at_window": None,
            "high_since_detection": None,
            "low_since_detection": None,
            "max_favorable_excursion": None,
            "max_adverse_excursion": None,
            "follow_through_percent": None,
            "reversal_percent": None,
            "hit_trigger": False,
            "hit_target": False,
            "hit_stop": False,
            "failed_breakout": False,
            "liquidity_deteriorated": False,
            "spread_widened": False,
            "volume_confirmed": False,
            "outcome_status": "data_insufficient",
            "final_outcome": "missing_entry_reference_price",
            "data_resolution_insufficient": False,
            "delay_source": "missing_entry_reference_price",
        }
    history = [row for row in (price_history or []) if isinstance(row, dict)]
    window_rows = []
    offsets: list[tuple[float, dict[str, Any]]] = []
    for row in history:
        offset = _offset_seconds(row, detected_at)
        if offset is not None and offset >= 0:
            offsets.append((offset, row))
    offsets = sorted(offsets, key=lambda item: item[0])
    delayed = False
    delay_source = "on_time_price_history"
    if seconds is None:
        window_rows = history
    else:
        window_rows = [row for offset, row in offsets if offset <= seconds]
    effective_seconds = seconds
    if not window_rows:
        if seconds is not None:
            late = [(offset, row) for offset, row in offsets if offset > seconds]
            if late:
                effective_seconds = late[0][0]
                window_rows = [row for offset, row in offsets if offset <= effective_seconds]
                delayed = True
                delay_source = str(late[0][1].get("delay_source") or late[0][1].get("source") or "late_price_history")
        if window_rows:
            pass
        else:
            pending_status = "delayed_pending" if seconds is not None else "pending"
            final = "delayed_price_window_pending" if seconds is not None else "pending_price_window"
            delay_source = "awaiting_price_history" if seconds is not None else "pending_price_history"
            delayed_by = None
            return {
                **base,
                "effective_window_seconds": None,
                "delayed_by_seconds": delayed_by,
                "delay_source": delay_source,
                "price_at_window": None,
                "high_since_detection": None,
                "low_since_detection": None,
                "max_favorable_excursion": None,
                "max_adverse_excursion": None,
                "follow_through_percent": None,
                "reversal_percent": None,
                "hit_trigger": False,
                "hit_target": False,
                "hit_stop": False,
                "failed_breakout": False,
                "liquidity_deteriorated": False,
                "spread_widened": False,
                "volume_confirmed": False,
                "outcome_status": pending_status,
                "final_outcome": final,
                "data_resolution_insufficient": False,
            }
    if not window_rows:
        return {
            **base,
            "price_at_window": None,
            "high_since_detection": None,
            "low_since_detection": None,
            "max_favorable_excursion": None,
            "max_adverse_excursion": None,
            "follow_through_percent": None,
            "reversal_percent": None,
            "hit_trigger": False,
            "hit_target": False,
            "hit_stop": False,
            "failed_breakout": False,
            "liquidity_deteriorated": False,
            "spread_widened": False,
            "volume_confirmed": False,
            "outcome_status": "pending",
            "final_outcome": "pending_price_window",
            "data_resolution_insufficient": False,
            "delay_source": "pending_price_history",
        }
    price_at_window = _price(window_rows[-1], "close") or _price(window_rows[-1], "price")
    highs = [_price(row, "high") or _price(row, "price") for row in window_rows]
    lows = [_price(row, "low") or _price(row, "price") for row in window_rows]
    highs = [value for value in highs if value is not None]
    lows = [value for value in lows if value is not None]
    high_since = max(highs) if highs else price_at_window
    low_since = min(lows) if lows else price_at_window
    if direction == "bearish":
        favorable = ((entry - (low_since or entry)) / entry) * 100.0
        adverse = (((high_since or entry) - entry) / entry) * 100.0
        hit_trigger = bool(trigger is not None and low_since is not None and low_since <= trigger)
        hit_target = bool(target is not None and low_since is not None and low_since <= target)
        hit_stop = bool(stop is not None and high_since is not None and high_since >= stop)
        follow = ((entry - (price_at_window or entry)) / entry) * 100.0
        reversal = (((high_since or entry) - entry) / entry) * 100.0
    else:
        favorable = (((high_since or entry) - entry) / entry) * 100.0
        adverse = ((entry - (low_since or entry)) / entry) * 100.0
        hit_trigger = bool(trigger is not None and high_since is not None and high_since >= trigger)
        hit_target = bool(target is not None and high_since is not None and high_since >= target)
        hit_stop = bool(stop is not None and low_since is not None and low_since <= stop)
        follow = (((price_at_window or entry) - entry) / entry) * 100.0
        reversal = ((entry - (low_since or entry)) / entry) * 100.0
    failed_breakout = bool(hit_trigger and (hit_stop or (price_at_window is not None and ((price_at_window < entry) if direction != "bearish" else (price_at_window > entry)))))
    first_spread = _num(window_rows[0].get("spread_percent"))
    spreads = [_num(row.get("spread_percent")) for row in window_rows]
    spreads = [value for value in spreads if value is not None]
    spread_widened = bool(first_spread is not None and spreads and max(spreads) >= first_spread * 1.5 and max(spreads) - first_spread >= 0.10)
    liquidity_scores = [_num(row.get("liquidity_score")) for row in window_rows]
    liquidity_scores = [value for value in liquidity_scores if value is not None]
    liquidity_deteriorated = bool(liquidity_scores and min(liquidity_scores) < 40)
    volumes = [_num(row.get("volume")) for row in window_rows]
    volumes = [value for value in volumes if value is not None]
    volume_confirmed = bool(volumes and volumes[-1] >= (sum(volumes) / len(volumes)))
    if hit_target:
        final = "target_hit"
    elif hit_stop:
        final = "stop_hit"
    elif failed_breakout:
        final = "failed_breakout"
    elif follow > 0:
        final = "follow_through"
    else:
        final = "reversal"
    return {
        **base,
        "effective_window_seconds": round(effective_seconds, 6) if effective_seconds is not None else None,
        "delayed_by_seconds": round(max(0.0, (effective_seconds or 0.0) - (seconds or effective_seconds or 0.0)), 6) if effective_seconds is not None and seconds is not None else 0.0,
        "delay_source": delay_source,
        "usable_for_calibration": True,
        "price_at_window": round(price_at_window, 6) if price_at_window is not None else None,
        "high_since_detection": round(high_since, 6) if high_since is not None else None,
        "low_since_detection": round(low_since, 6) if low_since is not None else None,
        "max_favorable_excursion": round(max(0.0, favorable), 6),
        "max_adverse_excursion": round(max(0.0, adverse), 6),
        "follow_through_percent": round(follow, 6),
        "reversal_percent": round(max(0.0, reversal), 6),
        "hit_trigger": hit_trigger,
        "hit_target": hit_target,
        "hit_stop": hit_stop,
        "failed_breakout": failed_breakout,
        "liquidity_deteriorated": liquidity_deteriorated,
        "spread_widened": spread_widened,
        "volume_confirmed": volume_confirmed,
        "outcome_status": "delayed_measured" if delayed else "settled",
        "final_outcome": final,
        "data_resolution_insufficient": False,
    }


def record_micro_outcome_windows(
    detection: dict[str, Any],
    price_history: list[dict[str, Any]] | None,
    *,
    data_resolution: str,
    windows: tuple[str, ...] = MICRO_OUTCOME_WINDOWS,
) -> dict[str, Any]:
    records = [
        settle_outcome_window(detection, price_history, outcome_window=window, data_resolution=data_resolution)
        for window in windows
    ]
    status_counts: dict[str, int] = {}
    for record in records:
        status = str(record.get("outcome_status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "ok": True,
        "status": "micro_outcomes_recorded",
        "created_at": utc_now_iso(),
        "detection_id": detection.get("detection_id"),
        "data_resolution": data_resolution,
        "records": records,
        "record_count": len(records),
        "status_counts": status_counts,
        "unsupported_windows": unsupported_windows_for_resolution(data_resolution, windows),
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
    }


def build_micro_calibration_report(records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = [row for row in (records or []) if isinstance(row, dict)]
    settled = [row for row in rows if row.get("outcome_status") == "settled" or (row.get("outcome_status") == "delayed_measured" and row.get("usable_for_calibration"))]
    segments: dict[str, dict[str, int]] = {}
    for row in rows:
        key = "|".join(
            [
                str(row.get("pattern_id") or "unknown"),
                str(row.get("asset_type") or "unknown"),
                str(row.get("timeframe") or "unknown"),
                str(row.get("data_resolution") or "unknown"),
            ]
        )
        bucket = segments.setdefault(key, {"sample_size": 0, "settled": 0, "data_insufficient": 0})
        bucket["sample_size"] += 1
        if row.get("outcome_status") == "settled" or (row.get("outcome_status") == "delayed_measured" and row.get("usable_for_calibration")):
            bucket["settled"] += 1
        if row.get("outcome_status") == "data_insufficient":
            bucket["data_insufficient"] += 1
    return {
        "ok": True,
        "status": "metrics_ready" if len(settled) >= 30 else "insufficient_data",
        "created_at": utc_now_iso(),
        "record_count": len(rows),
        "settled_count": len(settled),
        "sample_size": len(settled),
        "insufficient_sample": len(settled) < 30,
        "segments": segments,
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
    }

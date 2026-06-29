from __future__ import annotations

from typing import Any

from .scheduler_config import safe_run_id, utc_now_iso


HIGH_PRIORITY_PATTERNS = {
    "opening_range_breakout",
    "gap_and_go",
    "vwap_reclaim",
    "vwap_hold",
    "bull_flag_breakout",
    "abcd_pattern",
    "higher_low_continuation",
    "breakout_retest",
    "consecutive_green_momentum",
    "five_minute_new_high_breakout",
    "parabolic_momentum",
    "ema_pullback_continuation",
    "support_reclaim",
}
MEDIUM_PRIORITY_PATTERNS = {
    "marubozu",
    "bullish_engulfing",
    "bearish_engulfing",
    "hammer",
    "inverted_hammer",
    "shooting_star",
    "morning_star",
    "evening_star",
    "piercing_pattern",
    "dark_cloud_cover",
    "three_white_soldiers",
    "three_black_crows",
    "inside_bar_breakout",
    "outside_bar",
    "rising_three_methods",
    "falling_three_methods",
    "bullish_kicker",
    "bearish_kicker",
    "long_lower_wick",
    "long_upper_wick",
}
LOW_PRIORITY_PATTERNS = {
    "doji",
    "dragonfly_doji",
    "gravestone_doji",
    "spinning_top",
    "bullish_harami",
    "bearish_harami",
    "tweezer_top",
    "tweezer_bottom",
    "narrow_range_cluster",
    "failed_breakout",
    "failed_breakdown",
    "parabolic_blowoff",
}


PATTERN_CATALOG: dict[str, dict[str, Any]] = {
    **{pid: {"pattern_family": "momentum", "base_priority": 84.0, "direction": "bullish"} for pid in HIGH_PRIORITY_PATTERNS},
    **{pid: {"pattern_family": "continuation_reversal", "base_priority": 68.0, "direction": "neutral"} for pid in MEDIUM_PRIORITY_PATTERNS},
    **{pid: {"pattern_family": "confirmation_warning", "base_priority": 48.0, "direction": "neutral"} for pid in LOW_PRIORITY_PATTERNS},
}
for _pid in ("bearish_engulfing", "shooting_star", "evening_star", "dark_cloud_cover", "three_black_crows", "falling_three_methods", "bearish_kicker", "long_upper_wick"):
    PATTERN_CATALOG[_pid]["direction"] = "bearish"
for _pid in ("failed_breakout", "failed_breakdown", "parabolic_blowoff"):
    PATTERN_CATALOG[_pid]["direction"] = "warning"
for _pid in ("bullish_engulfing", "hammer", "inverted_hammer", "morning_star", "piercing_pattern", "three_white_soldiers", "rising_three_methods", "bullish_kicker", "long_lower_wick"):
    PATTERN_CATALOG[_pid]["direction"] = "bullish"
PATTERN_CATALOG["doji"]["direction"] = "neutral"


def get_pattern_catalog() -> dict[str, dict[str, Any]]:
    return {key: dict(value, pattern_id=key, pattern_name=key) for key, value in sorted(PATTERN_CATALOG.items())}


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, float(value)))


def _candle(row: dict[str, Any]) -> dict[str, Any]:
    open_price = _num(row.get("open", row.get("o")))
    high = _num(row.get("high", row.get("h")), open_price)
    low = _num(row.get("low", row.get("l")), open_price)
    close = _num(row.get("close", row.get("c")), open_price)
    volume = _num(row.get("volume", row.get("v")), 0.0)
    rng = max(0.000001, high - low)
    body = abs(close - open_price)
    upper_wick = high - max(open_price, close)
    lower_wick = min(open_price, close) - low
    return {
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "timestamp": row.get("timestamp") or row.get("time") or row.get("detected_at"),
        "range": rng,
        "body": body,
        "upper_wick": upper_wick,
        "lower_wick": lower_wick,
        "bullish": close > open_price,
        "bearish": close < open_price,
    }


def _volume_confirmation(candles: list[dict[str, Any]]) -> float:
    if len(candles) < 2:
        return 45.0
    current = candles[-1]["volume"]
    previous = [row["volume"] for row in candles[:-1] if row["volume"] > 0]
    if not previous:
        return 45.0
    avg = sum(previous) / len(previous)
    if avg <= 0:
        return 45.0
    ratio = current / avg
    return _clamp(35.0 + ratio * 25.0)


def _reward_risk(entry: float, stop: float, target: float, direction: str) -> float | None:
    if direction == "bearish":
        risk = stop - entry
        reward = entry - target
    else:
        risk = entry - stop
        reward = target - entry
    if risk <= 0 or reward <= 0:
        return None
    return round(reward / risk, 4)


def _build_pattern(
    pattern_id: str,
    candles: list[dict[str, Any]],
    context: dict[str, Any],
    *,
    quality_bonus: float = 0.0,
    trigger: float | None = None,
    stop: float | None = None,
    target: float | None = None,
) -> dict[str, Any]:
    last = candles[-1]
    meta = PATTERN_CATALOG[pattern_id]
    direction = str(meta["direction"])
    base = float(meta["base_priority"])
    volume_score = _volume_confirmation(candles)
    breakout_score = _clamp(float(context.get("breakout_confirmation_score", 50.0)) + quality_bonus)
    quality = _clamp(base * 0.65 + volume_score * 0.20 + breakout_score * 0.15 + quality_bonus)
    entry = trigger if trigger is not None else last["close"]
    if stop is None:
        stop = last["high"] if direction == "bearish" else last["low"]
    if target is None:
        risk_unit = abs(entry - stop) if abs(entry - stop) > 0 else max(last["range"], entry * 0.01)
        target = entry - risk_unit * 2.0 if direction == "bearish" else entry + risk_unit * 2.0
    rr = _reward_risk(entry, stop, target, direction)
    detected_at = context.get("detected_at") or last.get("timestamp") or utc_now_iso()
    symbol = str(context.get("asset_symbol") or context.get("symbol") or "UNKNOWN").upper()
    pattern_seed = f"{symbol}|{context.get('timeframe','unknown')}|{pattern_id}|{detected_at}|{entry}"
    return {
        "detection_id": safe_run_id("candlestick_detection", pattern_seed),
        "asset_symbol": symbol,
        "asset_type": str(context.get("asset_type") or "stock"),
        "timeframe": str(context.get("timeframe") or "unknown"),
        "pattern_id": pattern_id,
        "pattern_name": pattern_id,
        "pattern_family": meta["pattern_family"],
        "direction": direction,
        "detected_at": detected_at,
        "trigger_price": round(entry, 6),
        "invalidation_price": round(stop, 6),
        "target_price": round(target, 6),
        "pattern_quality_score": round(quality, 2),
        "pattern_base_priority_score": round(base, 2),
        "volume_confirmation_score": round(volume_score, 2),
        "breakout_confirmation_score": round(breakout_score, 2),
        "failed_pattern_risk": round(_clamp(100.0 - quality + (15.0 if pattern_id.startswith("failed_") else 0.0)), 2),
        "entry_trigger_price": round(entry, 6),
        "stop_loss_level": round(stop, 6),
        "reward_risk_ratio": rr,
        "review_only": True,
        "execution_allowed": False,
    }


def detect_candlestick_patterns(candles: list[dict[str, Any]] | None, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    context = context or {}
    parsed = [_candle(row) for row in (candles or []) if isinstance(row, dict)]
    if not parsed:
        return []
    patterns: list[dict[str, Any]] = []
    last = parsed[-1]
    prev = parsed[-2] if len(parsed) >= 2 else None

    body_ratio = last["body"] / last["range"]
    upper_ratio = last["upper_wick"] / last["range"]
    lower_ratio = last["lower_wick"] / last["range"]
    if body_ratio <= 0.10:
        patterns.append(_build_pattern("doji", parsed, context, quality_bonus=-5.0))
    if body_ratio >= 0.80:
        patterns.append(_build_pattern("marubozu", parsed, context, quality_bonus=8.0))
    if lower_ratio >= 0.55 and body_ratio <= 0.35:
        patterns.append(_build_pattern("hammer" if last["bullish"] else "long_lower_wick", parsed, context, quality_bonus=7.0))
    if upper_ratio >= 0.55 and body_ratio <= 0.35:
        patterns.append(_build_pattern("shooting_star" if last["bearish"] else "long_upper_wick", parsed, context, quality_bonus=7.0))

    if prev is not None:
        if last["bullish"] and prev["bearish"] and last["close"] >= prev["open"] and last["open"] <= prev["close"]:
            patterns.append(_build_pattern("bullish_engulfing", parsed, context, quality_bonus=10.0))
        if last["bearish"] and prev["bullish"] and last["open"] >= prev["close"] and last["close"] <= prev["open"]:
            patterns.append(_build_pattern("bearish_engulfing", parsed, context, quality_bonus=10.0))
        if last["high"] <= prev["high"] and last["low"] >= prev["low"]:
            patterns.append(_build_pattern("inside_bar_breakout", parsed, context, quality_bonus=0.0))
        if last["high"] > prev["high"] and last["low"] < prev["low"]:
            patterns.append(_build_pattern("outside_bar", parsed, context, quality_bonus=4.0))

    if len(parsed) >= 3:
        last3 = parsed[-3:]
        if all(row["bullish"] for row in last3) and all(last3[i]["close"] > last3[i - 1]["close"] for i in range(1, 3)):
            patterns.append(_build_pattern("three_white_soldiers", parsed, context, quality_bonus=12.0))
            patterns.append(_build_pattern("consecutive_green_momentum", parsed, context, quality_bonus=14.0, trigger=last["high"]))
        if all(row["bearish"] for row in last3) and all(last3[i]["close"] < last3[i - 1]["close"] for i in range(1, 3)):
            patterns.append(_build_pattern("three_black_crows", parsed, context, quality_bonus=12.0))
        if last["low"] > parsed[-2]["low"] > parsed[-3]["low"] and last["close"] > parsed[-2]["close"]:
            patterns.append(_build_pattern("higher_low_continuation", parsed, context, quality_bonus=10.0, trigger=last["high"], stop=parsed[-2]["low"]))

    opening_range_high = context.get("opening_range_high")
    if opening_range_high is not None and last["close"] > _num(opening_range_high):
        patterns.append(_build_pattern("opening_range_breakout", parsed, context, quality_bonus=14.0, trigger=last["high"], stop=_num(opening_range_high)))
    prev_close = context.get("previous_close")
    if prev_close is not None and parsed[0]["open"] > _num(prev_close) * 1.03 and last["close"] > parsed[0]["open"]:
        patterns.append(_build_pattern("gap_and_go", parsed, context, quality_bonus=13.0, trigger=last["high"], stop=parsed[0]["open"]))
    vwap = context.get("vwap")
    if vwap is not None:
        vwap_value = _num(vwap)
        if prev is not None and prev["close"] < vwap_value <= last["close"]:
            patterns.append(_build_pattern("vwap_reclaim", parsed, context, quality_bonus=12.0, trigger=last["close"], stop=vwap_value * 0.995))
        elif last["low"] <= vwap_value <= last["close"]:
            patterns.append(_build_pattern("vwap_hold", parsed, context, quality_bonus=8.0, trigger=last["high"], stop=vwap_value * 0.995))
    pullback_high = context.get("pullback_high")
    if pullback_high is not None and last["close"] > _num(pullback_high):
        patterns.append(_build_pattern("bull_flag_breakout", parsed, context, quality_bonus=13.0, trigger=last["high"], stop=min(row["low"] for row in parsed[-min(5, len(parsed)) :])))
    prior_high = context.get("prior_high")
    if prior_high is not None and last["close"] > _num(prior_high):
        patterns.append(_build_pattern("five_minute_new_high_breakout", parsed, context, quality_bonus=11.0, trigger=last["high"], stop=_num(prior_high)))
    if len(parsed) >= 5:
        first_close = parsed[-5]["close"]
        if first_close > 0 and (last["close"] - first_close) / first_close >= 0.12 and _volume_confirmation(parsed) >= 75:
            patterns.append(_build_pattern("parabolic_momentum", parsed, context, quality_bonus=7.0, trigger=last["high"], stop=parsed[-2]["low"]))

    unique: dict[str, dict[str, Any]] = {}
    for pattern in patterns:
        existing = unique.get(pattern["pattern_id"])
        if existing is None or float(pattern["pattern_quality_score"]) > float(existing["pattern_quality_score"]):
            unique[pattern["pattern_id"]] = pattern
    return sorted(unique.values(), key=lambda row: (-float(row["pattern_quality_score"]), str(row["pattern_id"])))

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def seconds_since(timestamp: Any, now: datetime | None = None) -> int | None:
    parsed = parse_timestamp(timestamp)
    if parsed is None:
        return None
    current = now or utc_now()
    return max(0, int((current - parsed).total_seconds()))


def is_market_closed(item: dict[str, Any], now: datetime | None = None) -> bool:
    current = now or utc_now()
    status = str(item.get("status") or "").lower()
    if status in {"closed", "settled", "resolved", "final"}:
        return True
    close_at = parse_timestamp(item.get("market_close_at") or item.get("close_at"))
    return bool(close_at and close_at <= current)


def is_stale(item: dict[str, Any], now: datetime | None = None) -> bool:
    current = now or utc_now()
    stale_after_seconds = int(item.get("stale_after_seconds") or 0)
    if stale_after_seconds <= 0:
        return False
    reference = (
        item.get("updated_at")
        or item.get("snapshot_at")
        or item.get("created_at")
    )
    age = seconds_since(reference, current)
    return bool(age is not None and age >= stale_after_seconds)


def apply_score_decay(score: float, age_seconds: int, *, decay_window_seconds: int = 900) -> float:
    if age_seconds <= 0:
        return round(score, 2)
    decay_steps = age_seconds // max(1, decay_window_seconds)
    return round(max(0.0, float(score) - (decay_steps * 3.0)), 2)


def market_open_status(market_type: str, now: datetime | None = None) -> dict[str, Any]:
    current = now or utc_now()
    hour = current.hour
    if market_type in {"news", "news_events"}:
        return {"is_open": True, "reason": "always_open_news", "next_check_allowed": current.isoformat()}
    if market_type in {"low_liquidity"}:
        return {"is_open": True, "reason": "low_liquidity_polling", "next_check_allowed": current.isoformat()}
    if market_type in {"stock", "stocks_watchlist"}:
        is_open = 13 <= hour <= 20
        return {"is_open": is_open, "reason": "market_hours" if is_open else "outside_market_hours", "next_check_allowed": current.isoformat()}
    return {"is_open": True, "reason": "placeholder_open", "next_check_allowed": current.isoformat()}

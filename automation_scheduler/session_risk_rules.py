from __future__ import annotations

from datetime import datetime, time, timezone
from typing import Any


SESSION_BUCKETS = (
    "PREMARKET",
    "OPENING_DRIVE",
    "MORNING_MOMENTUM",
    "MIDDAY_CHOP",
    "AFTERNOON_RECLAIM",
    "POWER_HOUR",
    "AFTER_HOURS",
)


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value.strip():
        text = value.strip().replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            return None
    return None


def _minutes_since_midnight(dt: datetime | None, minutes: Any = None) -> int | None:
    if minutes is not None:
        try:
            parsed = int(minutes)
            if 0 <= parsed <= 24 * 60:
                return parsed
        except (TypeError, ValueError):
            pass
    if dt is None:
        return None
    return dt.hour * 60 + dt.minute


def classify_session_time(value: Any = None, *, minutes_since_midnight: int | None = None) -> str:
    dt = _parse_datetime(value)
    minutes = _minutes_since_midnight(dt, minutes_since_midnight)
    if minutes is None:
        return "DATA_INSUFFICIENT"
    market_open = 9 * 60 + 30
    if minutes < market_open:
        return "PREMARKET"
    if minutes < 10 * 60:
        return "OPENING_DRIVE"
    if minutes < 11 * 60:
        return "MORNING_MOMENTUM"
    if minutes < 14 * 60:
        return "MIDDAY_CHOP"
    if minutes < 15 * 60 + 30:
        return "AFTERNOON_RECLAIM"
    if minutes < 16 * 60:
        return "POWER_HOUR"
    return "AFTER_HOURS"


def score_time_of_day(value: Any = None, *, minutes_since_midnight: int | None = None) -> dict[str, Any]:
    bucket = classify_session_time(value, minutes_since_midnight=minutes_since_midnight)
    base_scores = {
        "PREMARKET": 55.0,
        "OPENING_DRIVE": 92.0,
        "MORNING_MOMENTUM": 84.0,
        "MIDDAY_CHOP": 42.0,
        "AFTERNOON_RECLAIM": 62.0,
        "POWER_HOUR": 74.0,
        "AFTER_HOURS": 34.0,
        "DATA_INSUFFICIENT": 45.0,
    }
    score = base_scores[bucket]
    return {
        "session_time_bucket": bucket,
        "premarket_score": 70.0 if bucket == "PREMARKET" else 0.0,
        "opening_drive_score": 95.0 if bucket == "OPENING_DRIVE" else 0.0,
        "morning_momentum_score": 88.0 if bucket in {"OPENING_DRIVE", "MORNING_MOMENTUM"} else 0.0,
        "midday_decay_risk": 80.0 if bucket == "MIDDAY_CHOP" else (45.0 if bucket == "AFTERNOON_RECLAIM" else 20.0),
        "afternoon_chop_risk": 70.0 if bucket in {"AFTERNOON_RECLAIM", "POWER_HOUR"} else (85.0 if bucket == "AFTER_HOURS" else 25.0),
        "time_of_day_edge_score": score,
        "session_quality_score": score,
        "calibration_bucket_required": True,
    }


def evaluate_session_risk(session: dict[str, Any] | None) -> dict[str, Any]:
    session = session or {}
    session_profit = _num(session.get("session_profit"))
    peak_session_profit = _num(session.get("peak_session_profit"), session_profit)
    consecutive_loss_count = int(_num(session.get("consecutive_loss_count"), 0.0))
    max_consecutive_losses = int(_num(session.get("max_consecutive_losses"), 3.0))
    daily_giveback_limit_percent = _num(session.get("daily_giveback_limit_percent"), 20.0)
    idle_minutes = _num(session.get("idle_time_without_a_quality_setup_minutes"), 0.0)
    max_idle_minutes = _num(session.get("max_idle_minutes"), 60.0)
    giveback_percent = 0.0
    if peak_session_profit > 0 and session_profit < peak_session_profit:
        giveback_percent = (peak_session_profit - session_profit) / peak_session_profit * 100.0

    reasons: list[str] = []
    status = "ALLOW_REVIEW"
    kill_switch = False
    profit_protection_mode = False
    overtrading_risk = 0.0
    if giveback_percent >= daily_giveback_limit_percent:
        status = "NO_TRADE_SESSION_LOCK"
        kill_switch = True
        profit_protection_mode = True
        reasons.append("daily_giveback_limit_reached")
    if consecutive_loss_count >= max_consecutive_losses:
        status = "COOLDOWN" if not kill_switch else status
        kill_switch = True
        overtrading_risk += 35.0
        reasons.append("max_consecutive_losses_reached")
    if idle_minutes >= max_idle_minutes:
        if status == "ALLOW_REVIEW":
            status = "REDUCE_PRIORITY"
        overtrading_risk += 25.0
        reasons.append("idle_without_a_quality_setup")
    if session_profit > 0 and giveback_percent > 0:
        profit_protection_mode = True
        overtrading_risk += min(25.0, giveback_percent)

    session_risk_score = max(0.0, 100.0 - overtrading_risk - (60.0 if kill_switch else 0.0))
    return {
        "session_profit": session_profit,
        "peak_session_profit": peak_session_profit,
        "giveback_percent": round(giveback_percent, 4),
        "daily_giveback_limit_percent": daily_giveback_limit_percent,
        "consecutive_loss_count": consecutive_loss_count,
        "max_consecutive_losses": max_consecutive_losses,
        "idle_time_without_a_quality_setup_minutes": idle_minutes,
        "max_idle_minutes": max_idle_minutes,
        "profit_protection_mode": profit_protection_mode,
        "overtrading_risk": round(min(100.0, overtrading_risk), 2),
        "session_kill_switch_active": kill_switch,
        "session_permission_status": status,
        "session_risk_score": round(session_risk_score, 2),
        "walk_away_reasons": sorted(set(reasons)),
    }

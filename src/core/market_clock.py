from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any


FLOAT_TOLERANCE = 1e-12


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _finite_float(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric.")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric.") from exc
    if math.isnan(numeric):
        raise ValueError(f"{name} must not be NaN.")
    if math.isinf(numeric):
        raise ValueError(f"{name} must be finite.")
    return numeric


def _non_negative_seconds(value: Any, name: str) -> float:
    seconds = _finite_float(value, name)
    if seconds < 0.0:
        raise ValueError(f"{name} must be non-negative seconds.")
    return seconds


def _positive_duration_seconds(value: Any, name: str) -> float:
    if isinstance(value, timedelta):
        seconds = value.total_seconds()
    else:
        seconds = _finite_float(value, name)
    if seconds <= 0.0:
        raise ValueError(f"{name} must be positive seconds.")
    return seconds


def to_iso8601_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_time_risk_timestamp(value: Any, *, name: str = "timestamp") -> datetime:
    """Return a timezone-aware timestamp normalized to Coordinated Universal Time.

    The time-risk contract is stricter than legacy parsing: timestamps must be
    explicit and timezone-aware so observation, evaluation, and event times are
    never silently substituted.
    """
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError(f"{name} must be a timezone-aware timestamp.")
        candidate = text[:-1] + "+00:00" if text.endswith("Z") else text
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError as exc:
            raise ValueError(f"{name} must be a timezone-aware timestamp.") from exc
    else:
        raise ValueError(f"{name} must be a timezone-aware timestamp.")

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{name} must include timezone information.")
    return parsed.astimezone(timezone.utc)


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


def information_age_seconds(
    information_available_at: Any,
    evaluation_time: Any,
    *,
    allow_negative: bool = False,
) -> float:
    """Seconds between information availability and evaluation time."""
    available_at = normalize_time_risk_timestamp(
        information_available_at,
        name="information_available_at",
    )
    evaluated_at = normalize_time_risk_timestamp(evaluation_time, name="evaluation_time")
    age = (evaluated_at - available_at).total_seconds()
    if age < 0.0 and not allow_negative:
        raise ValueError("information_available_at must be at or before evaluation_time.")
    return age


def freshness_decay_weight(age_seconds: Any, *, half_life_seconds: Any) -> float:
    """Exponential freshness weight using an explicit half-life in seconds."""
    age = _non_negative_seconds(age_seconds, "age_seconds")
    half_life = _positive_duration_seconds(half_life_seconds, "half_life_seconds")
    weight = 0.5 ** (age / half_life)
    if not math.isfinite(weight):
        raise ValueError("freshness weight must be finite.")
    return min(1.0, max(0.0, weight))


def _confidence_bound(confidence_scale: str) -> float:
    scale = str(confidence_scale).strip().lower()
    if scale == "unit":
        return 1.0
    if scale == "percent":
        return 100.0
    raise ValueError("confidence_scale must be 'unit' or 'percent'.")


def _confidence_scale_key(confidence_scale: str) -> str:
    scale = str(confidence_scale).strip().lower()
    _confidence_bound(scale)
    return scale


def _validate_confidence(value: Any, *, confidence_scale: str) -> float:
    confidence = _finite_float(value, "base_confidence")
    upper_bound = _confidence_bound(confidence_scale)
    if confidence < 0.0 or confidence > upper_bound:
        raise ValueError(f"base_confidence must be between 0 and {upper_bound:g}.")
    return confidence


def _validate_freshness_weight(value: Any) -> float:
    weight = _finite_float(value, "freshness_weight")
    if weight < 0.0 or weight > 1.0:
        raise ValueError("freshness_weight must be between 0 and 1.")
    return weight


def adjust_confidence_for_freshness(
    base_confidence: Any,
    freshness_weight: Any,
    *,
    confidence_scale: str = "unit",
) -> dict[str, Any]:
    """Apply freshness weight to a supplied confidence value without mutation."""
    base = _validate_confidence(base_confidence, confidence_scale=confidence_scale)
    weight = _validate_freshness_weight(freshness_weight)
    return {
        "base_confidence": base,
        "freshness_weight": weight,
        "effective_confidence": base * weight,
        "confidence_scale": str(confidence_scale).strip().lower(),
        "confidence_adjustment": "base_confidence * freshness_weight",
    }


def time_to_event_seconds(event_time: Any, evaluation_time: Any) -> float:
    """Seconds from evaluation time to event time; negative means post-event."""
    event_at = normalize_time_risk_timestamp(event_time, name="event_time")
    evaluated_at = normalize_time_risk_timestamp(evaluation_time, name="evaluation_time")
    return (event_at - evaluated_at).total_seconds()


def _event_state(seconds_to_event: float) -> str:
    if math.isclose(seconds_to_event, 0.0, rel_tol=0.0, abs_tol=FLOAT_TOLERANCE):
        return "at_event_boundary"
    if seconds_to_event > 0.0:
        return "pre_event"
    return "post_event"


def holding_horizon_state(holding_horizon_seconds: Any) -> dict[str, Any]:
    """Represent intended holding horizon without applying unsupported scaling."""
    seconds = _positive_duration_seconds(holding_horizon_seconds, "holding_horizon_seconds")
    return {
        "holding_horizon_seconds": seconds,
        "holding_horizon_unit": "seconds",
        "risk_scaling_applied": False,
        "scaling_assumption": "none",
    }


def forecast_horizon_state(forecast_horizon_seconds: Any) -> dict[str, Any]:
    """Represent forecast horizon without inventing calibration."""
    seconds = _positive_duration_seconds(forecast_horizon_seconds, "forecast_horizon_seconds")
    return {
        "forecast_horizon_seconds": seconds,
        "forecast_horizon_unit": "seconds",
        "calibration_assumption": "none",
    }


def time_dependent_risk_state(
    *,
    evaluation_time: Any,
    information_available_at: Any,
    event_time: Any | None = None,
    holding_horizon_seconds: Any | None = None,
    forecast_horizon_seconds: Any | None = None,
    freshness_half_life_seconds: Any | None = None,
    base_confidence: Any | None = None,
    confidence_scale: str = "unit",
) -> dict[str, Any]:
    """Build a reproducible, provider-agnostic time-dependent risk state."""
    confidence_scale_key = _confidence_scale_key(confidence_scale)
    evaluated_at = normalize_time_risk_timestamp(evaluation_time, name="evaluation_time")
    available_at = normalize_time_risk_timestamp(
        information_available_at,
        name="information_available_at",
    )
    age_seconds = information_age_seconds(available_at, evaluated_at)

    freshness_weight: float | None = None
    freshness_model = "not_applied"
    half_life_seconds: float | None = None
    if freshness_half_life_seconds is not None:
        half_life_seconds = _positive_duration_seconds(
            freshness_half_life_seconds,
            "freshness_half_life_seconds",
        )
        freshness_weight = freshness_decay_weight(
            age_seconds,
            half_life_seconds=half_life_seconds,
        )
        freshness_model = "exponential_half_life"

    confidence_payload: dict[str, Any] = {
        "base_confidence": None,
        "confidence_scale": confidence_scale_key,
        "effective_confidence": None,
        "confidence_adjustment_applied": False,
    }
    if base_confidence is not None:
        confidence_weight = freshness_weight if freshness_weight is not None else 1.0
        adjusted = adjust_confidence_for_freshness(
            base_confidence,
            confidence_weight,
            confidence_scale=confidence_scale_key,
        )
        confidence_payload = {
            "base_confidence": adjusted["base_confidence"],
            "confidence_scale": adjusted["confidence_scale"],
            "effective_confidence": adjusted["effective_confidence"],
            "confidence_adjustment": adjusted["confidence_adjustment"],
            "confidence_adjustment_applied": freshness_weight is not None,
        }

    event_payload: dict[str, Any] = {
        "event_time": None,
        "time_to_event_seconds": None,
        "time_to_event_unit": "seconds",
        "event_state": None,
    }
    if event_time is not None:
        seconds_to_event = time_to_event_seconds(event_time, evaluated_at)
        event_payload = {
            "event_time": to_iso8601_utc(
                normalize_time_risk_timestamp(event_time, name="event_time")
            ),
            "time_to_event_seconds": seconds_to_event,
            "time_to_event_unit": "seconds",
            "event_state": _event_state(seconds_to_event),
        }

    holding_payload = {
        "holding_horizon_seconds": None,
        "holding_horizon_unit": "seconds",
        "risk_scaling_applied": False,
        "scaling_assumption": "none",
    }
    if holding_horizon_seconds is not None:
        holding_payload = holding_horizon_state(holding_horizon_seconds)

    forecast_payload = {
        "forecast_horizon_seconds": None,
        "forecast_horizon_unit": "seconds",
        "calibration_assumption": "none",
    }
    if forecast_horizon_seconds is not None:
        forecast_payload = forecast_horizon_state(forecast_horizon_seconds)

    return {
        "ok": True,
        "status": "ready",
        "evaluation_time": to_iso8601_utc(evaluated_at),
        "information_available_at": to_iso8601_utc(available_at),
        "information_age_seconds": age_seconds,
        "information_age_unit": "seconds",
        "freshness_model": freshness_model,
        "freshness_half_life_seconds": half_life_seconds,
        "freshness_weight": freshness_weight,
        **confidence_payload,
        **event_payload,
        **holding_payload,
        **forecast_payload,
        "point_in_time_safe": True,
        "exposure_mutation_applied": False,
    }


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


__all__ = [
    "adjust_confidence_for_freshness",
    "apply_score_decay",
    "forecast_horizon_state",
    "freshness_decay_weight",
    "holding_horizon_state",
    "information_age_seconds",
    "is_market_closed",
    "is_stale",
    "market_open_status",
    "normalize_time_risk_timestamp",
    "parse_timestamp",
    "seconds_since",
    "time_dependent_risk_state",
    "time_to_event_seconds",
    "to_iso8601_utc",
    "utc_now",
]

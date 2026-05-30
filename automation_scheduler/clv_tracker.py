from __future__ import annotations

import json
from pathlib import Path
from statistics import median
from typing import Any

from .data_paths import get_runtime_data_path
from .scheduler_config import SCHEMA_VERSION, redact_secrets, sanitize_filename, utc_now_iso

def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _american_to_implied_probability(odds: Any) -> float:
    american = _to_float(odds)
    if american == 0:
        return 0.0
    if american > 0:
        return 100.0 / (american + 100.0)
    return abs(american) / (abs(american) + 100.0)


def calculate_clv_percent(recommended_implied_probability: float, closing_implied_probability: float) -> float:
    return round((_to_float(closing_implied_probability) - _to_float(recommended_implied_probability)) * 100.0, 4)


def calculate_clv_for_american_odds(recommended_odds: float, closing_odds: float) -> float:
    recommended_ip = _american_to_implied_probability(recommended_odds)
    closing_ip = _american_to_implied_probability(closing_odds)
    return calculate_clv_percent(recommended_ip, closing_ip)


def calculate_positive_clv_rate(clv_values: list[float]) -> float:
    if not clv_values:
        return 0.0
    positives = sum(1 for value in clv_values if _to_float(value) > 0)
    return round(positives / len(clv_values), 4)


def detect_clv_decay(clv_values: list[float], threshold_percent: float = 1.5) -> bool:
    if len(clv_values) < 6:
        return False
    values = [_to_float(v) for v in clv_values]
    midpoint = len(values) // 2
    early_avg = sum(values[:midpoint]) / max(1, len(values[:midpoint]))
    late_avg = sum(values[midpoint:]) / max(1, len(values[midpoint:]))
    return (early_avg - late_avg) >= _to_float(threshold_percent, default=1.5)


def _build_summary(clv_values: list[float]) -> dict[str, Any]:
    values = [_to_float(v) for v in clv_values]
    if not values:
        return {
            "average_clv_percent": 0.0,
            "median_clv_percent": 0.0,
            "positive_clv_rate": 0.0,
            "clv_sample_size": 0,
            "clv_decay_detected": False,
        }
    return {
        "average_clv_percent": round(sum(values) / len(values), 4),
        "median_clv_percent": round(float(median(values)), 4),
        "positive_clv_rate": calculate_positive_clv_rate(values),
        "clv_sample_size": len(values),
        "clv_decay_detected": detect_clv_decay(values),
    }


def summarize_clv_by_model(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_model: dict[str, list[float]] = {}
    for entry in entries:
        if entry.get("closing_odds") is None or entry.get("recommended_odds") is None:
            continue
        model_id = str(entry.get("model_id") or "unknown_model")
        by_model.setdefault(model_id, []).append(
            calculate_clv_for_american_odds(entry.get("recommended_odds"), entry.get("closing_odds"))
        )
    return {model_id: _build_summary(values) for model_id, values in by_model.items()}


def summarize_clv_by_market(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_market: dict[str, list[float]] = {}
    for entry in entries:
        if entry.get("closing_odds") is None or entry.get("recommended_odds") is None:
            continue
        market = str(entry.get("market_type") or "unknown_market")
        by_market.setdefault(market, []).append(
            calculate_clv_for_american_odds(entry.get("recommended_odds"), entry.get("closing_odds"))
        )
    return {market: _build_summary(values) for market, values in by_market.items()}


def calculate_clv(opening_odds: Any, current_odds: Any, closing_odds: Any | None = None) -> dict[str, float]:
    opening = _to_float(opening_odds)
    current = _to_float(current_odds)
    closing = _to_float(closing_odds if closing_odds is not None else current_odds)
    return {
        "opening_to_current": round(current - opening, 4),
        "opening_to_closing": round(closing - opening, 4),
        "current_to_closing": round(closing - current, 4),
    }


def build_clv_record(payload: dict[str, Any]) -> dict[str, Any]:
    odds_delta = calculate_clv(payload.get("opening_odds"), payload.get("current_odds"), payload.get("closing_odds"))
    return {
        "schema_version": SCHEMA_VERSION,
        "recorded_at": utc_now_iso(),
        "candidate_type": "clv_watch",
        "event": payload.get("event"),
        "market": payload.get("market"),
        "selection": payload.get("selection"),
        "opening_odds": payload.get("opening_odds"),
        "current_odds": payload.get("current_odds"),
        "closing_odds": payload.get("closing_odds"),
        "clv": odds_delta,
        "human_approval_required": True,
        "auto_execution_enabled": False,
    }


def write_clv_record(payload: dict[str, Any], *, base_dir: str = "data/reports") -> dict[str, Any]:
    record = build_clv_record(payload)
    normalized = str(base_dir).replace("\\", "/").rstrip("/")
    directory = get_runtime_data_path("reports") if normalized == "data/reports" else Path(base_dir)
    directory.mkdir(parents=True, exist_ok=True)
    name = sanitize_filename(f"clv_{payload.get('event', 'event')}_{payload.get('selection', 'selection')}")
    path = directory / f"{name}.json"
    path.write_text(json.dumps(redact_secrets(record), indent=2, sort_keys=True), encoding="utf-8")
    return {"path": str(path), "record": record}

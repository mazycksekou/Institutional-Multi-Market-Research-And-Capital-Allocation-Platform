from __future__ import annotations

from typing import Any, Mapping

from ._shared import clamp, safe_float


def build_targets(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    data = dict(payload or {})
    data.update(overrides)
    current = safe_float(data.get("current_price_or_odds") or data.get("current") or data.get("price"))
    support = safe_float(data.get("support"))
    resistance = safe_float(data.get("resistance"))
    expected_move = safe_float(data.get("expected_move"))
    bias = str(data.get("bias") or "neutral").lower()
    if current is None:
        current = 0.0
    if expected_move is None:
        expected_move = abs(current) * 0.05 if current else 1.0
    if support is None:
        support = current - expected_move
    if resistance is None:
        resistance = current + expected_move
    if bias in {"bullish", "long", "over", "yes"}:
        primary = resistance
        secondary = resistance + expected_move * 0.5
        stretch = resistance + expected_move
    elif bias in {"bearish", "short", "under", "no"}:
        primary = support
        secondary = support - expected_move * 0.5
        stretch = support - expected_move
    else:
        primary = current
        secondary = resistance
        stretch = support
    return {
        "primary_target": round(clamp(primary), 4),
        "secondary_target": round(clamp(secondary), 4),
        "stretch_target": round(clamp(stretch), 4),
        "expected_move": round(abs(expected_move), 4),
        "support": round(clamp(support), 4),
        "resistance": round(clamp(resistance), 4),
    }


def build_market_targets(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    return build_targets(payload, **overrides)

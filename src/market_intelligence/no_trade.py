from __future__ import annotations

from typing import Any, Mapping

from ._shared import clamp
from .risk import build_no_trade_reason


def evaluate_no_trade(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    data = dict(payload or {})
    data.update(overrides)
    confidence = clamp(data.get("confidence") or 0.0)
    risk = clamp(data.get("risk") or 0.0)
    liquidity = clamp(data.get("liquidity") or data.get("liquidity_score") or 0.0)
    regime = data.get("regime")
    reason = build_no_trade_reason(confidence=confidence, risk=risk, liquidity=liquidity, regime=regime)
    return {
        "no_trade": reason != "none",
        "no_trade_reason": reason,
        "no_trade_zone": reason != "none",
    }

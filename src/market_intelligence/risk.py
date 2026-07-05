from __future__ import annotations

from typing import Any, Mapping

from ._shared import clamp, compact_list, normalize_text, weighted_average


def build_risk_profile(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    data = dict(payload or {})
    data.update(overrides)
    risk_score = weighted_average(
        (
            (data.get("volatility_risk"), 1.0),
            (data.get("liquidity_risk"), 1.0),
            (data.get("event_risk"), 0.9),
            (data.get("regime_risk"), 0.8),
            (data.get("execution_risk"), 0.7),
        )
    )
    value = clamp(risk_score if risk_score is not None else data.get("risk", 0.0))
    invalidation = str(data.get("invalidation") or data.get("stop") or "")
    return {
        "risk": round(value, 2),
        "risk_label": "high" if value >= 70.0 else "medium" if value >= 40.0 else "low",
        "stop": data.get("stop"),
        "invalidation": invalidation,
        "risk_notes": compact_list(data.get("risk_notes"), limit=8),
    }


def build_no_trade_reason(*, confidence: Any = None, risk: Any = None, liquidity: Any = None, regime: Any = None) -> str:
    parts = []
    if clamp(confidence or 0.0) < 35.0:
        parts.append("low_confidence")
    if clamp(risk or 0.0) >= 70.0:
        parts.append("elevated_risk")
    if clamp(liquidity or 0.0) < 35.0:
        parts.append("thin_liquidity")
    if normalize_text(regime) in {"risk_off", "volatile", "uncertain"}:
        parts.append(f"regime_{normalize_text(regime)}")
    return "; ".join(parts) if parts else "none"


def evaluate_market_risk(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    return build_risk_profile(payload, **overrides)

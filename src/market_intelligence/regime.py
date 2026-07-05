from __future__ import annotations

from typing import Any, Mapping

from ._shared import clamp, normalize_text


def classify_regime(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    data = dict(payload or {})
    data.update(overrides)
    market = normalize_text(data.get("market") or data.get("asset_type") or data.get("market_type"))
    volatility = clamp(data.get("volatility") or data.get("volatility_score") or 0.0)
    liquidity = clamp(data.get("liquidity") or data.get("liquidity_score") or 0.0)
    if volatility >= 70.0 and liquidity < 45.0:
        regime = "volatile"
    elif liquidity < 35.0:
        regime = "risk_off"
    elif volatility < 30.0 and liquidity >= 60.0:
        regime = "stable"
    else:
        regime = "balanced"
    return {
        "regime": regime,
        "market": market,
        "regime_score": round(clamp((100.0 - abs(50.0 - volatility)) * 0.5 + liquidity * 0.5), 2),
    }


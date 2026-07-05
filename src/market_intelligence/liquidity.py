from __future__ import annotations

from typing import Any, Mapping

from ._shared import build_band, clamp, safe_float


def build_liquidity_zones(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    data = dict(payload or {})
    data.update(overrides)
    current = safe_float(data.get("current_price_or_odds") or data.get("current") or data.get("price"))
    support = safe_float(data.get("support"))
    resistance = safe_float(data.get("resistance"))
    spread = safe_float(data.get("spread") or data.get("bid_ask_spread")) or 0.0
    depth = safe_float(data.get("depth") or data.get("order_book_depth"))
    zones = []
    if current is not None:
        zones.extend(build_band(current, spread=spread or abs(current) * 0.02))
    if support is not None:
        zones.append({"label": "support", "value": round(support, 4)})
    if resistance is not None:
        zones.append({"label": "resistance", "value": round(resistance, 4)})
    return {
        "liquidity_zones": zones[:8],
        "liquidity_score": round(clamp(depth if depth is not None else data.get("liquidity_score", 0.0)), 2),
    }


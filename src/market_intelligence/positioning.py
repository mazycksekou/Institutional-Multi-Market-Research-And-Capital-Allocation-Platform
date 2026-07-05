from __future__ import annotations

from typing import Any, Mapping

from ._shared import build_text_summary, clamp, safe_float


def build_positioning_summary(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    data = dict(payload or {})
    data.update(overrides)
    current = safe_float(data.get("current_price_or_odds") or data.get("current") or data.get("price"))
    support = safe_float(data.get("support"))
    resistance = safe_float(data.get("resistance"))
    zones = data.get("positioning_zones") or []
    summary = build_text_summary(
        [
            f"support={round(support, 4)}" if support is not None else "",
            f"resistance={round(resistance, 4)}" if resistance is not None else "",
            f"current={round(current, 4)}" if current is not None else "",
            data.get("positioning_note"),
        ]
    )
    return {
        "positioning_summary": summary,
        "positioning_zones": list(zones)[:10],
        "support": round(clamp(support), 4) if support is not None else None,
        "resistance": round(clamp(resistance), 4) if resistance is not None else None,
    }


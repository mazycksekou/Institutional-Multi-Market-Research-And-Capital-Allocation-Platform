from __future__ import annotations

from typing import Any, Mapping

from ._shared import build_text_summary, clamp, safe_float


def build_flow_summary(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    data = dict(payload or {})
    data.update(overrides)
    current = safe_float(data.get("current_price_or_odds") or data.get("current") or data.get("price"))
    volume = safe_float(data.get("volume") or data.get("handle"))
    open_interest = safe_float(data.get("open_interest"))
    tickets = safe_float(data.get("tickets"))
    money = safe_float(data.get("money"))
    reverse_line_movement = bool(data.get("reverse_line_movement"))
    parts = []
    if volume is not None:
        parts.append(f"volume={round(volume, 4)}")
    if open_interest is not None:
        parts.append(f"open_interest={round(open_interest, 4)}")
    if tickets is not None:
        parts.append(f"tickets={round(tickets, 4)}")
    if money is not None:
        parts.append(f"money={round(money, 4)}")
    if reverse_line_movement:
        parts.append("reverse_line_movement_detected")
    return {
        "flow_summary": build_text_summary(parts),
        "flow_strength": round(clamp((volume or 0.0) / 1000.0), 2),
        "reverse_line_movement": reverse_line_movement,
    }


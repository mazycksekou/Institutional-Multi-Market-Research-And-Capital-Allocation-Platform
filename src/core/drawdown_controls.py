from __future__ import annotations

from typing import Any


def apply_drawdown_controls(stake_fraction: float, state: dict[str, Any]) -> dict[str, Any]:
    drawdown = float(state.get("current_drawdown_percent", 0))
    action = "review_required"
    adjusted = max(0.0, float(stake_fraction))
    gate_result = "pass"
    if drawdown >= 20:
        adjusted = 0.0
        action = "pause_review"
        gate_result = "blocked"
    elif drawdown >= 12:
        adjusted = adjusted * 0.5
        gate_result = "reduced_half"
    elif drawdown >= 8:
        adjusted = adjusted * 0.75
        gate_result = "reduced_quarter"
    return {
        "drawdown_gate_result": gate_result,
        "current_drawdown_percent": drawdown,
        "adjusted_stake_fraction": round(adjusted, 6),
        "action": action,
    }

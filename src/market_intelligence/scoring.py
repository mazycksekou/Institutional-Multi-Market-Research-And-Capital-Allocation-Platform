from __future__ import annotations

from typing import Any, Mapping

from ._shared import clamp, weighted_average


def score_signal(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    data = dict(payload or {})
    data.update(overrides)
    score = weighted_average(
        (
            (data.get("confidence"), 1.1),
            (data.get("liquidity_score"), 1.0),
            (data.get("catalyst_score"), 0.9),
            (data.get("risk_adjustment"), 0.6),
            (data.get("flow_strength"), 0.8),
        )
    )
    value = clamp(score if score is not None else 0.0)
    return {"score": round(value, 2), "signal_label": "strong" if value >= 70.0 else "moderate" if value >= 40.0 else "weak"}


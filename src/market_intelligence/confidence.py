from __future__ import annotations

from typing import Any, Mapping

from ._shared import clamp, weighted_average


def build_confidence_profile(payload: Mapping[str, Any] | None = None, /, **overrides: Any) -> dict[str, Any]:
    data = dict(payload or {})
    data.update(overrides)
    confidence = weighted_average(
        (
            (data.get("signal_strength"), 1.15),
            (data.get("data_quality"), 1.0),
            (data.get("timing_quality"), 0.85),
            (data.get("liquidity_quality"), 0.75),
            (data.get("regime_alignment"), 0.6),
        )
    )
    value = clamp(confidence if confidence is not None else data.get("confidence", 0.0))
    return {
        "confidence": round(value, 2),
        "confidence_label": "high" if value >= 70.0 else "medium" if value >= 40.0 else "low",
        "confidence_components": {key: data.get(key) for key in ("signal_strength", "data_quality", "timing_quality", "liquidity_quality", "regime_alignment")},
    }


def score_confidence(*values: Any) -> float:
    profile = build_confidence_profile({"signal_strength": values[0] if values else None})
    return float(profile["confidence"])

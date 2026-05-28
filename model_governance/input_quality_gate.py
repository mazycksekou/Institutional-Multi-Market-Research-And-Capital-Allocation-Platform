from __future__ import annotations

from typing import Any


def evaluate_input_quality(
    *,
    required_inputs: list[str],
    provided_inputs: dict[str, Any],
    numeric_inputs: list[str] | None = None,
    max_input_age_seconds: int = 300,
    input_age_seconds: int = 0,
    source_reliability: float = 100,
    timestamp_quality: float = 100,
    market_identity_confidence: float = 100,
    settlement_rule_confidence: float = 100,
    provider_consensus: float = 100,
) -> dict[str, Any]:
    missing_inputs = [field for field in required_inputs if provided_inputs.get(field) is None]
    malformed_inputs: list[str] = []
    for field in numeric_inputs or []:
        value = provided_inputs.get(field)
        if value is None:
            continue
        try:
            float(value)
        except (TypeError, ValueError):
            malformed_inputs.append(field)
    stale_inputs = list(required_inputs) if input_age_seconds > max_input_age_seconds else []
    score_components = [
        max(0.0, 100.0 - len(missing_inputs) * 25.0),
        max(0.0, 100.0 - len(malformed_inputs) * 35.0),
        max(0.0, 100.0 - (20.0 if stale_inputs else 0.0)),
        float(source_reliability),
        float(timestamp_quality),
        float(market_identity_confidence),
        float(settlement_rule_confidence),
        float(provider_consensus),
    ]
    input_quality_score = round(sum(score_components) / len(score_components), 2)
    blocked = bool(missing_inputs or malformed_inputs or stale_inputs)
    return {
        "missing_inputs": missing_inputs,
        "malformed_inputs": malformed_inputs,
        "stale_inputs": stale_inputs,
        "source_reliability": float(source_reliability),
        "timestamp_quality": float(timestamp_quality),
        "market_identity_confidence": float(market_identity_confidence),
        "settlement_rule_confidence": float(settlement_rule_confidence),
        "provider_consensus": float(provider_consensus),
        "input_quality_score": input_quality_score,
        "blocked": blocked,
        "can_affect_full_kelly": not blocked,
        "can_affect_active_scoring": not blocked,
    }


"""Canonical probability blending helpers.

This module owns deterministic probability blending and calibration-safe
helpers. It does not import providers, connectors, or live services.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Any, Optional

from src.core.pricing import clamp_probability, probability_to_edge as _pricing_probability_to_edge


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        if isinstance(value, bool):
            return float(value)
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_probability(value: Any) -> float:
    probability = clamp_probability(value)
    if probability <= 0.0 or probability >= 1.0:
        raise ValueError("Probability must be between 0 and 1.")
    return probability


def implied_probability_from_american(odds: int | float) -> float:
    from src.core.math_utils import implied_probability_from_american as _core

    return _core(odds)


def implied_probability_from_decimal(decimal_odds: int | float) -> float:
    from src.core.math_utils import decimal_to_implied_probability as _core

    return _core(decimal_odds)


@dataclass(slots=True)
class IndependentInputs:
    """Container for independent model inputs and adjustments."""

    projection_probability: Optional[float] = None
    pitcher_adjustment: Optional[float] = None
    weather_adjustment: Optional[float] = None
    lineup_adjustment: Optional[float] = None
    bullpen_adjustment: Optional[float] = None
    injury_adjustment: Optional[float] = None
    park_factor_adjustment: Optional[float] = None
    umpire_adjustment: Optional[float] = None
    player_prop_projection: Optional[float] = None
    sharp_market_probability: Optional[float] = None
    closing_line_projection: Optional[float] = None

    def get_active_inputs(self) -> list[str]:
        active = []
        for attr_name in (
            "projection_probability",
            "pitcher_adjustment",
            "weather_adjustment",
            "lineup_adjustment",
            "bullpen_adjustment",
            "injury_adjustment",
            "park_factor_adjustment",
            "umpire_adjustment",
            "player_prop_projection",
            "sharp_market_probability",
            "closing_line_projection",
        ):
            if getattr(self, attr_name) is not None:
                active.append(attr_name)
        return active

    def get_missing_inputs(self) -> list[str]:
        all_inputs = (
            "projection_probability",
            "pitcher_adjustment",
            "weather_adjustment",
            "lineup_adjustment",
            "bullpen_adjustment",
            "injury_adjustment",
            "park_factor_adjustment",
            "umpire_adjustment",
            "player_prop_projection",
            "sharp_market_probability",
            "closing_line_projection",
        )
        return [inp for inp in all_inputs if getattr(self, inp) is None]

    def get_adjustment_values(self) -> list[float]:
        adjustments = []
        for attr_name in (
            "pitcher_adjustment",
            "weather_adjustment",
            "lineup_adjustment",
            "bullpen_adjustment",
            "injury_adjustment",
            "park_factor_adjustment",
            "umpire_adjustment",
            "player_prop_projection",
            "closing_line_projection",
        ):
            value = getattr(self, attr_name)
            if value is not None:
                adjustments.append(float(value))
        return adjustments


@dataclass(slots=True)
class ModelProbabilityResult:
    final_probability: float
    probability_type: str
    active_inputs: list[str]
    missing_inputs: list[str]
    model_limitations: list[str]
    data_quality_score: float
    confidence: float
    confidence_grade: str
    provider_status: dict[str, str]
    market_probability: Optional[float] = None
    applied_adjustments: dict[str, float] = field(default_factory=dict)
    adjustment_cap_warnings: list[str] = field(default_factory=list)


SINGLE_ADJUSTMENT_MAX_IMPACT = 0.03
TOTAL_ADJUSTMENT_MAX_IMPACT = 0.08
FINAL_PROBABILITY_FLOOR = 0.01
FINAL_PROBABILITY_CEILING = 0.99


def calculate_data_quality_score(inputs: IndependentInputs) -> float:
    total_possible = 11
    active_count = len(inputs.get_active_inputs())
    completeness_score = (active_count / total_possible) * 0.7
    projection_bonus = 0.15 if inputs.projection_probability is not None else 0.0
    sharp_bonus = 0.1 if inputs.sharp_market_probability is not None else 0.0
    adjustment_count = len(inputs.get_adjustment_values())
    adjustment_bonus = min(0.05, adjustment_count * 0.01)
    return min(1.0, completeness_score + projection_bonus + sharp_bonus + adjustment_bonus)


def calculate_confidence_score(data_quality: float, probability_volatility: float = 0.0) -> float:
    base_confidence = clamp_probability(data_quality)
    volatility_penalty = min(0.1, max(0.0, float(probability_volatility)) * 0.5)
    return max(0.0, base_confidence - volatility_penalty)


def get_confidence_grade(confidence: float) -> str:
    if confidence >= 0.9:
        return "A"
    if confidence >= 0.8:
        return "B"
    if confidence >= 0.7:
        return "C"
    if confidence >= 0.6:
        return "D"
    return "F"


def apply_adjustment_caps(base_probability: float, adjustments: list[float]) -> tuple[float, list[str]]:
    warnings: list[str] = []
    capped_adjustments: list[float] = []

    for adj in adjustments:
        if abs(adj) > SINGLE_ADJUSTMENT_MAX_IMPACT:
            warnings.append(
                f"Single adjustment {adj:.3f} exceeds {SINGLE_ADJUSTMENT_MAX_IMPACT:.3f} cap"
            )
            capped_adj = max(-SINGLE_ADJUSTMENT_MAX_IMPACT, min(SINGLE_ADJUSTMENT_MAX_IMPACT, adj))
        else:
            capped_adj = adj
        capped_adjustments.append(capped_adj)

    total_adjustment = sum(capped_adjustments)
    if abs(total_adjustment) > TOTAL_ADJUSTMENT_MAX_IMPACT:
        warnings.append(
            f"Total adjustment {total_adjustment:.3f} exceeds {TOTAL_ADJUSTMENT_MAX_IMPACT:.3f} cap"
        )
        total_adjustment = max(-TOTAL_ADJUSTMENT_MAX_IMPACT, min(TOTAL_ADJUSTMENT_MAX_IMPACT, total_adjustment))

    adjusted_probability = clamp_probability(base_probability + total_adjustment)
    if adjusted_probability < FINAL_PROBABILITY_FLOOR:
        adjusted_probability = FINAL_PROBABILITY_FLOOR
        warnings.append(f"Probability floored to {FINAL_PROBABILITY_FLOOR:.2f}")
    elif adjusted_probability >= FINAL_PROBABILITY_CEILING:
        adjusted_probability = FINAL_PROBABILITY_CEILING
        warnings.append(f"Probability ceilinged to {FINAL_PROBABILITY_CEILING:.2f}")

    return adjusted_probability, warnings


def blend_probabilities(market_probability: float, inputs: IndependentInputs) -> ModelProbabilityResult:
    active_inputs = inputs.get_active_inputs()
    missing_inputs = inputs.get_missing_inputs()

    if not active_inputs:
        probability_type = "market_derived"
        final_probability = clamp_probability(market_probability)
        model_limitations = ["No independent model inputs available"]
        applied_adjustments: dict[str, float] = {}
        adjustment_warnings: list[str] = []
    elif inputs.projection_probability is not None:
        probability_type = "blended_market_and_projection"
        data_quality = calculate_data_quality_score(inputs)
        market_weight = 0.3 + (1.0 - data_quality) * 0.4
        projection_weight = 1.0 - market_weight
        base_probability = (
            clamp_probability(market_probability) * market_weight
            + clamp_probability(inputs.projection_probability) * projection_weight
        )
        adjustments = inputs.get_adjustment_values()
        final_probability, adjustment_warnings = apply_adjustment_caps(base_probability, adjustments)
        applied_adjustments = {
            name: float(value)
            for name, value in (
                ("pitcher_adjustment", inputs.pitcher_adjustment),
                ("weather_adjustment", inputs.weather_adjustment),
                ("lineup_adjustment", inputs.lineup_adjustment),
                ("bullpen_adjustment", inputs.bullpen_adjustment),
                ("injury_adjustment", inputs.injury_adjustment),
                ("park_factor_adjustment", inputs.park_factor_adjustment),
                ("umpire_adjustment", inputs.umpire_adjustment),
                ("player_prop_projection", inputs.player_prop_projection),
                ("closing_line_projection", inputs.closing_line_projection),
            )
            if value is not None
        }
        model_limitations = []
    else:
        probability_type = "blended_market_projection_and_adjustments"
        base_probability = clamp_probability(market_probability)
        adjustments = inputs.get_adjustment_values()
        final_probability, adjustment_warnings = apply_adjustment_caps(base_probability, adjustments)
        applied_adjustments = {
            name: float(value)
            for name, value in (
                ("pitcher_adjustment", inputs.pitcher_adjustment),
                ("weather_adjustment", inputs.weather_adjustment),
                ("lineup_adjustment", inputs.lineup_adjustment),
                ("bullpen_adjustment", inputs.bullpen_adjustment),
                ("injury_adjustment", inputs.injury_adjustment),
                ("park_factor_adjustment", inputs.park_factor_adjustment),
                ("umpire_adjustment", inputs.umpire_adjustment),
                ("player_prop_projection", inputs.player_prop_projection),
                ("closing_line_projection", inputs.closing_line_projection),
            )
            if value is not None
        }
        model_limitations = ["No projection probability available - using market base with adjustments"]

    data_quality = calculate_data_quality_score(inputs)
    adjustment_values = inputs.get_adjustment_values()
    probability_volatility = statistics.stdev(adjustment_values) if len(adjustment_values) > 1 else 0.0
    confidence = calculate_confidence_score(data_quality, probability_volatility)
    confidence_grade = get_confidence_grade(confidence)
    provider_status = {
        "weather_provider_status": "placeholder",
        "lineup_provider_status": "placeholder",
        "pitcher_provider_status": "placeholder",
        "injury_provider_status": "placeholder",
        "player_projection_provider_status": "placeholder",
        "clv_provider_status": "placeholder",
    }

    if all(value == "placeholder" for value in provider_status.values()):
        model_limitations.append(
            "All advanced providers are placeholder - probability is market derived only and should not be treated as a fully independent projection"
        )

    return ModelProbabilityResult(
        final_probability=final_probability,
        probability_type=probability_type,
        active_inputs=active_inputs,
        missing_inputs=missing_inputs,
        model_limitations=model_limitations,
        data_quality_score=data_quality,
        confidence=confidence,
        confidence_grade=confidence_grade,
        provider_status=provider_status,
        market_probability=clamp_probability(market_probability),
        applied_adjustments=applied_adjustments,
        adjustment_cap_warnings=adjustment_warnings,
    )


def create_probability_response(market_probability: float, inputs: IndependentInputs) -> dict[str, Any]:
    result = blend_probabilities(market_probability, inputs)
    return {
        "ok": True,
        "final_probability": round(result.final_probability, 6),
        "probability_type": result.probability_type,
        "market_probability": round(result.market_probability, 6) if result.market_probability is not None else None,
        "active_inputs": result.active_inputs,
        "missing_inputs": result.missing_inputs,
        "applied_adjustments": {k: round(v, 6) for k, v in result.applied_adjustments.items()},
        "adjustment_cap_warnings": result.adjustment_cap_warnings,
        "model_limitations": result.model_limitations,
        "data_quality_score": round(result.data_quality_score, 3),
        "confidence": round(result.confidence, 3),
        "confidence_grade": result.confidence_grade,
        "provider_status": result.provider_status,
    }


def blend_probability_series(probabilities: list[float], *, fallback: float = 0.5) -> float:
    if not probabilities:
        return clamp_probability(fallback)
    cleaned = [clamp_probability(probability) for probability in probabilities]
    return clamp_probability(sum(cleaned) / len(cleaned))


def probability_to_edge(true_probability: Any, implied_probability: Any) -> float:
    return _pricing_probability_to_edge(true_probability, implied_probability)


__all__ = [
    "IndependentInputs",
    "ModelProbabilityResult",
    "SINGLE_ADJUSTMENT_MAX_IMPACT",
    "TOTAL_ADJUSTMENT_MAX_IMPACT",
    "FINAL_PROBABILITY_FLOOR",
    "FINAL_PROBABILITY_CEILING",
    "apply_adjustment_caps",
    "blend_probabilities",
    "blend_probability_series",
    "calculate_confidence_score",
    "calculate_data_quality_score",
    "clamp_probability",
    "create_probability_response",
    "get_confidence_grade",
    "implied_probability_from_american",
    "implied_probability_from_decimal",
    "normalize_probability",
    "probability_to_edge",
]

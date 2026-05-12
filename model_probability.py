"""Model probability blending and adjustment layer with future-ready inputs."""
from __future__ import annotations

from typing import Any, Optional
import statistics


class IndependentInputs:
    """Container for independent model inputs and adjustments."""
    
    def __init__(
        self,
        projection_probability: Optional[float] = None,
        pitcher_adjustment: Optional[float] = None,
        weather_adjustment: Optional[float] = None,
        lineup_adjustment: Optional[float] = None,
        bullpen_adjustment: Optional[float] = None,
        injury_adjustment: Optional[float] = None,
        park_factor_adjustment: Optional[float] = None,
        umpire_adjustment: Optional[float] = None,
        player_prop_projection: Optional[float] = None,
        sharp_market_probability: Optional[float] = None,
        closing_line_projection: Optional[float] = None,
    ):
        self.projection_probability = projection_probability
        self.pitcher_adjustment = pitcher_adjustment
        self.weather_adjustment = weather_adjustment
        self.lineup_adjustment = lineup_adjustment
        self.bullpen_adjustment = bullpen_adjustment
        self.injury_adjustment = injury_adjustment
        self.park_factor_adjustment = park_factor_adjustment
        self.umpire_adjustment = umpire_adjustment
        self.player_prop_projection = player_prop_projection
        self.sharp_market_probability = sharp_market_probability
        self.closing_line_projection = closing_line_projection
    
    def get_active_inputs(self) -> list[str]:
        """Return list of input types that have values."""
        active = []
        for attr_name in [
            "projection_probability", "pitcher_adjustment", "weather_adjustment",
            "lineup_adjustment", "bullpen_adjustment", "injury_adjustment",
            "park_factor_adjustment", "umpire_adjustment", "player_prop_projection",
            "sharp_market_probability", "closing_line_projection"
        ]:
            value = getattr(self, attr_name)
            if value is not None:
                active.append(attr_name)
        return active
    
    def get_missing_inputs(self) -> list[str]:
        """Return list of input types that are missing."""
        all_inputs = [
            "projection_probability", "pitcher_adjustment", "weather_adjustment",
            "lineup_adjustment", "bullpen_adjustment", "injury_adjustment",
            "park_factor_adjustment", "umpire_adjustment", "player_prop_projection",
            "sharp_market_probability", "closing_line_projection"
        ]
        return [inp for inp in all_inputs if getattr(self, inp) is None]
    
    def get_adjustment_values(self) -> list[float]:
        """Get all adjustment values (excluding projection and sharp market)."""
        adjustments = []
        for attr_name in [
            "pitcher_adjustment", "weather_adjustment", "lineup_adjustment",
            "bullpen_adjustment", "injury_adjustment", "park_factor_adjustment",
            "umpire_adjustment", "player_prop_projection", "closing_line_projection"
        ]:
            value = getattr(self, attr_name)
            if value is not None:
                adjustments.append(value)
        return adjustments


class ModelProbabilityResult:
    """Result of model probability calculation with transparency."""
    
    def __init__(
        self,
        final_probability: float,
        probability_type: str,
        active_inputs: list[str],
        missing_inputs: list[str],
        model_limitations: list[str],
        data_quality_score: float,
        confidence: float,
        confidence_grade: str,
        provider_status: dict[str, str],
        market_probability: Optional[float] = None,
        applied_adjustments: Optional[dict[str, float]] = None,
        adjustment_cap_warnings: Optional[list[str]] = None,
    ):
        self.final_probability = final_probability
        self.probability_type = probability_type
        self.active_inputs = active_inputs
        self.missing_inputs = missing_inputs
        self.model_limitations = model_limitations
        self.data_quality_score = data_quality_score
        self.confidence = confidence
        self.confidence_grade = confidence_grade
        self.provider_status = provider_status
        self.market_probability = market_probability
        self.applied_adjustments = applied_adjustments or {}
        self.adjustment_cap_warnings = adjustment_cap_warnings or []


# Adjustment caps
SINGLE_ADJUSTMENT_MAX_IMPACT = 0.03  # 3 percentage points
TOTAL_ADJUSTMENT_MAX_IMPACT = 0.08   # 8 percentage points
FINAL_PROBABILITY_FLOOR = 0.01
FINAL_PROBABILITY_CEILING = 0.99


def calculate_data_quality_score(inputs: IndependentInputs) -> float:
    """Calculate data quality score based on available inputs."""
    total_possible = 11  # Total number of possible inputs
    active_count = len(inputs.get_active_inputs())
    
    # Base score from completeness (0.7 weight)
    completeness_score = (active_count / total_possible) * 0.7
    
    # Bonus for having projection probability (0.15 weight)
    has_projection = inputs.projection_probability is not None
    projection_bonus = 0.15 if has_projection else 0.0
    
    # Bonus for having sharp market probability (0.1 weight)
    has_sharp = inputs.sharp_market_probability is not None
    sharp_bonus = 0.1 if has_sharp else 0.0
    
    # Bonus for having multiple adjustments (0.05 weight)
    adjustment_count = len(inputs.get_adjustment_values())
    adjustment_bonus = min(0.05, adjustment_count * 0.01)
    
    raw_score = completeness_score + projection_bonus + sharp_bonus + adjustment_bonus
    return min(1.0, raw_score)


def calculate_confidence_score(data_quality: float, probability_volatility: float = 0.0) -> float:
    """Calculate confidence score based on data quality and probability volatility."""
    # Base confidence is primarily data quality
    base_confidence = data_quality
    
    # Small reduction for volatility
    volatility_penalty = min(0.1, probability_volatility * 0.5)
    
    return max(0.0, base_confidence - volatility_penalty)


def get_confidence_grade(confidence: float) -> str:
    """Convert confidence score to letter grade."""
    if confidence >= 0.9:
        return "A"
    elif confidence >= 0.8:
        return "B"
    elif confidence >= 0.7:
        return "C"
    elif confidence >= 0.6:
        return "D"
    else:
        return "F"


def apply_adjustment_caps(
    base_probability: float, 
    adjustments: list[float]
) -> tuple[float, list[str]]:
    """Apply adjustment caps and return final probability and warnings."""
    warnings = []
    
    # Cap individual adjustments first
    capped_adjustments = []
    for adj in adjustments:
        if abs(adj) > SINGLE_ADJUSTMENT_MAX_IMPACT:
            warnings.append(f"Single adjustment {adj:.3f} exceeds {SINGLE_ADJUSTMENT_MAX_IMPACT:.3f} cap")
            capped_adj = max(-SINGLE_ADJUSTMENT_MAX_IMPACT, min(SINGLE_ADJUSTMENT_MAX_IMPACT, adj))
        else:
            capped_adj = adj
        capped_adjustments.append(capped_adj)
    
    # Calculate total adjustment from capped values
    total_adjustment = sum(capped_adjustments)
    
    # Check total adjustment cap
    if abs(total_adjustment) > TOTAL_ADJUSTMENT_MAX_IMPACT:
        warnings.append(f"Total adjustment {total_adjustment:.3f} exceeds {TOTAL_ADJUSTMENT_MAX_IMPACT:.3f} cap")
        total_adjustment = max(-TOTAL_ADJUSTMENT_MAX_IMPACT, min(TOTAL_ADJUSTMENT_MAX_IMPACT, total_adjustment))
    
    # Apply adjustment
    adjusted_probability = base_probability + total_adjustment
    
    # Apply floor and ceiling
    if adjusted_probability < FINAL_PROBABILITY_FLOOR:
        adjusted_probability = FINAL_PROBABILITY_FLOOR
        warnings.append(f"Probability floored to {FINAL_PROBABILITY_FLOOR:.2f}")
    elif adjusted_probability >= FINAL_PROBABILITY_CEILING:
        adjusted_probability = FINAL_PROBABILITY_CEILING
        warnings.append(f"Probability ceilinged to {FINAL_PROBABILITY_CEILING:.2f}")
    
    return adjusted_probability, warnings


def blend_probabilities(
    market_probability: float,
    inputs: IndependentInputs
) -> ModelProbabilityResult:
    """Blend market probability with independent inputs and adjustments."""
    
    active_inputs = inputs.get_active_inputs()
    missing_inputs = inputs.get_missing_inputs()
    
    # Determine probability type
    if not active_inputs:
        # Only market probability available
        probability_type = "market_derived"
        final_probability = market_probability
        model_limitations = ["No independent model inputs available"]
        applied_adjustments = {}
        adjustment_warnings = []
        
    elif inputs.projection_probability is not None:
        # Have projection probability
        probability_type = "blended_market_and_projection"
        
        # Calculate weights based on data quality
        data_quality = calculate_data_quality_score(inputs)
        market_weight = 0.3 + (1.0 - data_quality) * 0.4  # Market gets more weight if data quality is low
        projection_weight = 1.0 - market_weight
        
        # Blend market and projection
        base_probability = (market_probability * market_weight + inputs.projection_probability * projection_weight)
        
        # Apply adjustments
        adjustments = inputs.get_adjustment_values()
        final_probability, adjustment_warnings = apply_adjustment_caps(base_probability, adjustments)
        
        # Track applied adjustments
        applied_adjustments = {}
        if inputs.pitcher_adjustment is not None:
            applied_adjustments["pitcher_adjustment"] = inputs.pitcher_adjustment
        if inputs.weather_adjustment is not None:
            applied_adjustments["weather_adjustment"] = inputs.weather_adjustment
        if inputs.lineup_adjustment is not None:
            applied_adjustments["lineup_adjustment"] = inputs.lineup_adjustment
        if inputs.bullpen_adjustment is not None:
            applied_adjustments["bullpen_adjustment"] = inputs.bullpen_adjustment
        if inputs.injury_adjustment is not None:
            applied_adjustments["injury_adjustment"] = inputs.injury_adjustment
        if inputs.park_factor_adjustment is not None:
            applied_adjustments["park_factor_adjustment"] = inputs.park_factor_adjustment
        if inputs.umpire_adjustment is not None:
            applied_adjustments["umpire_adjustment"] = inputs.umpire_adjustment
        if inputs.player_prop_projection is not None:
            applied_adjustments["player_prop_projection"] = inputs.player_prop_projection
        if inputs.closing_line_projection is not None:
            applied_adjustments["closing_line_projection"] = inputs.closing_line_projection
        
        model_limitations = []
        
    else:
        # Have adjustments but no projection
        probability_type = "blended_market_projection_and_adjustments"
        
        # Start with market probability and apply adjustments
        base_probability = market_probability
        adjustments = inputs.get_adjustment_values()
        final_probability, adjustment_warnings = apply_adjustment_caps(base_probability, adjustments)
        
        # Track applied adjustments
        applied_adjustments = {}
        if inputs.pitcher_adjustment is not None:
            applied_adjustments["pitcher_adjustment"] = inputs.pitcher_adjustment
        if inputs.weather_adjustment is not None:
            applied_adjustments["weather_adjustment"] = inputs.weather_adjustment
        if inputs.lineup_adjustment is not None:
            applied_adjustments["lineup_adjustment"] = inputs.lineup_adjustment
        if inputs.bullpen_adjustment is not None:
            applied_adjustments["bullpen_adjustment"] = inputs.bullpen_adjustment
        if inputs.injury_adjustment is not None:
            applied_adjustments["injury_adjustment"] = inputs.injury_adjustment
        if inputs.park_factor_adjustment is not None:
            applied_adjustments["park_factor_adjustment"] = inputs.park_factor_adjustment
        if inputs.umpire_adjustment is not None:
            applied_adjustments["umpire_adjustment"] = inputs.umpire_adjustment
        if inputs.player_prop_projection is not None:
            applied_adjustments["player_prop_projection"] = inputs.player_prop_projection
        if inputs.closing_line_projection is not None:
            applied_adjustments["closing_line_projection"] = inputs.closing_line_projection
        
        model_limitations = ["No projection probability available - using market base with adjustments"]
    
    # Calculate data quality and confidence
    data_quality = calculate_data_quality_score(inputs)
    
    # Calculate probability volatility for confidence
    adjustment_values = inputs.get_adjustment_values()
    probability_volatility = statistics.stdev(adjustment_values) if len(adjustment_values) > 1 else 0.0
    confidence = calculate_confidence_score(data_quality, probability_volatility)
    confidence_grade = get_confidence_grade(confidence)
    
    # Provider status placeholders
    provider_status = {
        "weather_provider_status": "placeholder",
        "lineup_provider_status": "placeholder", 
        "pitcher_provider_status": "placeholder",
        "injury_provider_status": "placeholder",
        "player_projection_provider_status": "placeholder",
        "clv_provider_status": "placeholder"
    }
    
    # Add limitation if all advanced providers are missing
    advanced_providers = [
        "weather_provider_status", "lineup_provider_status", "pitcher_provider_status",
        "injury_provider_status", "player_projection_provider_status", "clv_provider_status"
    ]
    
    if all(provider_status[provider] == "placeholder" for provider in advanced_providers):
        model_limitations.append("All advanced providers are placeholder - probability is market derived only and should not be treated as a fully independent projection")
    
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
        market_probability=market_probability,
        applied_adjustments=applied_adjustments,
        adjustment_cap_warnings=adjustment_warnings
    )


def create_probability_response(
    market_probability: float,
    inputs: IndependentInputs
) -> dict[str, Any]:
    """Create response dictionary for model probability calculation."""
    
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
        "provider_status": result.provider_status
    }

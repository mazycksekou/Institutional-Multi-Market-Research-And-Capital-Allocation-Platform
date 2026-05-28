from __future__ import annotations


def evaluate_kelly_gate(
    *,
    raw_full_kelly_fraction: float,
    model_confidence_for_full_kelly: float,
    data_quality_for_full_kelly: float,
    liquidity_for_full_kelly: float,
    drawdown_gate_result: bool,
    exposure_gate_result: bool,
) -> dict[str, float | str | bool]:
    minimum_quality = min(
        float(model_confidence_for_full_kelly),
        float(data_quality_for_full_kelly),
        float(liquidity_for_full_kelly),
    )
    if minimum_quality >= 85 and drawdown_gate_result and exposure_gate_result:
        recommended_mode = "full_kelly"
        operating_fraction = float(raw_full_kelly_fraction)
        gate_result = "full_kelly_allowed"
    elif minimum_quality >= 70 and drawdown_gate_result and exposure_gate_result:
        recommended_mode = "half_kelly" if minimum_quality >= 78 else "quarter_kelly"
        divisor = 2.0 if recommended_mode == "half_kelly" else 4.0
        operating_fraction = float(raw_full_kelly_fraction) / divisor
        gate_result = "fractional_kelly_only"
    else:
        recommended_mode = "no_stake"
        operating_fraction = 0.0
        gate_result = "blocked"
    return {
        "raw_full_kelly_fraction": float(raw_full_kelly_fraction),
        "operating_full_kelly_fraction": round(operating_fraction, 6),
        "fractional_fallback_fraction": round(float(raw_full_kelly_fraction) / 4.0, 6),
        "recommended_kelly_mode": recommended_mode,
        "model_confidence_for_full_kelly": float(model_confidence_for_full_kelly),
        "data_quality_for_full_kelly": float(data_quality_for_full_kelly),
        "liquidity_for_full_kelly": float(liquidity_for_full_kelly),
        "drawdown_gate_result": bool(drawdown_gate_result),
        "exposure_gate_result": bool(exposure_gate_result),
        "kelly_gate_result": gate_result,
        "full_kelly_auto_execution_allowed": False,
    }


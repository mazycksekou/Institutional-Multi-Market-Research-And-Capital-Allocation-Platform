from __future__ import annotations

def evaluate_kelly_gate(*, raw_full_kelly_fraction: float, model_confidence_for_full_kelly: float, data_quality_for_full_kelly: float, liquidity_for_full_kelly: float, drawdown_gate_result: bool, exposure_gate_result: bool, market_identity_for_full_kelly: float = 100.0):
    minq = min(model_confidence_for_full_kelly, data_quality_for_full_kelly, liquidity_for_full_kelly, market_identity_for_full_kelly)
    if minq >= 85 and drawdown_gate_result and exposure_gate_result:
        mode = "full_kelly"; op = raw_full_kelly_fraction; result = "full_kelly_allowed"
    elif minq >= 70 and drawdown_gate_result and exposure_gate_result:
        mode = "half_kelly" if minq >= 78 else "quarter_kelly"; op = raw_full_kelly_fraction / (2 if mode == "half_kelly" else 4); result = "fractional_kelly_only"
    else:
        mode = "no_stake"; op = 0.0; result = "blocked"
    return {"raw_full_kelly_fraction": raw_full_kelly_fraction, "operating_full_kelly_fraction": round(op,6), "fractional_fallback_fraction": round(raw_full_kelly_fraction/4,6), "recommended_kelly_mode": mode, "model_confidence_for_full_kelly": model_confidence_for_full_kelly, "data_quality_for_full_kelly": data_quality_for_full_kelly, "liquidity_for_full_kelly": liquidity_for_full_kelly, "market_identity_for_full_kelly": market_identity_for_full_kelly, "drawdown_gate_result": drawdown_gate_result, "exposure_gate_result": exposure_gate_result, "kelly_gate_result": result, "full_kelly_auto_execution_allowed": False}

from __future__ import annotations

def evaluate_risk_gate(**kwargs):
    risks = [float(kwargs.get(k, 0)) for k in ["drawdown_risk", "tail_risk", "liquidity_risk", "settlement_risk", "correlation_risk", "market_regime_risk", "execution_risk", "risk_of_ruin", "max_loss", "exposure_concentration"]]
    avg = sum(risks) / max(len(risks), 1)
    score = max(0, min(100, 100 - avg * 100))
    hard_block = float(kwargs.get("drawdown_risk", 0)) >= 0.8 or float(kwargs.get("risk_of_ruin", 0)) >= 0.8 or float(kwargs.get("exposure_concentration", 0)) >= 0.8
    return {**kwargs, "risk_score": round(score, 2), "passes_gate": (score >= 70) and (not hard_block)}

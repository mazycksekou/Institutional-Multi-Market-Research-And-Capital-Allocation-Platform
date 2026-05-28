from __future__ import annotations


def evaluate_risk_gate(
    *,
    drawdown_risk: float,
    tail_risk: float,
    liquidity_risk: float,
    settlement_risk: float,
    correlation_risk: float,
    market_regime_risk: float,
    execution_risk: float,
    risk_of_ruin: float,
) -> dict[str, float | bool]:
    average_risk = (
        float(drawdown_risk)
        + float(tail_risk)
        + float(liquidity_risk)
        + float(settlement_risk)
        + float(correlation_risk)
        + float(market_regime_risk)
        + float(execution_risk)
        + float(risk_of_ruin)
    ) / 8.0
    risk_score = round(max(0.0, min(100.0, 100.0 - average_risk * 100.0)), 2)
    return {
        "drawdown_risk": float(drawdown_risk),
        "tail_risk": float(tail_risk),
        "liquidity_risk": float(liquidity_risk),
        "settlement_risk": float(settlement_risk),
        "correlation_risk": float(correlation_risk),
        "market_regime_risk": float(market_regime_risk),
        "execution_risk": float(execution_risk),
        "risk_of_ruin": float(risk_of_ruin),
        "risk_score": risk_score,
        "passes_gate": risk_score >= 70,
    }


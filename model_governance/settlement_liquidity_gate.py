from __future__ import annotations

def evaluate_settlement_liquidity_gate(**kwargs):
    ok = all([kwargs.get("settlement_rule_match", True), kwargs.get("overtime_rule_match", True), kwargs.get("void_rule_match", True), kwargs.get("prediction_market_resolution_match", True), kwargs.get("player_prop_rule_match", True), float(kwargs.get("liquidity_score", 100)) >= 60])
    return {**kwargs, "execution_feasibility_score": float(kwargs.get("execution_feasibility_score", kwargs.get("fill_probability", 0) * 100)), "gate_result": "approved" if ok else "blocked_by_governance"}

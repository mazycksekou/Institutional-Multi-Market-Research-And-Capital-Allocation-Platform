from __future__ import annotations

def evaluate_backtest_gate(**kwargs):
    score = float(kwargs.get("out_of_sample_result", 0))
    score += 100 if not kwargs.get("data_leakage_flag", False) else -100
    score += 10 if kwargs.get("vig", 0) is not None else -10
    score += 10 if kwargs.get("transaction_cost", 0) is not None else -10
    score += 10 if kwargs.get("slippage", 0) is not None else -10
    score += float(kwargs.get("closing_line_value", 0)) * 100
    score -= float(kwargs.get("max_drawdown", 0)) * 100
    score = max(0, min(100, score / 2))
    return {**kwargs, "backtest_score": round(score, 2), "passes_gate": score >= 70}

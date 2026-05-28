from __future__ import annotations


def evaluate_backtest_gate(**kwargs):
    score = float(kwargs.get("out_of_sample_result", 0))
    score += 100 if not kwargs.get("data_leakage_flag", False) else -100
    score += 10 if kwargs.get("vig", 0) is not None else -10
    score += 10 if kwargs.get("transaction_cost", 0) is not None else -10
    score += 10 if kwargs.get("slippage", 0) is not None else -10
    score += float(kwargs.get("closing_line_value", 0)) * 100
    score -= float(kwargs.get("max_drawdown", 0)) * 100
    score += float(kwargs.get("realized_roi_percent", 0))
    score += float(kwargs.get("expected_roi_percent", 0)) * 0.5
    score += float(kwargs.get("positive_clv_rate", 0)) * 20
    if kwargs.get("sample_size", 0) and int(kwargs.get("sample_size", 0)) < 30:
        score -= 20
    if str(kwargs.get("performance_status", "")) in {"needs_more_sample", "blocked_by_performance"}:
        score -= 10
    score = max(0, min(100, score / 2))
    blocked_reasons = list(kwargs.get("blocked_reasons", []))
    if score < 70 and "blocked_by_performance" not in blocked_reasons:
        blocked_reasons.append("blocked_by_performance")
    return {
        **kwargs,
        "backtest_score": round(score, 2),
        "passes_gate": score >= 70,
        "blocked_reasons": blocked_reasons,
    }

from __future__ import annotations


def evaluate_backtest_gate(
    *,
    in_sample_result: float,
    out_of_sample_result: float,
    transaction_costs: float,
    vig: float,
    slippage: float,
    max_drawdown: float,
    profit_factor: float,
    realized_roi: float,
    expected_roi: float,
    data_leakage_flag: bool,
) -> dict[str, float | bool]:
    gross_score = 62.0
    gross_score += min(12.0, max(in_sample_result, 0.0) * 40.0)
    gross_score += min(16.0, max(out_of_sample_result, 0.0) * 50.0)
    gross_score += min(6.0, max(profit_factor - 1.0, 0.0) * 12.0)
    gross_score += min(6.0, max(realized_roi, 0.0) * 100.0)
    gross_score += min(6.0, max(expected_roi, 0.0) * 100.0)
    penalty = (transaction_costs + vig + slippage) * 20.0 + max_drawdown * 18.0
    if data_leakage_flag:
        penalty += 100.0
    backtest_score = round(max(0.0, min(100.0, gross_score - penalty)), 2)
    return {
        "in_sample_result": float(in_sample_result),
        "out_of_sample_result": float(out_of_sample_result),
        "transaction_costs": float(transaction_costs),
        "vig": float(vig),
        "slippage": float(slippage),
        "max_drawdown": float(max_drawdown),
        "profit_factor": float(profit_factor),
        "realized_roi": float(realized_roi),
        "expected_roi": float(expected_roi),
        "data_leakage_flag": bool(data_leakage_flag),
        "backtest_score": backtest_score,
        "passes_gate": backtest_score >= 70 and not data_leakage_flag,
    }

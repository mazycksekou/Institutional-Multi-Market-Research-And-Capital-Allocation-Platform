import unittest

from model_governance.backtest_gate import evaluate_backtest_gate


class TestBacktestGate(unittest.TestCase):
    def test_backtest_gate_includes_realistic_costs(self):
        result = evaluate_backtest_gate(
            in_sample_result=0.15,
            out_of_sample_result=0.11,
            transaction_costs=0.01,
            vig=0.02,
            slippage=0.01,
            max_drawdown=0.08,
            profit_factor=1.4,
            realized_roi=0.05,
            expected_roi=0.04,
            data_leakage_flag=False,
        )
        self.assertTrue(result["passes_gate"])
        self.assertEqual(result["vig"], 0.02)
        self.assertEqual(result["slippage"], 0.01)


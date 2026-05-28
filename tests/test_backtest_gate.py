import unittest
from model_governance.backtest_gate import evaluate_backtest_gate


class TestBacktestGate(unittest.TestCase):
    def test_includes_costs(self):
        r = evaluate_backtest_gate(
            out_of_sample_result=80,
            data_leakage_flag=False,
            vig=0.02,
            transaction_cost=0.01,
            slippage=0.01,
            closing_line_value=0.02,
            max_drawdown=0.1,
            realized_roi_percent=2.5,
            expected_roi_percent=1.2,
            positive_clv_rate=0.6,
            sample_size=50,
            performance_status="backtest_complete",
        )
        self.assertIn("backtest_score", r)
        self.assertIn("blocked_reasons", r)

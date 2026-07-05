import unittest

from src.services.streamlit_dashboard_facade import calculate_performance_metrics


class TestPerformanceMetrics(unittest.TestCase):
    def test_realized_and_expected_roi_profit_factor_drawdown(self):
        entries = [
            {
                "settlement_status": "settled",
                "result_status": "win",
                "paper_stake": 10,
                "paper_profit_loss": 10,
                "ev_percent": 6.0,
                "recommended_stake_percent": 1.5,
            },
            {
                "settlement_status": "settled",
                "result_status": "loss",
                "paper_stake": 10,
                "paper_profit_loss": -10,
                "ev_percent": 2.0,
                "recommended_stake_percent": 1.0,
            },
        ]
        metrics = calculate_performance_metrics(entries)
        self.assertEqual(metrics["realized_roi_percent"], 0.0)
        self.assertEqual(metrics["expected_roi_percent"], 4.0)
        self.assertEqual(metrics["profit_factor"], 1.0)
        self.assertGreaterEqual(metrics["max_drawdown_percent"], 0.0)
        self.assertIn("sample_size_warning", metrics)


if __name__ == "__main__":
    unittest.main()


import unittest

from automation_scheduler.backtesting import run_backtesting_scaffold


class TestBacktesting(unittest.TestCase):
    def test_insufficient_without_outcomes(self):
        result = run_backtesting_scaffold([{"provider": "kalshi"}])
        self.assertTrue(result["insufficient_data"])

    def test_computed_with_outcomes(self):
        result = run_backtesting_scaffold([{"provider": "kalshi", "final_outcome": 1}, {"provider": "sharp", "final_outcome": 0}])
        self.assertEqual(result["status"], "metrics_ready")
        self.assertIn("provider", result["group_counts"])

    def test_partial_with_some_outcomes(self):
        result = run_backtesting_scaffold(
            [
                {"provider": "kalshi", "market_type": "prediction_market", "reason_codes": ["watch"], "implied_probability": 0.7, "final_outcome": 1},
                {"provider": "sharp", "market_type": "sports_pregame_main", "reason_codes": ["watch"], "implied_probability": 0.4},
            ]
        )
        self.assertEqual(result["status"], "partial_calibration")
        self.assertEqual(result["settled_count"], 1)

    def test_void_and_missing_probability_do_not_fabricate_metrics(self):
        result = run_backtesting_scaffold(
            [
                {"provider": "kalshi", "implied_probability": 0.7, "outcome_status": "void", "final_outcome": "void"},
                {"provider": "sharp", "final_outcome": "win"},
            ]
        )
        self.assertEqual(result["status"], "partial_calibration")
        self.assertEqual(result["metrics"], {})

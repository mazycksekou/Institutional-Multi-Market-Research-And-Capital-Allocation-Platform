import unittest

from automation_scheduler.backtesting import run_backtesting_scaffold


class TestBacktesting(unittest.TestCase):
    def test_insufficient_without_outcomes(self):
        result = run_backtesting_scaffold([{"provider": "kalshi"}])
        self.assertTrue(result["insufficient_data"])

    def test_computed_with_outcomes(self):
        result = run_backtesting_scaffold([{"provider": "kalshi", "final_outcome": 1}, {"provider": "sharp", "final_outcome": 0}])
        self.assertEqual(result["status"], "computed")

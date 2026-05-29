import unittest

from automation_scheduler.calibration import run_calibration_scaffold


class TestCalibration(unittest.TestCase):
    def test_insufficient_without_labels(self):
        result = run_calibration_scaffold([{"implied_probability": 0.5}])
        self.assertTrue(result["insufficient_data"])

    def test_computed_with_labels(self):
        result = run_calibration_scaffold([{"implied_probability": 0.6, "final_outcome": 1}, {"implied_probability": 0.4, "final_outcome": 0}])
        self.assertEqual(result["status"], "computed")
        self.assertIn("brier_score", result["metrics"])

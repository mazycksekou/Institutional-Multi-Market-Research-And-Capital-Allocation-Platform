import unittest

from automation_scheduler.calibration_tracker import (
    bucket_predictions,
    calculate_brier_score,
    calculate_expected_calibration_error,
    calculate_log_loss,
    detect_overconfidence,
)


class TestCalibrationTracker(unittest.TestCase):
    def test_buckets_brier_logloss_ece_overconfidence(self):
        rows = [
            {"model_probability": 0.52, "result_status": "win"},
            {"model_probability": 0.58, "result_status": "loss"},
            {"model_probability": 0.72, "result_status": "loss"},
            {"model_probability": 0.78, "result_status": "loss"},
        ]
        buckets = bucket_predictions(rows)
        self.assertIn("0.50-0.55", buckets)
        self.assertGreater(calculate_brier_score(rows), 0)
        self.assertGreater(calculate_log_loss(rows), 0)
        self.assertGreaterEqual(calculate_expected_calibration_error(rows), 0)
        self.assertTrue(detect_overconfidence(rows))


if __name__ == "__main__":
    unittest.main()


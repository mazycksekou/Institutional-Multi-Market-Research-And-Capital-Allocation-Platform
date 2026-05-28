import unittest

from model_governance.model_drift_monitor import evaluate_model_drift


class TestModelDriftMonitor(unittest.TestCase):
    def test_model_drift_detected(self):
        result = evaluate_model_drift(
            baseline_metrics={"edge": 0.1, "clv": 0.02},
            current_metrics={"edge": 0.05, "clv": 0.005},
        )
        self.assertTrue(result["drift_detected"])
        self.assertLess(result["drift_score"], 70)


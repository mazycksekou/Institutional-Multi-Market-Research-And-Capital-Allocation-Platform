import unittest
from src.analytics.model_governance.model_drift_monitor import evaluate_model_drift

class TestModelDriftMonitor(unittest.TestCase):
    def test_detect(self):
        r = evaluate_model_drift(baseline_metrics={'input_distribution_shift':0}, current_metrics={'input_distribution_shift':1})
        self.assertTrue(r['drift_detected'])

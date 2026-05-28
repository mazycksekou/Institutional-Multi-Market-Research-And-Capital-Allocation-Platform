import unittest
from model_governance.calibration_gate import evaluate_calibration_gate

class TestCalibrationGate(unittest.TestCase):
    def test_calculates(self):
        r = evaluate_calibration_gate(brier_score=0.2, log_loss=0.3, ignorance_score=0.2, expected_calibration_error=0.05, overconfidence_penalty=0.1, sample_size=100)
        self.assertIn('calibration_score', r)

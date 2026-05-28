import unittest

from model_governance.calibration_gate import evaluate_calibration_gate


class TestCalibrationGate(unittest.TestCase):
    def test_calibration_gate_calculates_safe_score(self):
        result = evaluate_calibration_gate(
            brier_score=0.12,
            log_loss=0.45,
            expected_calibration_error=0.04,
            calibration_bucket_reliability=85,
            overconfidence_penalty=0.03,
            sample_size=1200,
        )
        self.assertGreaterEqual(result["calibration_score"], 70)
        self.assertTrue(result["passes_gate"])


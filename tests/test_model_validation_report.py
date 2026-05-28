import unittest

from model_governance.model_validation_report import build_model_validation_report


class TestModelValidationReport(unittest.TestCase):
    def test_validation_report_blocks_failed_gates(self):
        report = build_model_validation_report(
            model_id="sportsbook_side_total",
            activation_tier="active_scoring_ready",
            input_quality_gate_result={"blocked": False, "passes_gate": True},
            calibration_gate_result={"passes_gate": True},
            backtest_gate_result={"passes_gate": True},
            walk_forward_gate_result={"passes_gate": False},
            risk_gate_result={"passes_gate": True},
            drift_gate_result={"passes_gate": True},
        )
        self.assertEqual(report["validation_status"], "blocked_by_governance")
        self.assertIn("walk_forward_gate_result", report["blocked_gates"])


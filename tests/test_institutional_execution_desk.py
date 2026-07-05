import tempfile
import unittest
from unittest.mock import Mock

from src.services.execution_service import ExecutionDeskRejected, simulate_execution, validate_simulation_request


class TestInstitutionalExecutionDesk(unittest.TestCase):
    def _record(self):
        return {
            "sidecar_id": "candidate-1",
            "source_record_id": "candidate-1",
            "asset_class": "prediction_market",
            "provider": "kalshi_prediction_market",
            "liquidity_score": 90,
            "pricing_quality_score": 95,
            "market_structure_score": 90,
            "confidence_score": 85,
            "settlement_quality_score": 80,
            "risk_score": 15,
            "reason_codes": [],
            "execution_allowed": False,
        }

    def test_simulation_only_is_required(self):
        with self.assertRaises(ExecutionDeskRejected):
            validate_simulation_request({"simulation_only": False})

    def test_live_flags_are_rejected(self):
        for flag in ("live_execution_requested", "submit_live_order", "provider_write", "execution_allowed"):
            with self.subTest(flag=flag):
                with self.assertRaises(ExecutionDeskRejected):
                    validate_simulation_request({"simulation_only": True, flag: True})

    def test_simulation_never_submits_real_action_and_writes_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = simulate_execution(
                {
                    "simulation_only": True,
                    "live_execution_requested": False,
                    "candidate_id": "candidate-1",
                    "asset_class": "prediction_market",
                    "provider": "kalshi_prediction_market",
                    "human_command": "simulate_only",
                    "max_theoretical_risk": 0,
                    "submit_live_order": False,
                },
                records=[self._record()],
                calibration_report={"asset_classes": {"prediction_market": {"matched_outcomes_count": 30}}},
                base_data_dir=tmp,
            )
        self.assertEqual(result["execution_desk_status"], "simulation_only")
        self.assertFalse(result["actual_order_submitted"])
        self.assertFalse(result["actual_bet_submitted"])
        self.assertFalse(result["actual_trade_submitted"])
        self.assertFalse(result["provider_write"])
        self.assertFalse(result["execution_allowed"])
        self.assertTrue(result["simulated_ticket_created"])
        self.assertIn("audit_id", result)

    def test_risk_blocks_are_enforced(self):
        bad = self._record()
        bad["liquidity_score"] = 5
        with tempfile.TemporaryDirectory() as tmp:
            result = simulate_execution(
                {"simulation_only": True, "candidate_id": "candidate-1", "human_command": "simulate_only"},
                records=[bad],
                calibration_report={"asset_classes": {"prediction_market": {"matched_outcomes_count": 0}}},
                base_data_dir=tmp,
            )
        self.assertIn("low_liquidity", result["risk_blocks"])
        self.assertIn("insufficient_calibration_sample", result["risk_blocks"])
        self.assertFalse(result["pre_trade_checks_passed"])

    def test_no_provider_client_write_method_is_called(self):
        provider = Mock()
        provider.submit_order = Mock()
        with tempfile.TemporaryDirectory() as tmp:
            simulate_execution(
                {"simulation_only": True, "candidate_id": "candidate-1", "human_command": "simulate_only"},
                records=[self._record()],
                calibration_report={"asset_classes": {"prediction_market": {"matched_outcomes_count": 30}}},
                base_data_dir=tmp,
            )
        provider.submit_order.assert_not_called()


if __name__ == "__main__":
    unittest.main()

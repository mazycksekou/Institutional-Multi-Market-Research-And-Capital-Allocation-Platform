import unittest

from model_governance.kelly_gate import evaluate_kelly_gate


class TestKellyGate(unittest.TestCase):
    def test_full_kelly_only_when_all_gates_pass(self):
        full = evaluate_kelly_gate(
            raw_full_kelly_fraction=0.08,
            model_confidence_for_full_kelly=90,
            data_quality_for_full_kelly=92,
            liquidity_for_full_kelly=88,
            drawdown_gate_result=True,
            exposure_gate_result=True,
        )
        self.assertEqual(full["recommended_kelly_mode"], "full_kelly")
        self.assertFalse(full["full_kelly_auto_execution_allowed"])

    def test_fractional_and_no_stake_fallbacks(self):
        half = evaluate_kelly_gate(
            raw_full_kelly_fraction=0.08,
            model_confidence_for_full_kelly=75,
            data_quality_for_full_kelly=74,
            liquidity_for_full_kelly=78,
            drawdown_gate_result=True,
            exposure_gate_result=True,
        )
        self.assertIn(half["recommended_kelly_mode"], {"half_kelly", "quarter_kelly"})
        none = evaluate_kelly_gate(
            raw_full_kelly_fraction=0.08,
            model_confidence_for_full_kelly=50,
            data_quality_for_full_kelly=60,
            liquidity_for_full_kelly=55,
            drawdown_gate_result=False,
            exposure_gate_result=True,
        )
        self.assertEqual(none["recommended_kelly_mode"], "no_stake")


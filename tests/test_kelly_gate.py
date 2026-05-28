import unittest
from model_governance.kelly_gate import evaluate_kelly_gate

class TestKellyGate(unittest.TestCase):
    def test_modes(self):
        full = evaluate_kelly_gate(raw_full_kelly_fraction=0.1, model_confidence_for_full_kelly=90, data_quality_for_full_kelly=90, liquidity_for_full_kelly=90, drawdown_gate_result=True, exposure_gate_result=True)
        self.assertEqual(full['recommended_kelly_mode'], 'full_kelly')
        no = evaluate_kelly_gate(raw_full_kelly_fraction=0.1, model_confidence_for_full_kelly=60, data_quality_for_full_kelly=60, liquidity_for_full_kelly=60, drawdown_gate_result=False, exposure_gate_result=True)
        self.assertEqual(no['recommended_kelly_mode'], 'no_stake')

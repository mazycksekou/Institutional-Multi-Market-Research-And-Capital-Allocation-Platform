import unittest
from model_governance.alert_gate import evaluate_alert_gate

class TestAlertGate(unittest.TestCase):
    def test_block_research(self):
        r = evaluate_alert_gate(activation_tier='research_only', opportunity_score=99, risk_gate_passed=True)
        self.assertFalse(r['can_alert'])

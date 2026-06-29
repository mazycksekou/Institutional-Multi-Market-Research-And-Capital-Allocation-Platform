import unittest
from src.analytics.model_governance.human_approval_gate import evaluate_human_approval_gate

class TestHumanApprovalGate(unittest.TestCase):
    def test_blocks_pending(self):
        self.assertFalse(evaluate_human_approval_gate('pending')['allowed'])

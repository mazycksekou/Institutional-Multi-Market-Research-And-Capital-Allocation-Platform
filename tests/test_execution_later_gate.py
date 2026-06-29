import unittest
from src.analytics.model_governance.execution_later_gate import evaluate_execution_later_gate

class TestExecutionLaterGate(unittest.TestCase):
    def test_not_ready(self):
        self.assertEqual(evaluate_execution_later_gate()['result'], 'not_ready')

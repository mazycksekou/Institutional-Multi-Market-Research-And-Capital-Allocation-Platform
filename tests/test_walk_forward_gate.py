import unittest
from model_governance.walk_forward_gate import evaluate_walk_forward_gate

class TestWalkForwardGate(unittest.TestCase):
    def test_decay(self):
        r = evaluate_walk_forward_gate(rolling_window_performance=80, expanding_window_performance=80, regime_split_performance=80, performance_decay=0.5, sample_size=100)
        self.assertLess(r['walk_forward_score'], 70)

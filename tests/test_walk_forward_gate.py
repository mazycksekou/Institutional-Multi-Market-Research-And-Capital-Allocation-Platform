import unittest

from model_governance.walk_forward_gate import evaluate_walk_forward_gate


class TestWalkForwardGate(unittest.TestCase):
    def test_walk_forward_detects_decay(self):
        result = evaluate_walk_forward_gate(
            rolling_window_performance=0.8,
            expanding_window_performance=0.82,
            regime_split_performance=0.78,
            performance_decay=0.3,
            sample_size=800,
        )
        self.assertTrue(result["performance_decay_detected"])


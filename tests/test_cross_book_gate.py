import unittest
from model_governance.cross_book_gate import evaluate_cross_book_gate

class TestCrossBookGate(unittest.TestCase):
    def test_blocks_low_identity(self):
        r = evaluate_cross_book_gate(market_identity_confidence=50)
        self.assertIn('low_market_identity', r['blocked_reasons'])

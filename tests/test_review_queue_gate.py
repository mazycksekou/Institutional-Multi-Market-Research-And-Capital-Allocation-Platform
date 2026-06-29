import unittest
from src.analytics.model_governance.review_queue_gate import evaluate_review_queue_gate

class TestReviewQueueGate(unittest.TestCase):
    def test_blocks_low_tier(self):
        r = evaluate_review_queue_gate(activation_tier='paper_trade_ready', evidence_score=90, input_quality_score=90, model_risk_rating='low', stale_data=False, settlement_mismatch=False)
        self.assertFalse(r['can_enter_review_queue'])

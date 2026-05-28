import unittest

from model_governance.review_queue_gate import evaluate_review_queue_gate


class TestReviewQueueGate(unittest.TestCase):
    def test_review_queue_gate_blocks_below_required_tier(self):
        result = evaluate_review_queue_gate(
            activation_tier="paper_trade_ready",
            evidence_score=90,
            input_quality_score=90,
            model_risk_rating="low",
            stale_data=False,
            settlement_mismatch=False,
        )
        self.assertFalse(result["can_enter_review_queue"])

    def test_review_queue_gate_blocks_stale_or_settlement_mismatch(self):
        stale = evaluate_review_queue_gate(
            activation_tier="review_queue_ready",
            evidence_score=90,
            input_quality_score=90,
            model_risk_rating="moderate",
            stale_data=True,
            settlement_mismatch=False,
        )
        self.assertEqual(stale["review_queue_gate_result"], "blocked_by_governance")
        mismatch = evaluate_review_queue_gate(
            activation_tier="production_candidate",
            evidence_score=90,
            input_quality_score=90,
            model_risk_rating="moderate",
            stale_data=False,
            settlement_mismatch=True,
        )
        self.assertFalse(mismatch["can_affect_opportunity_score"])


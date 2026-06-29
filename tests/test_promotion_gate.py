import unittest
from src.analytics.model_governance.promotion_gate import evaluate_promotion_gate

class TestPromotionGate(unittest.TestCase):
    def test_one_tier(self):
        result = evaluate_promotion_gate(model_card={'model_id':'x'}, inventory_item={'activation_tier':'research_only','evidence_score':80}, target_tier='paper_trade_ready')
        self.assertFalse(result['approved'])

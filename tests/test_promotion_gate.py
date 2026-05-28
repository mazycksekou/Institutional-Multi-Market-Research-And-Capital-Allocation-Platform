import unittest

from model_governance.model_card import build_card_from_inventory_item
from model_governance.model_inventory import get_model_by_id
from model_governance.promotion_gate import evaluate_promotion_gate


class TestPromotionGate(unittest.TestCase):
    def test_promotion_fails_without_evidence_or_documentation(self):
        item = get_model_by_id("institutional_portfolio_construction")
        item["evidence_score"] = 60
        card = build_card_from_inventory_item(item)
        card["assumptions"] = []
        result = evaluate_promotion_gate(model_card=card, inventory_item=item, target_tier="backtest_ready")
        self.assertFalse(result["approved"])
        self.assertIn("model_card_incomplete", result["blocked_reasons"])

    def test_promotion_fails_on_prohibited_claim_language(self):
        item = get_model_by_id("institutional_factor_risk")
        card = build_card_from_inventory_item(item)
        card["mathematical_summary"] = "This is risk-free."
        result = evaluate_promotion_gate(model_card=card, inventory_item=item, target_tier="backtest_ready")
        self.assertFalse(result["approved"])
        self.assertIn("prohibited_claim_language_detected", result["blocked_reasons"])

    def test_promotion_requires_one_tier_at_a_time(self):
        item = get_model_by_id("automation_model_recheck_runner")
        card = build_card_from_inventory_item(item)
        result = evaluate_promotion_gate(model_card=card, inventory_item=item, target_tier="review_queue_ready")
        self.assertFalse(result["approved"])
        self.assertIn("promotion_must_be_one_tier_at_a_time", result["blocked_reasons"])


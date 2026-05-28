import unittest

from model_governance.activation_tiers import can_promote_one_tier, default_activation_tier, tier_allows_active_scoring, tier_allows_review_queue, tier_allows_stake_sizing


class TestActivationTiers(unittest.TestCase):
    def test_default_tier_is_research_only(self):
        self.assertEqual(default_activation_tier(), "research_only")
        self.assertFalse(tier_allows_review_queue("research_only"))
        self.assertFalse(tier_allows_active_scoring("research_only"))

    def test_tier_permissions_and_promotion_step(self):
        self.assertTrue(can_promote_one_tier("research_only", "backtest_ready"))
        self.assertFalse(can_promote_one_tier("research_only", "paper_trade_ready"))
        self.assertTrue(tier_allows_review_queue("review_queue_ready"))
        self.assertTrue(tier_allows_active_scoring("active_scoring_ready"))
        self.assertTrue(tier_allows_stake_sizing("production_candidate"))


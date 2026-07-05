import unittest
from src.analytics.model_governance.activation_tiers import default_activation_tier, can_promote_one_tier, tier_allows_active_scoring

class TestActivationTiers(unittest.TestCase):
    def test_tier_logic(self):
        self.assertEqual(default_activation_tier(), 'research_only')
        self.assertTrue(can_promote_one_tier('research_only', 'backtest_ready'))
        self.assertTrue(tier_allows_active_scoring('active_scoring_ready'))

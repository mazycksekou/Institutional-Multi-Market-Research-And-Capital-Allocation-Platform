import unittest

from src.core.stake_sizing_simulator import simulate_stake_plan


class TestStakeSizingSimulator(unittest.TestCase):
    def test_stake_sizing_respects_bankroll_and_risk_caps(self):
        result = simulate_stake_plan(
            {
                "candidate_type": "arbitrage_candidate",
                "estimated_roi_percent": 2.5,
                "stake_plan": [{"selection": "A", "stake": 50}, {"selection": "B", "stake": 50}],
                "max_gain": 2.5,
                "max_loss": 97.5,
            },
            bankroll=1000,
            risk_profile="low",
            max_loss_cap=8,
        )
        self.assertEqual(result["risk_cap"], 10.0)
        for profile in result["profiles"]:
            self.assertLessEqual(profile["suggested_stake"], 10.0)
            self.assertLessEqual(profile["max_loss"], 8)
            self.assertTrue(profile["review_only"])
        self.assertFalse(result["auto_bet_enabled"])
        self.assertFalse(result["auto_trade_enabled"])

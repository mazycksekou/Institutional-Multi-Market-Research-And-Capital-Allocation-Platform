import unittest

from src.core.risk_of_ruin import evaluate_risk_of_ruin


class RiskOfRuinTests(unittest.TestCase):
    def test_high_ruin_blocks_aggressive(self):
        res = evaluate_risk_of_ruin({"estimated_losing_streak_risk": 90, "bankroll_survival_score": 20})
        self.assertTrue(res["full_kelly_blocked"])

    def test_severe_ruin_no_stake(self):
        res = evaluate_risk_of_ruin({"estimated_losing_streak_risk": 100, "bankroll_survival_score": 0})
        self.assertTrue(res["no_stake_required"])


if __name__ == "__main__":
    unittest.main()

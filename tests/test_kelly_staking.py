import unittest

from src.automation_scheduler_legacy.kelly_staking import calculate_full_kelly_american, calculate_full_kelly_binary, calculate_operating_full_kelly
from src.automation_scheduler_legacy.stake_confidence import evaluate_stake_confidence


class KellyStakingTests(unittest.TestCase):
    def test_full_kelly_binary_formula(self):
        k = calculate_full_kelly_binary(0.55, 2.0)
        self.assertAlmostEqual(k, 0.10, places=6)

    def test_american_formula(self):
        k = calculate_full_kelly_american(0.55, 100)
        self.assertAlmostEqual(k, 0.10, places=6)

    def test_no_edge_returns_zero(self):
        self.assertEqual(calculate_full_kelly_binary(0.49, 2.0), 0.0)

    def test_invalid_probability_returns_zero(self):
        self.assertEqual(calculate_full_kelly_binary(1.2, 2.0), 0.0)

    def test_invalid_odds_returns_zero(self):
        self.assertEqual(calculate_full_kelly_binary(0.55, 1.0), 0.0)

    def test_mode_selection(self):
        high = evaluate_stake_confidence(
            {"model_confidence": 90, "data_quality_score": 90, "market_identity_confidence": 95, "liquidity_score": 9, "stale_data_risk": 10, "settlement_risk": 10, "calibration_score": 85, "CLV_sample_size": 120, "positive_CLV_rate": 60}
        )
        res = calculate_operating_full_kelly(0.1, high, {"full_kelly_allowed": True})
        self.assertEqual(res["recommended_kelly_mode"], "operating_full_kelly")


if __name__ == "__main__":
    unittest.main()

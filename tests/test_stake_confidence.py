import unittest

from src.core.stake_confidence import evaluate_stake_confidence


class StakeConfidenceTests(unittest.TestCase):
    def test_medium_confidence_fallback(self):
        result = evaluate_stake_confidence(
            {"model_confidence": 78, "data_quality_score": 80, "market_identity_confidence": 92, "liquidity_score": 8, "stale_data_risk": 20, "settlement_risk": 20, "calibration_score": 80, "CLV_sample_size": 100, "positive_CLV_rate": 55}
        )
        self.assertEqual(result["confidence_tier"], "medium")

    def test_low_confidence_blocks(self):
        result = evaluate_stake_confidence(
            {"model_confidence": 40, "data_quality_score": 45, "market_identity_confidence": 60, "liquidity_score": 3, "stale_data_risk": 180, "settlement_risk": 80, "calibration_score": 40, "CLV_sample_size": 10, "positive_CLV_rate": 20}
        )
        self.assertEqual(result["confidence_tier"], "low")
        self.assertTrue(result["hard_block"])

    def test_stale_data_blocks_full_kelly(self):
        result = evaluate_stake_confidence(
            {"model_confidence": 95, "data_quality_score": 95, "market_identity_confidence": 95, "liquidity_score": 10, "stale_data_risk": 200, "settlement_risk": 10, "calibration_score": 90, "CLV_sample_size": 200, "positive_CLV_rate": 70}
        )
        self.assertFalse(result["full_kelly_pass"])


if __name__ == "__main__":
    unittest.main()

import unittest

from automation_scheduler.institutional_cross_asset_scores import (
    complete_institutional_scores,
    execution_readiness_tier,
    liquidity_tier,
    quality_tier,
    risk_tier,
)


class TestInstitutionalCrossAssetScores(unittest.TestCase):
    def test_scores_are_bounded_and_execution_remains_disabled(self):
        scored = complete_institutional_scores(
            {
                "asset_class": "prediction_market",
                "provider": "kalshi_prediction_market",
                "market_type": "prediction_market",
                "contract_id": "KXTEST",
                "observed_at": "2026-05-30T12:00:00+00:00",
                "bid": 0.49,
                "ask": 0.51,
                "volume": 1000,
                "open_interest": 1500,
                "implied_probability": 0.5,
                "model_probability": 0.54,
                "reason_codes": [],
            }
        )
        for field in ("quick_quality_score", "broad_quality_score", "liquidity_score", "pricing_quality_score", "risk_score"):
            self.assertGreaterEqual(scored[field], 0)
            self.assertLessEqual(scored[field], 100)
        self.assertTrue(scored["paper_only"])
        self.assertTrue(scored["review_only"])
        self.assertTrue(scored["simulation_only"])
        self.assertFalse(scored["execution_allowed"])

    def test_existing_upstream_scores_are_not_overwritten(self):
        scored = complete_institutional_scores(
            {
                "asset_class": "prediction_market",
                "provider": "kalshi_prediction_market",
                "market_type": "prediction_market",
                "contract_id": "KXTEST",
                "observed_at": "2026-05-30T12:00:00+00:00",
                "bid": 0.49,
                "ask": 0.51,
                "liquidity_score": 99.94,
                "pricing_quality_score": 100.0,
                "market_structure_score": 95.36,
            }
        )
        self.assertEqual(scored["liquidity_score"], 99.94)
        self.assertEqual(scored["pricing_quality_score"], 100.0)
        self.assertEqual(scored["market_structure_score"], 95.36)

    def test_tiers(self):
        self.assertEqual(quality_tier(91), "institutional")
        self.assertEqual(liquidity_tier(None), "missing")
        self.assertEqual(risk_tier(70), "high_fragility")
        self.assertEqual(execution_readiness_tier(0), "prohibited")


if __name__ == "__main__":
    unittest.main()

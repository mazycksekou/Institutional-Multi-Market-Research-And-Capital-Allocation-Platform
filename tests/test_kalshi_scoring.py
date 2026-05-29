import unittest

from automation_scheduler.kalshi_scoring import KALSHI_LIQUIDITY_POLICY_VERSION, evaluate_kalshi_liquidity_policy, score_kalshi_candidate


class TestKalshiScoring(unittest.TestCase):
    def test_scores_complete_pricing(self):
        result = score_kalshi_candidate(
            {
                "implied_probability": 0.53,
                "yes_bid": 0.52,
                "yes_ask": 0.54,
                "volume": 4000,
                "open_interest": 5000,
                "liquidity_score": 0.8,
                "pricing_quality": "complete",
                "settlement_rule": "official_results",
                "status": "open",
            }
        )
        self.assertIn("review_priority_score", result)
        self.assertEqual(result["classification"], "review_only")
        self.assertEqual(result["liquidity_policy_version"], KALSHI_LIQUIDITY_POLICY_VERSION)
        for key in (
            "liquidity_score",
            "spread_score",
            "pricing_quality_score",
            "close_time_score",
            "market_structure_score",
            "risk_score",
            "confidence_score",
            "review_priority_score",
        ):
            self.assertGreaterEqual(result[key], 0)
            self.assertLessEqual(result[key], 100)

    def test_missing_pricing_is_data_insufficient(self):
        result = score_kalshi_candidate({"pricing_quality": "missing", "status": "open"})
        self.assertEqual(result["classification"], "data_insufficient")
        self.assertNotIn("confirmed", str(result).lower())

    def test_liquidity_policy_distinguishes_missing_from_low(self):
        missing = evaluate_kalshi_liquidity_policy({})
        self.assertEqual(missing["liquidity_tier"], "missing_liquidity")
        self.assertTrue(missing["missing_liquidity_flag"])
        self.assertFalse(missing["low_liquidity_flag"])

        very_low = evaluate_kalshi_liquidity_policy({"volume": 0, "open_interest": 0, "liquidity_score": 0.9})
        self.assertEqual(very_low["liquidity_source"], "volume_open_interest_proxy")
        self.assertEqual(very_low["liquidity_tier"], "low_liquidity")
        self.assertTrue(very_low["low_liquidity_flag"])
        self.assertFalse(very_low["missing_liquidity_flag"])

    def test_liquidity_policy_tiers_and_sources(self):
        direct = evaluate_kalshi_liquidity_policy({"liquidity_score": 0.82})
        self.assertEqual(direct["liquidity_source"], "direct_liquidity")
        self.assertEqual(direct["liquidity_tier"], "adequate_liquidity")

        low = evaluate_kalshi_liquidity_policy({"volume": 100, "open_interest": 100, "liquidity_score": 0.8})
        self.assertEqual(low["liquidity_tier"], "low_liquidity")

        moderate = evaluate_kalshi_liquidity_policy({"volume": 500, "open_interest": 500, "liquidity_score": 0.8})
        self.assertEqual(moderate["liquidity_tier"], "moderate_liquidity")

        adequate = evaluate_kalshi_liquidity_policy({"volume": 1000, "open_interest": 1000, "liquidity_score": 0.8})
        self.assertEqual(adequate["liquidity_tier"], "adequate_liquidity")

    def test_volume_fp_scale_is_not_double_scaled_after_normalization(self):
        policy = evaluate_kalshi_liquidity_policy({"volume": 1200, "open_interest": 900, "liquidity_score": 0.95})
        self.assertGreaterEqual(policy["volume_score"], 100)
        self.assertGreaterEqual(policy["open_interest_score"], 90)
        self.assertEqual(policy["liquidity_source"], "volume_open_interest_proxy")

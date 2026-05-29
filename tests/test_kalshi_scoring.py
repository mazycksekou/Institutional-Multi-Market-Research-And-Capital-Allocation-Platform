import unittest

from automation_scheduler.kalshi_scoring import score_kalshi_candidate


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

    def test_missing_pricing_is_data_insufficient(self):
        result = score_kalshi_candidate({"pricing_quality": "missing", "status": "open"})
        self.assertEqual(result["classification"], "data_insufficient")

import unittest

from automation_scheduler.opportunity_scoring import calculate_opportunity_score, classify_opportunity
from automation_scheduler.scheduler_config import get_default_scheduler_config


class TestOpportunityScoring(unittest.TestCase):
    def test_opportunity_score_range_and_thresholds(self):
        score = calculate_opportunity_score(
            {
                "edge_score": 9,
                "ev_score": 9,
                "line_value_score": 8,
                "arbitrage_score": 7,
                "middle_width_score": 7,
                "confidence_score": 8,
                "match_confidence_score": 9,
                "liquidity_score": 7,
                "movement_score": 9,
                "data_quality_score": 8,
                "market_depth_score": 7,
                "timing_score": 8,
                "model_fit_score": 7,
                "risk_score": 6,
                "volatility_score": 5,
                "source_consensus_score": 7,
                "execution_feasibility_score": 8,
                "expected_roi_score": 9,
                "stale_data_risk_score": 10,
            }
        )
        thresholds = get_default_scheduler_config()["score_thresholds"]
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)
        self.assertIn(classify_opportunity(score, thresholds), {"watch_recheck", "review_required", "urgent_review"})

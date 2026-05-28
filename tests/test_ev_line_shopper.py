import unittest
from tempfile import TemporaryDirectory

from automation_scheduler.ev_line_shopper import shop_ev_lines
from automation_scheduler.review_queue import build_review_item, upsert_review_item
from automation_scheduler.scheduler_config import get_default_scheduler_config


class TestEvLineShopper(unittest.TestCase):
    def test_ev_line_shopping_and_review_queue_fields(self):
        result = shop_ev_lines(
            [
                {"bookmaker": "DraftKings", "event": "Lakers vs Celtics", "market": "moneyline", "selection": "Lakers", "odds": 105},
                {"bookmaker": "FanDuel", "event": "Celtics @ Lakers", "market": "match winner", "selection": "Lakers", "odds": 120},
            ],
            model_probability=0.5,
        )
        self.assertTrue(result["candidate_found"])
        best = result["best_line_available"]
        self.assertEqual(best["best_book"], "fanduel")
        self.assertGreater(best["ev_percent"], 0)
        self.assertTrue(best["best_line_available"])

        with TemporaryDirectory() as tmp:
            config = get_default_scheduler_config(base_data_dir=tmp)
            best["opportunity_score"] = 72
            best["field_scores"] = {"ev_score": 9, "line_value_score": 8, "arbitrage_score": 0, "middle_width_score": 0, "confidence_score": 8, "match_confidence_score": 9, "liquidity_score": 8, "movement_score": 3, "data_quality_score": 8, "market_depth_score": 8, "timing_score": 6, "model_fit_score": 7, "risk_score": 7, "volatility_score": 6, "source_consensus_score": 6, "execution_feasibility_score": 7, "expected_roi_score": 9, "stale_data_risk_score": 10, "edge_score": 7}
            item = build_review_item(best, config)
            saved = upsert_review_item(config, item)
            self.assertEqual(saved["candidate_type"], "best_line_available")
            self.assertIn("books_compared", saved)
            self.assertIn("ev_percent", saved)
            self.assertIn("line_match_confidence", saved)

    def test_model_probability_required(self):
        result = shop_ev_lines(
            [{"bookmaker": "DraftKings", "event": "Lakers vs Celtics", "market": "moneyline", "selection": "Lakers", "odds": 105}],
            model_probability=None,
        )
        self.assertFalse(result["candidate_found"])

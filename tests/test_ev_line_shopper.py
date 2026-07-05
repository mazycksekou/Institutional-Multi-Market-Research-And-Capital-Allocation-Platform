import unittest
from tempfile import TemporaryDirectory

from src.services.streamlit_dashboard_facade import alt_line_ev, consensus_market_ev, model_ev, no_vig_market_ev, shop_ev_lines, stale_line_ev
from src.services.streamlit_dashboard_facade import build_review_item, upsert_review_item
from src.services.streamlit_dashboard_facade import get_default_scheduler_config


class TestEvLineShopper(unittest.TestCase):
    def setUp(self):
        self.offers = [
            {"bookmaker": "DraftKings", "event": "Lakers vs Celtics", "market": "moneyline", "selection": "Lakers", "odds": 105},
            {"bookmaker": "FanDuel", "event": "Celtics @ Lakers", "market": "match winner", "selection": "Lakers", "odds": 120, "timestamp": 100},
        ]

    def test_ev_subfamilies(self):
        self.assertTrue(model_ev(self.offers, model_probability=0.5)["candidate_found"])
        self.assertTrue(no_vig_market_ev(self.offers, fair_probability=0.5)["candidate_found"])
        self.assertTrue(consensus_market_ev(self.offers, probabilities=[0.48, 0.5, 0.52])["candidate_found"])
        self.assertTrue(alt_line_ev(self.offers, model_probability=0.5)["candidate_found"])
        stale = stale_line_ev(self.offers, model_probability=0.5)
        self.assertTrue(stale["candidate_found"])
        self.assertTrue(stale["best_line_available"]["stale_data_risk"])

    def test_no_ev_without_model_probability(self):
        result = shop_ev_lines(self.offers, model_probability=None)
        self.assertFalse(result["candidate_found"])

    def test_review_queue_stores_ev_fields(self):
        result = shop_ev_lines(self.offers, model_probability=0.5)
        best = result["best_line_available"]
        best["opportunity_score"] = 74
        best["field_scores"] = {"edge_score": 7, "ev_score": 9, "line_value_score": 8, "arbitrage_score": 0, "middle_width_score": 0, "confidence_score": 8, "model_confidence_score": 8, "match_confidence_score": 9, "market_identity_score": 9, "liquidity_score": 8, "movement_score": 3, "data_quality_score": 8, "market_depth_score": 7, "timing_score": 6, "model_fit_score": 7, "risk_score": 7, "volatility_score": 6, "source_consensus_score": 6, "execution_feasibility_score": 7, "expected_roi_score": 9, "stale_data_risk_score": 10, "settlement_risk_score": 10, "max_loss_score": 10}
        with TemporaryDirectory() as tmp:
            config = get_default_scheduler_config(base_data_dir=tmp)
            item = build_review_item(best, config)
            saved = upsert_review_item(config, item)
            self.assertEqual(saved["candidate_type"], "best_line_available")
            self.assertIn("best_book", saved)
            self.assertIn("worst_book", saved)
            self.assertIn("market_identity_confidence", saved)

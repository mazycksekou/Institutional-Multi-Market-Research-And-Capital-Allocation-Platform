import unittest

from automation_scheduler.middle_opportunity_detector import detect_middle_opportunity


class TestMiddleOpportunityDetector(unittest.TestCase):
    def test_spread_middle_is_detected(self):
        result = detect_middle_opportunity(
            {"bookmaker": "DraftKings", "event": "Lakers vs Celtics", "market": "spread", "selection": "Lakers", "line": -2.5, "odds": -110, "timestamp": 100},
            {"bookmaker": "FanDuel", "event": "Celtics @ Lakers", "market": "spread", "selection": "Celtics", "line": 4.5, "odds": -110, "timestamp": 110},
            market_identity_confidence=90,
            model_distribution={"middle_hit_probability": 0.2},
        )
        self.assertTrue(result["candidate_found"])
        self.assertEqual(result["candidate_type"], "middle_candidate")
        self.assertGreater(result["middle_width"], 0)

    def test_total_middle_is_detected(self):
        result = detect_middle_opportunity(
            {"bookmaker": "DraftKings", "event": "Lakers vs Celtics", "market": "total", "selection": "over", "line": 210.5, "odds": -110, "timestamp": 100},
            {"bookmaker": "FanDuel", "event": "Celtics @ Lakers", "market": "total", "selection": "under", "line": 214.5, "odds": -110, "timestamp": 110},
            market_identity_confidence=92,
            model_distribution={"middle_hit_probability": 0.25},
        )
        self.assertTrue(result["candidate_found"])
        self.assertEqual(result["middle_zone"], [210.5, 214.5])

    def test_middle_ev_can_be_positive_or_negative(self):
        positive = detect_middle_opportunity(
            {"bookmaker": "DraftKings", "event": "Lakers vs Celtics", "market": "total", "selection": "over", "line": 210.5, "odds": -110, "timestamp": 100},
            {"bookmaker": "FanDuel", "event": "Celtics @ Lakers", "market": "total", "selection": "under", "line": 214.5, "odds": -110, "timestamp": 110},
            market_identity_confidence=92,
            model_distribution={"middle_hit_probability": 0.3},
        )
        negative = detect_middle_opportunity(
            {"bookmaker": "DraftKings", "event": "Lakers vs Celtics", "market": "total", "selection": "over", "line": 210.5, "odds": -130, "timestamp": 100},
            {"bookmaker": "FanDuel", "event": "Celtics @ Lakers", "market": "total", "selection": "under", "line": 211.0, "odds": -130, "timestamp": 110},
            market_identity_confidence=92,
            model_distribution={"middle_hit_probability": 0.01},
        )
        self.assertTrue(positive["candidate_found"])
        self.assertFalse(negative["candidate_found"])
        self.assertEqual(negative["reason"], "negative_middle_ev")

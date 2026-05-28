import unittest

from automation_scheduler.middles.prop_middle import detect_prop_middle


class TestMiddleProp(unittest.TestCase):
    def test_prop_middle_detected(self):
        result = detect_prop_middle(
            {"bookmaker": "Book1", "event": "A vs B", "market": "player_points", "selection": "over", "line": 24.5, "odds": -110},
            {"bookmaker": "Book2", "event": "B @ A", "market": "player_points", "selection": "under", "line": 27.5, "odds": -110},
            market_identity_confidence=90,
            model_distribution={"middle_hit_probability": 0.2},
        )
        self.assertTrue(result["candidate_found"])

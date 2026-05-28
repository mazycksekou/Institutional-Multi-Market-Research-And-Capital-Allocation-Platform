import unittest

from automation_scheduler.middles.push_corridor_middle import detect_push_corridor_middle


class TestMiddlePushCorridor(unittest.TestCase):
    def test_push_corridor_middle_detected(self):
        result = detect_push_corridor_middle(
            {"bookmaker": "Book1", "event": "A vs B", "market": "total", "selection": "over", "line": 210.0, "odds": -110},
            {"bookmaker": "Book2", "event": "B @ A", "market": "total", "selection": "under", "line": 214.0, "odds": -110},
            market_identity_confidence=90,
            model_distribution={"middle_hit_probability": 0.2},
        )
        self.assertTrue(result["candidate_found"])
        self.assertTrue(result["push_corridor"])

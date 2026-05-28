import unittest

from automation_scheduler.middles.total_middle import detect_total_middle


class TestMiddleTotal(unittest.TestCase):
    def test_total_middle_detected(self):
        result = detect_total_middle(
            {"bookmaker": "Book1", "event": "A vs B", "market": "total", "selection": "over", "line": 210.5, "odds": -110},
            {"bookmaker": "Book2", "event": "B @ A", "market": "total", "selection": "under", "line": 214.5, "odds": -110},
            market_identity_confidence=90,
            model_distribution={"middle_hit_probability": 0.25},
        )
        self.assertTrue(result["candidate_found"])

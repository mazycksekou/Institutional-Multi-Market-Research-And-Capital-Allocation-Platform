import unittest

from automation_scheduler.middles.key_number_middle import detect_key_number_middle


class TestMiddleKeyNumber(unittest.TestCase):
    def test_key_number_middle_detected(self):
        result = detect_key_number_middle(
            {"bookmaker": "Book1", "event": "A vs B", "market": "spread", "selection": "A", "line": -2.5, "odds": -110},
            {"bookmaker": "Book2", "event": "B @ A", "market": "spread", "selection": "B", "line": 4.5, "odds": -110},
            market_identity_confidence=90,
            model_distribution={"middle_hit_probability": 0.2},
        )
        self.assertTrue(result["candidate_found"])
        self.assertIn(3, result["key_numbers_hit"])

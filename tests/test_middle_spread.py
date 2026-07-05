import unittest

from src.services.streamlit_dashboard_facade import detect_spread_middle


class TestMiddleSpread(unittest.TestCase):
    def test_spread_middle_detected(self):
        result = detect_spread_middle(
            {"bookmaker": "Book1", "event": "A vs B", "market": "spread", "selection": "A", "line": -2.5, "odds": -110},
            {"bookmaker": "Book2", "event": "B @ A", "market": "spread", "selection": "B", "line": 4.5, "odds": -110},
            market_identity_confidence=90,
            model_distribution={"middle_hit_probability": 0.2},
        )
        self.assertTrue(result["candidate_found"])

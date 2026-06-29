import unittest

from src.services.streamlit_dashboard_facade import detect_alt_line_middle


class TestMiddleAltLine(unittest.TestCase):
    def test_alt_line_middle_detected(self):
        result = detect_alt_line_middle(
            {"bookmaker": "Book1", "event": "A vs B", "market": "alt_total", "selection": "over", "line": 208.5, "odds": -110},
            {"bookmaker": "Book2", "event": "B @ A", "market": "alt_total", "selection": "under", "line": 214.5, "odds": -110},
            market_identity_confidence=90,
            model_distribution={"middle_hit_probability": 0.2},
        )
        self.assertTrue(result["candidate_found"])

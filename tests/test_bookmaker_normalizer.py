import unittest

from src.services.streamlit_dashboard_facade import normalize_bookmaker_name, normalize_entity_name, normalize_event_name, normalize_market_name, normalize_offer, normalize_selection_name, normalize_timestamp


class TestBookmakerNormalizer(unittest.TestCase):
    def test_normalizes_names_and_values(self):
        self.assertEqual(normalize_bookmaker_name("Draft Kings"), "draftkings")
        self.assertEqual(normalize_entity_name("Real Madrid CF"), "real madrid")
        self.assertEqual(normalize_event_name("Lakers @ Celtics"), "celtics vs lakers")
        self.assertEqual(normalize_market_name("Match Winner"), "moneyline")
        self.assertEqual(normalize_selection_name("O"), "over")
        self.assertIsInstance(normalize_timestamp("2026-05-28T12:00:00Z"), int)

    def test_normalize_offer(self):
        offer = normalize_offer(
            {
                "bookmaker": "FD",
                "event": "Yankees vs Red Sox",
                "team": "New York Yankees",
                "market": "Spread",
                "selection": "New York Yankees",
                "odds": "+110",
                "line": "-1.5",
                "timestamp": "2026-05-28T12:00:00Z",
            }
        )
        self.assertEqual(offer["bookmaker"], "fanduel")
        self.assertEqual(offer["odds"], 110)
        self.assertEqual(offer["line"], -1.5)
        self.assertIsInstance(offer["timestamp"], int)
        self.assertGreaterEqual(offer["normalization_confidence"], 85)

import unittest

from automation_scheduler.bookmaker_normalizer import (
    normalize_bookmaker_name,
    normalize_entity_name,
    normalize_event_name,
    normalize_market_name,
    normalize_offer,
    normalize_selection_name,
)


class TestBookmakerNormalizer(unittest.TestCase):
    def test_normalizes_names_and_values(self):
        self.assertEqual(normalize_bookmaker_name("Draft Kings"), "draftkings")
        self.assertEqual(normalize_entity_name("Real Madrid CF"), "real madrid")
        self.assertEqual(normalize_event_name("Lakers @ Celtics"), "celtics vs lakers")
        self.assertEqual(normalize_market_name("Match Winner"), "moneyline")
        self.assertEqual(normalize_selection_name("O"), "over")

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
            }
        )
        self.assertEqual(offer["bookmaker"], "fanduel")
        self.assertEqual(offer["odds"], 110)
        self.assertEqual(offer["line"], -1.5)

import unittest

from automation_scheduler.cross_book_line_comparator import compare_cross_book_lines


class TestCrossBookLineComparator(unittest.TestCase):
    def test_best_line_selection_and_spreads(self):
        result = compare_cross_book_lines(
            [
                {"bookmaker": "DraftKings", "event": "Lakers vs Celtics", "market": "moneyline", "selection": "Lakers", "odds": -110},
                {"bookmaker": "FanDuel", "event": "Lakers vs Celtics", "market": "moneyline", "selection": "Lakers", "odds": 105},
                {"bookmaker": "BetMGM", "event": "Lakers vs Celtics", "market": "moneyline", "selection": "Lakers", "odds": -120},
            ]
        )
        self.assertEqual(result["best_book"], "fanduel")
        self.assertEqual(result["best_odds"], 105)
        self.assertGreater(result["odds_spread"], 0)
        self.assertGreaterEqual(result["book_disagreement_score"], 0)

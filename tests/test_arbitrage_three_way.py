import unittest

from src.services.streamlit_dashboard_facade import detect_three_way_arbitrage


class TestArbitrageThreeWay(unittest.TestCase):
    def test_three_way_arb_works(self):
        result = detect_three_way_arbitrage(
            [
                {"bookmaker": "Book1", "event": "Team A vs Team B", "market": "moneyline_3way", "selection": "home", "odds": 260},
                {"bookmaker": "Book2", "event": "Team A vs Team B", "market": "moneyline_3way", "selection": "draw", "odds": 360},
                {"bookmaker": "Book3", "event": "Team A vs Team B", "market": "moneyline_3way", "selection": "away", "odds": 300},
            ]
        )
        self.assertTrue(result["candidate_found"])
        self.assertLess(result["arbitrage_implied_sum"], 1)

    def test_false_arb_blocked_by_vig(self):
        result = detect_three_way_arbitrage(
            [
                {"bookmaker": "Book1", "event": "Team A vs Team B", "market": "moneyline_3way", "selection": "home", "odds": 150},
                {"bookmaker": "Book2", "event": "Team A vs Team B", "market": "moneyline_3way", "selection": "draw", "odds": 250},
                {"bookmaker": "Book3", "event": "Team A vs Team B", "market": "moneyline_3way", "selection": "away", "odds": 180},
            ]
        )
        self.assertFalse(result["candidate_found"])

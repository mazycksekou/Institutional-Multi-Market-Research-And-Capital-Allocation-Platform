import unittest

from automation_scheduler.arbitrage.draw_market_arbitrage import detect_draw_market_arbitrage


class TestArbitrageDrawMarket(unittest.TestCase):
    def test_draw_market_arb_works(self):
        result = detect_draw_market_arbitrage(
            [
                {"bookmaker": "Book1", "event": "Team A vs Team B", "market": "draw_no_bet", "selection": "home", "odds": 260},
                {"bookmaker": "Book2", "event": "Team A vs Team B", "market": "draw_no_bet", "selection": "draw", "odds": 360},
                {"bookmaker": "Book3", "event": "Team A vs Team B", "market": "draw_no_bet", "selection": "away", "odds": 300},
            ]
        )
        self.assertTrue(result["candidate_found"])

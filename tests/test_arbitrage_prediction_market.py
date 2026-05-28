import unittest

from automation_scheduler.arbitrage.prediction_market_arbitrage import detect_prediction_market_vs_sportsbook_arbitrage


class TestArbitragePredictionMarket(unittest.TestCase):
    def test_prediction_market_vs_sportsbook_arb_works(self):
        result = detect_prediction_market_vs_sportsbook_arbitrage(
            sportsbook_odds_american=150,
            prediction_market_yes_price=0.35,
        )
        self.assertTrue(result["candidate_found"])
        self.assertLess(result["arbitrage_implied_sum"], 1)

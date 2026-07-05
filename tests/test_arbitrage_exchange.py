import unittest

from src.services.streamlit_dashboard_facade import detect_exchange_back_lay_arbitrage


class TestArbitrageExchange(unittest.TestCase):
    def test_exchange_back_lay_math_works(self):
        result = detect_exchange_back_lay_arbitrage(back_odds_american=150, lay_decimal_odds=2.2)
        self.assertTrue(result["candidate_found"])
        self.assertGreater(result["estimated_roi_percent"], 0)

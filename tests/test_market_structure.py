import unittest

from src.services.streamlit_dashboard_facade import kalshi_market_structure_signals, sportsbook_market_structure_signals


class TestMarketStructure(unittest.TestCase):
    def test_kalshi_signals(self):
        signals = kalshi_market_structure_signals(
            {"yes_bid": 0.48, "yes_ask": 0.52, "implied_probability": 0.50, "volume": 120, "open_interest": 220, "liquidity_score": 0.7, "status": "open"},
            {"implied_probability": 0.45, "volume": 100, "open_interest": 200, "liquidity_score": 0.6, "status": "open"},
        )
        self.assertIn("bid_ask_spread", signals)
        self.assertIn("probability_velocity", signals)
        self.assertEqual(signals["liquidity_tier"], "low_liquidity")
        self.assertFalse(signals["missing_liquidity_signal"])

    def test_sportsbook_signals(self):
        signals = sportsbook_market_structure_signals({"odds": -110, "line": -2.5, "book_disagreement_score": 5}, {"odds": -105, "line": -2.0})
        self.assertIn("line_movement", signals)

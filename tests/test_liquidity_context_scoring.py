import unittest

from src.services.streamlit_dashboard_facade import calculate_float_rotation, score_crypto_liquidity, score_stock_liquidity


class TestLiquidityContextScoring(unittest.TestCase):
    def test_stock_liquidity_scoring_and_float_rotation(self):
        scored = score_stock_liquidity(
            {
                "price": 6,
                "float_shares": 5_000_000,
                "daily_volume": 20_000_000,
                "relative_volume": 8,
                "spread_percent": 0.2,
                "bid_ask_depth": 300_000,
            }
        )
        self.assertGreaterEqual(scored["liquidity_score"], 70)
        self.assertEqual(scored["float_rotation"], 4.0)
        self.assertEqual(calculate_float_rotation(20_000_000, 5_000_000), 4.0)

    def test_stock_liquidity_below_40_has_blocker(self):
        scored = score_stock_liquidity(
            {
                "price": 1.5,
                "float_shares": 2_000_000,
                "daily_volume": 20_000,
                "relative_volume": 0.5,
                "spread_percent": 5.0,
                "bid_ask_depth": 0,
            }
        )
        self.assertLess(scored["liquidity_score"], 40)
        self.assertIn("liquidity_score_below_40", scored["liquidity_blockers"])

    def test_crypto_liquidity_scoring(self):
        scored = score_crypto_liquidity(
            {
                "volume_24h": 150_000_000,
                "relative_volume": 2.5,
                "exchange_count": 12,
                "order_book_depth_1pct": 7_000_000,
                "order_book_depth_2pct": 12_000_000,
                "spread_percent": 0.08,
                "slippage_estimate": 0.15,
            }
        )
        self.assertGreaterEqual(scored["liquidity_score"], 75)
        self.assertIn(scored["liquidity_tier"], {"strong", "institutional"})


if __name__ == "__main__":
    unittest.main()

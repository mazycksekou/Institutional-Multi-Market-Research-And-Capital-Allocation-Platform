import unittest
from datetime import datetime, timezone
from src.core.market_clock import market_open_status


class TestMarketClock(unittest.TestCase):
    def test_market_types_supported(self):
        now = datetime.now(timezone.utc)
        for t in ["sports", "player_props", "prediction_market", "stock", "news", "low_liquidity"]:
            r = market_open_status(t, now)
            self.assertIn("is_open", r)
            self.assertIn("reason", r)
            self.assertIn("next_check_allowed", r)

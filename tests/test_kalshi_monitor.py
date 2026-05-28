import unittest

from automation_scheduler.kalshi_monitor import monitor_kalshi_market
from automation_scheduler.scheduler_config import get_default_scheduler_config


class TestKalshiMonitor(unittest.TestCase):
    def test_detects_prediction_market_movement(self):
        config = get_default_scheduler_config()
        result = monitor_kalshi_market(
            previous_snapshot=[{"ticker": "KXTEST", "price": 44, "spread": 2, "order_book_imbalance": 0.1}],
            current_snapshot=[{"ticker": "KXTEST", "price": 52, "spread": 4, "order_book_imbalance": 0.4, "liquidity": 0.7}],
            provider="kalshi",
            config=config,
        )
        self.assertEqual(len(result["candidates"]), 1)
        self.assertEqual(result["candidates"][0]["market_type"], "prediction_markets")

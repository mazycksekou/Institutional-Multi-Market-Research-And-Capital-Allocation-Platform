import unittest

from automation_scheduler.scheduler_config import get_default_scheduler_config
from automation_scheduler.stock_monitor import monitor_stocks


class TestStockMonitor(unittest.TestCase):
    def test_detects_stock_movement(self):
        config = get_default_scheduler_config()
        result = monitor_stocks(
            previous_snapshot=[{"symbol": "NVDA", "price": 100, "volume_ratio": 1.0}],
            current_snapshot=[{"symbol": "NVDA", "price": 105, "volume_ratio": 2.0, "news_change_score": 3}],
            provider="alpaca",
            config=config,
        )
        self.assertEqual(len(result["candidates"]), 1)
        self.assertEqual(result["candidates"][0]["selection"], "NVDA")

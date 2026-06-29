import unittest

from src.services.streamlit_dashboard_facade import monitor_kalshi_market
from src.services.streamlit_dashboard_facade import get_default_scheduler_config


class TestKalshiMonitor(unittest.TestCase):
    def test_detects_prediction_market_movement(self):
        config = get_default_scheduler_config()
        result = monitor_kalshi_market(
            previous_snapshot=[{"ticker": "KXTEST", "contract_id": "KXTEST", "implied_probability": 0.44, "yes_price": 0.44, "liquidity_score": 0.7, "status": "open"}],
            current_snapshot=[{"ticker": "KXTEST", "contract_id": "KXTEST", "implied_probability": 0.52, "yes_price": 0.52, "yes_bid": 0.50, "yes_ask": 0.54, "liquidity_score": 0.7, "status": "open"}],
            provider="kalshi",
            config=config,
        )
        self.assertEqual(len(result["candidates"]), 1)
        self.assertEqual(result["candidates"][0]["market_type"], "prediction_market")

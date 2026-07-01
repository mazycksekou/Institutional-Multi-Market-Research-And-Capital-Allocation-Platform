from __future__ import annotations

import inspect
import unittest

from src.market_intelligence.prediction_market_manifold_mapper import map_prediction_market
from src.market_intelligence.prediction_markets import build_prediction_market_intelligence_report


class TestPhase10K8ZL4PredictionMarketIntelligenceAbsorption(unittest.TestCase):
    def test_prediction_market_outputs_exist(self):
        report = build_prediction_market_intelligence_report(
            {
                "yes_price": 0.62,
                "no_price": 0.38,
                "opening_probability": 0.50,
                "probability_movement": 0.12,
                "order_book_depth": 42,
                "volume": 1_000,
                "open_interest": 500,
                "holder_concentration": 0.25,
                "large_trades": ["buy"],
                "time_until_resolution": "3d",
                "news_catalysts": ["policy"],
                "probability_support": 0.58,
                "probability_resistance": 0.68,
                "buy_zone": 0.55,
                "sell_zone": 0.70,
                "take_profit_zone": 0.75,
                "breakout_probability": 0.40,
                "target_probability": 0.67,
                "invalidation_level": 0.52,
            }
        )
        self.assertEqual(report["yes_price"], 0.62)
        self.assertEqual(report["no_price"], 0.38)
        self.assertEqual(report["probability_support"], 0.58)
        self.assertEqual(report["probability_resistance"], 0.68)
        self.assertEqual(report["buy_zone"], 0.55)
        self.assertEqual(report["sell_zone"], 0.70)
        self.assertEqual(report["take_profit_zone"], 0.75)
        self.assertEqual(report["target_probability"], 0.67)
        self.assertEqual(report["invalidation_level"], 0.52)

    def test_manifold_mapper_imports_safely(self):
        mapped = map_prediction_market({"yes_price": 0.54})
        self.assertTrue(mapped["ok"])
        self.assertEqual(mapped["status"], "prediction_market_map_complete")
        self.assertFalse(mapped["provider_write"])
        self.assertFalse(mapped["execution_allowed"])

    def test_prediction_market_module_has_no_live_dependencies(self):
        import src.market_intelligence.prediction_markets as module

        source = inspect.getsource(module).lower()
        for token in ("requests", "httpx", "websocket", "openai", "deepseek", "anthropic"):
            self.assertNotIn(token, source)

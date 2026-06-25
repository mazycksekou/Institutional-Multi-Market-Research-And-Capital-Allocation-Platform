from __future__ import annotations

import inspect
import unittest

from src.market_intelligence import (
    STANDARD_REPORT_FIELDS,
    build_market_intelligence_report,
    build_market_state_graph,
    build_options_intelligence_report,
    build_prediction_market_intelligence_report,
    build_sports_intelligence_report,
    validate_market_intelligence_report,
)


class TestPhase10K8ZL2MarketIntelligenceFoundation(unittest.TestCase):
    def test_canonical_package_imports_and_builds(self):
        report = build_market_intelligence_report({"market": "stocks", "symbol_or_event": "ABC", "confidence": 55})
        self.assertTrue(set(STANDARD_REPORT_FIELDS).issubset(report))
        self.assertEqual(report["market"], "stocks")
        self.assertTrue(validate_market_intelligence_report(report)["ok"])

    def test_all_market_modules_import_safely(self):
        modules = [
            "src.market_intelligence",
            "src.market_intelligence.contracts",
            "src.market_intelligence.report",
            "src.market_intelligence.confidence",
            "src.market_intelligence.risk",
            "src.market_intelligence.targets",
            "src.market_intelligence.positioning",
            "src.market_intelligence.flow",
            "src.market_intelligence.liquidity",
            "src.market_intelligence.catalysts",
            "src.market_intelligence.regime",
            "src.market_intelligence.scoring",
            "src.market_intelligence.no_trade",
            "src.market_intelligence.options",
            "src.market_intelligence.sports",
            "src.market_intelligence.prediction_markets",
            "src.market_intelligence.futures",
            "src.market_intelligence.crypto",
            "src.market_intelligence.manifold",
            "src.market_intelligence.impact",
        ]
        forbidden = ("requests", "httpx", "websocket", "openai", "deepseek", "anthropic")
        for module_name in modules:
            module = __import__(module_name, fromlist=["*"])
            source = inspect.getsource(module)
            for token in forbidden:
                self.assertNotIn(token, source.lower(), module_name)

    def test_standardized_report_and_specialized_builders(self):
        sports = build_sports_intelligence_report(
            {
                "sport": "nba",
                "current_line": -3.5,
                "opening_line": -2.5,
                "consensus_line": -3.0,
                "target_spread": -4.5,
                "target_moneyline": -180,
                "target_total": 224.5,
                "confidence": 72,
            }
        )
        self.assertEqual(sports["target_spread"], -4.5)
        self.assertEqual(sports["target_moneyline"], -180)
        self.assertEqual(sports["target_total"], 224.5)
        self.assertIn("no_trade_reason", sports)

        pm = build_prediction_market_intelligence_report({"yes_price": 0.62, "probability_support": 0.58, "probability_resistance": 0.68})
        self.assertEqual(pm["yes_price"], 0.62)
        self.assertGreater(pm["confidence"], 0)

        options = build_options_intelligence_report(
            {
                "symbol": "ABC",
                "underlying_price": 100,
                "contracts": [{"option_type": "call", "open_interest": 10, "gamma": 0.1, "strike": 100, "days_to_expiry": 5}],
            }
        )
        self.assertIn("gex_profile", options)
        self.assertIn("vanna_profile", options)
        self.assertIn("gex_by_tenor", options)

        graph = build_market_state_graph({"asset_type": "prediction_market", "yes_price": 0.54})
        self.assertTrue(graph["ok"])
        self.assertEqual(graph["status"], "market_state_graph_complete")


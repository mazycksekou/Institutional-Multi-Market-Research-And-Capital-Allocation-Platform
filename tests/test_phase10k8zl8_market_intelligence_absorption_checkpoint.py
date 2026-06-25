from __future__ import annotations

import unittest
from pathlib import Path

from src.market_intelligence import (
    build_market_intelligence_report,
    build_options_intelligence_report,
    build_prediction_market_intelligence_report,
    build_sports_intelligence_report,
)


class TestPhase10K8ZL8MarketIntelligenceAbsorptionCheckpoint(unittest.TestCase):
    def test_checkpoint_docs_and_status(self):
        docs = [
            "PHASE10K8ZL2_MARKET_INTELLIGENCE_FOUNDATION.md",
            "PHASE10K8ZL3_SPORTS_INTELLIGENCE_ABSORPTION.md",
            "PHASE10K8ZL4_PREDICTION_MARKET_INTELLIGENCE_ABSORPTION.md",
            "PHASE10K8ZL5_OPTIONS_0DTE_GEX_VANNA_FOUNDATION.md",
            "PHASE10K8ZL6_MARKET_INTELLIGENCE_RUNTIME_TEST_REDIRECTION.md",
            "PHASE10K8ZL7_MARKET_INTELLIGENCE_SCHEDULER_DELETION.md",
            "PHASE10K8ZL8_MARKET_INTELLIGENCE_ABSORPTION_CHECKPOINT.md",
        ]
        for doc in docs:
            self.assertTrue(Path(doc).exists(), doc)

    def test_checkpoint_builders(self):
        self.assertEqual(build_market_intelligence_report({"market": "crypto"})["market"], "crypto")
        self.assertEqual(build_sports_intelligence_report({"sport": "nba", "current_line": -3.5})["market"], "sports betting")
        self.assertEqual(build_prediction_market_intelligence_report({"yes_price": 0.51})["market"], "prediction markets")
        self.assertEqual(build_options_intelligence_report({"symbol": "ABC", "underlying_price": 100, "contracts": []})["market"], "options/stocks")


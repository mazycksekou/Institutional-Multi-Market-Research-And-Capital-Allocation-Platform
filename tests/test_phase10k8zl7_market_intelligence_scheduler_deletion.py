from __future__ import annotations

import inspect
import unittest
from pathlib import Path

from src.market_intelligence import build_market_intelligence_report


class TestPhase10K8ZL7MarketIntelligenceSchedulerDeletion(unittest.TestCase):
    def test_no_scheduler_intelligence_file_was_deleted(self):
        candidate_paths = [
            "automation_scheduler/baseball_impact_common.py",
            "automation_scheduler/basketball_lineup_matchup_context.py",
            "automation_scheduler/basketball_market_relevance.py",
            "automation_scheduler/basketball_player_impact_common.py",
            "automation_scheduler/basketball_player_impact_red_team.py",
            "automation_scheduler/combat_impact_common.py",
            "automation_scheduler/football_impact_common.py",
            "automation_scheduler/football_impact_red_team.py",
            "automation_scheduler/football_impact_schema.py",
            "automation_scheduler/golf_impact_common.py",
            "automation_scheduler/hockey_impact_common.py",
            "automation_scheduler/soccer_impact_common.py",
            "automation_scheduler/tennis_impact_common.py",
            "automation_scheduler/manifold_review_queue.py",
            "automation_scheduler/market_state_graph.py",
            "automation_scheduler/prediction_market_manifold_mapper.py",
            "automation_scheduler/cross_asset_embedding_router.py",
        ]
        for rel_path in candidate_paths:
            self.assertTrue(Path(rel_path).exists(), rel_path)

    def test_canonical_market_intelligence_remains_safe(self):
        report = build_market_intelligence_report({"market": "prediction markets", "confidence": 45})
        self.assertEqual(report["market"], "prediction markets")
        self.assertFalse(report.get("provider_write", False))
        self.assertFalse(report.get("execution_allowed", False))


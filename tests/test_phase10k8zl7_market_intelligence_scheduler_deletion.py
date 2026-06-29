from __future__ import annotations

import inspect
import unittest
from pathlib import Path

from src.market_intelligence import build_market_intelligence_report


class TestPhase10K8ZL7MarketIntelligenceSchedulerDeletion(unittest.TestCase):
    def test_no_scheduler_intelligence_file_was_deleted(self):
        candidate_paths = [
            'src/automation_scheduler_legacy/baseball_impact_common.py',
            'src/automation_scheduler_legacy/basketball_lineup_matchup_context.py',
            'src/automation_scheduler_legacy/basketball_market_relevance.py',
            'src/automation_scheduler_legacy/basketball_player_impact_common.py',
            'src/automation_scheduler_legacy/basketball_player_impact_red_team.py',
            'src/automation_scheduler_legacy/combat_impact_common.py',
            'src/automation_scheduler_legacy/football_impact_common.py',
            'src/automation_scheduler_legacy/football_impact_red_team.py',
            'src/automation_scheduler_legacy/football_impact_schema.py',
            'src/automation_scheduler_legacy/golf_impact_common.py',
            'src/automation_scheduler_legacy/hockey_impact_common.py',
            'src/automation_scheduler_legacy/soccer_impact_common.py',
            'src/automation_scheduler_legacy/tennis_impact_common.py',
            'src/automation_scheduler_legacy/manifold_review_queue.py',
            'src/automation_scheduler_legacy/market_state_graph.py',
            'src/automation_scheduler_legacy/prediction_market_manifold_mapper.py',
            'src/automation_scheduler_legacy/cross_asset_embedding_router.py',
        ]
        for rel_path in candidate_paths:
            self.assertTrue(Path(rel_path).exists(), rel_path)

    def test_canonical_market_intelligence_remains_safe(self):
        report = build_market_intelligence_report({"market": "prediction markets", "confidence": 45})
        self.assertEqual(report["market"], "prediction markets")
        self.assertFalse(report.get("provider_write", False))
        self.assertFalse(report.get("execution_allowed", False))


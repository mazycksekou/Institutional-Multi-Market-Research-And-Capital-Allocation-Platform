from __future__ import annotations

import inspect
import unittest

from src.market_intelligence.sports import build_sports_intelligence_report, build_sports_no_trade, finalize_sports_response


class TestPhase10K8ZL3SportsIntelligenceAbsorption(unittest.TestCase):
    def test_sports_outputs_exist(self):
        report = build_sports_intelligence_report(
            {
                "sport": "football",
                "opening_line": -2.5,
                "current_line": -3.5,
                "consensus_line": -3.0,
                "tickets": 62,
                "money": 58,
                "handle": 61,
                "reverse_line_movement": True,
                "sharp_indicators": ["steam", "respected_money"],
                "injuries": ["qb_questionable"],
                "weather": "windy",
                "lineups": ["confirmed"],
                "limits": "tight",
                "closing_line_movement": "toward_favorite",
                "target_spread": -4.5,
                "target_moneyline": -180,
                "target_total": 44.5,
            }
        )
        self.assertEqual(report["target_spread"], -4.5)
        self.assertEqual(report["target_moneyline"], -180)
        self.assertEqual(report["target_total"], 44.5)
        self.assertIn("no_trade_reason", report)
        self.assertIn("confidence", report)
        self.assertIn("risk", report)
        self.assertIn("invalidation", report)

    def test_no_trade_and_finalize_helpers(self):
        no_trade = build_sports_no_trade({"confidence": 20, "risk": 80, "liquidity_score": 20, "regime": "risk_off"})
        self.assertTrue(no_trade["no_trade"])
        self.assertNotEqual(no_trade["no_trade_reason"], "none")

        payload = finalize_sports_response({"sport": "nba", "current_line": -3.5, "target_spread": -4.0})
        self.assertTrue(payload["provider_write"] is False)
        self.assertTrue(payload["human_approval_required"])

    def test_legacy_sports_wrappers_remain_importable(self):
        modules = [
            "automation_scheduler.baseball_impact_common",
            "automation_scheduler.basketball_lineup_matchup_context",
            "automation_scheduler.basketball_market_relevance",
            "automation_scheduler.basketball_player_impact_common",
            "automation_scheduler.basketball_player_impact_red_team",
            "automation_scheduler.combat_impact_common",
            "automation_scheduler.football_impact_common",
            "automation_scheduler.football_impact_red_team",
            "automation_scheduler.football_impact_schema",
            "automation_scheduler.golf_impact_common",
            "automation_scheduler.hockey_impact_common",
            "automation_scheduler.soccer_impact_common",
            "automation_scheduler.tennis_impact_common",
        ]
        for module_name in modules:
            module = __import__(module_name, fromlist=["*"])
            self.assertIsNotNone(module)
            self.assertTrue(module.__name__.startswith("automation_scheduler."))


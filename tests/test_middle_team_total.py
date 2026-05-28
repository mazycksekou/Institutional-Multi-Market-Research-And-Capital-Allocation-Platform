import unittest

from automation_scheduler.middles.team_total_middle import detect_team_total_middle


class TestMiddleTeamTotal(unittest.TestCase):
    def test_team_total_middle_detected(self):
        result = detect_team_total_middle(
            {"bookmaker": "Book1", "event": "A vs B", "market": "team_total", "selection": "over", "line": 102.5, "odds": -110},
            {"bookmaker": "Book2", "event": "B @ A", "market": "team_total", "selection": "under", "line": 105.5, "odds": -110},
            market_identity_confidence=90,
            model_distribution={"middle_hit_probability": 0.2},
        )
        self.assertTrue(result["candidate_found"])

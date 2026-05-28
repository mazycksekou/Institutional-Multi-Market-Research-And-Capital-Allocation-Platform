import unittest

from automation_scheduler.alert_engine import build_alert
from automation_scheduler.scheduler_config import get_default_scheduler_config


class TestAlertEngine(unittest.TestCase):
    def test_banned_language_forces_no_bet(self):
        thresholds = get_default_scheduler_config()["score_thresholds"]
        alert = build_alert({"opportunity_score": 90, "reason": "This is a guaranteed edge."}, thresholds)
        self.assertEqual(alert["recommended_action"], "no_bet")
        self.assertIn("contains_banned_language", alert["blockers"])
        self.assertTrue(alert["human_approval_required"])

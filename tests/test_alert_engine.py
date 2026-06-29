import unittest

from src.services.streamlit_dashboard_facade import build_alert, generate_alert_candidates
from src.services.streamlit_dashboard_facade import get_default_scheduler_config


class TestAlertEngine(unittest.TestCase):
    def test_banned_language_forces_no_bet(self):
        thresholds = get_default_scheduler_config()["score_thresholds"]
        alert = build_alert({"opportunity_score": 90, "reason": "This is a guaranteed edge."}, thresholds)
        self.assertEqual(alert["recommended_action"], "no_bet")
        self.assertIn("contains_banned_language", alert["blockers"])
        self.assertTrue(alert["human_approval_required"])

    def test_governance_block_forces_no_bet(self):
        thresholds = get_default_scheduler_config()["score_thresholds"]
        alert = build_alert({"opportunity_score": 90, "governance_status": "blocked_by_governance"}, thresholds)
        self.assertEqual(alert["recommended_action"], "no_bet")
        self.assertIn("blocked_by_governance", alert["blockers"])

    def test_alert_generation_dedupes(self):
        alerts = generate_alert_candidates(
            [
                {"id": "1", "provider_id": "kalshi_prediction_market", "ticker": "KX-1", "reason_codes": ["probability_move"], "recommendation_status": "review_only"},
                {"id": "2", "provider_id": "kalshi_prediction_market", "ticker": "KX-1", "reason_codes": ["probability_move"], "recommendation_status": "review_only"},
            ],
            time_bucket="bucket1",
        )
        self.assertEqual(len(alerts), 1)
        self.assertFalse(alerts[0]["execution_allowed"])

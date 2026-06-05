import unittest
from unittest.mock import patch

from automation_scheduler.soccer_sample_verifier import build_soccer_targeted_sample_verification_results


FAKE_LANES = [
    {"sport": "soccer", "lane_name": "schedule_results", "fields": ["stable_match_key"], "loader_exists": True, "candidate_source_name": "football-data.co.uk", "next_action": "backfill_approved_scope", "policy_status": "approved_free_open_transport", "free_or_paid_category": "free_open_populated", "retrieval_method": "residential_proxy", "entity_level": "match"},
    {"sport": "soccer", "lane_name": "injuries_availability", "fields": ["availability_status"], "loader_exists": False, "candidate_source_name": "Official page", "next_action": "create_manual_import_template", "policy_status": "manual_import_required", "free_or_paid_category": "free_open_manual_import_needed", "retrieval_method": "web_scraper_api", "entity_level": "player_match", "final_reason": "manual"},
]


class TestSoccerSampleVerifier(unittest.TestCase):
    def test_sample_report_counts_verified_and_blocked(self):
        with patch("automation_scheduler.soccer_sample_verifier.soccer_lane_catalog", return_value=FAKE_LANES), patch(
            "automation_scheduler.soccer_sample_verifier.load_soccer_lane_records",
            return_value={"ok": True, "normalized_records": [{"stable_match_key": "x"}], "normalized_record_count": 1, "oxylabs_used": True, "oxylabs_transport_used": "residential_proxy", "source_name": "football-data.co.uk"},
        ):
            report = build_soccer_targeted_sample_verification_results()
        self.assertEqual(report["sample_verified_count"], 1)
        self.assertEqual(report["sample_blocked_count"], 1)


if __name__ == "__main__":
    unittest.main()

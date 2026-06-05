import unittest

from automation_scheduler.nhl_sample_verifier import _sample_lane


class TestNhlSampleVerifier(unittest.TestCase):
    def test_manual_lane_keeps_manual_final_state(self):
        lane = {
            "sport": "icehockey_nhl",
            "lane_name": "injuries_availability",
            "free_or_paid_category": "free_open_manual_import_needed",
            "loader_exists": False,
            "fields": ["injury_status"],
            "candidate_source_name": "NHL team roster page",
            "retrieval_method": "web_scraper_api",
            "policy_status": "manual_import_only",
            "next_action": "create_manual_import_template",
            "final_reason": "manual only",
        }
        row = _sample_lane(lane)
        self.assertEqual(row["final_actionable_state"], "manual_import_required")

    def test_blocked_lane_keeps_policy_blocked_state(self):
        lane = {
            "sport": "icehockey_nhl",
            "lane_name": "restricted_reference_tables",
            "free_or_paid_category": "blocked_reference_or_restricted_source",
            "loader_exists": False,
            "fields": ["reference_duplicate_box_score"],
            "candidate_source_name": "Hockey Reference",
            "retrieval_method": "web_scraper_api",
            "policy_status": "blocked_reference_or_restricted_source",
            "next_action": "mark_policy_blocked",
            "final_reason": "blocked",
        }
        row = _sample_lane(lane)
        self.assertEqual(row["final_actionable_state"], "policy_blocked")


if __name__ == "__main__":
    unittest.main()

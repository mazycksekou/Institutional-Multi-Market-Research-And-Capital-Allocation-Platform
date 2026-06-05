import unittest
from unittest.mock import patch

from automation_scheduler.nhl_sample_verifier import build_nhl_targeted_sample_verification_results


FAKE_LANES = [
    {
        "sport": "icehockey_nhl",
        "lane_name": "team_box_scores",
        "free_or_paid_category": "free_open_populated",
        "loader_exists": True,
        "fields": ["game_id", "team_id", "team_score"],
        "candidate_source_name": "NHL public API",
        "retrieval_method": "residential_proxy",
        "policy_status": "approved_free_open_transport",
        "next_action": "backfill_approved_scope",
        "final_reason": "",
    }
]


class TestNhlTargetedSampleVerification(unittest.TestCase):
    def test_sample_report_marks_loader_lane_verified(self):
        with patch("automation_scheduler.nhl_sample_verifier.nhl_lane_catalog", return_value=FAKE_LANES), patch(
            "automation_scheduler.nhl_sample_verifier.load_nhl_lane_records",
            return_value={
                "ok": True,
                "normalized_records": [{"game_id": 1, "team_id": 2, "team_score": 3}],
                "normalized_record_count": 1,
                "oxylabs_used": True,
                "oxylabs_transport_used": "residential_proxy",
                "source_name": "NHL public API",
            },
        ):
            report = build_nhl_targeted_sample_verification_results()
        self.assertTrue(report["ok"])
        self.assertEqual(report["sample_verified_count"], 1)
        self.assertEqual(report["sample_results"][0]["validation_status"], "sample_verified")


if __name__ == "__main__":
    unittest.main()

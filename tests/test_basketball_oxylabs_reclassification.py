import tempfile
import unittest
from pathlib import Path

from automation_scheduler.basketball_oxylabs_audit import build_basketball_oxylabs_reclassification_report, write_basketball_oxylabs_reclassification_report


class TestBasketballOxylabsReclassification(unittest.TestCase):
    def test_reclassification_report_relabels_paid_manual_and_policy_rows(self):
        report = build_basketball_oxylabs_reclassification_report(
            source_exhaustion_report={
                "source_candidate_rows": [
                    {
                        "sport": "basketball_nba",
                        "lane_name": "injuries_availability",
                        "source_category": "paid_data_subscription_required",
                        "accepted_or_rejected": "accepted",
                        "rejection_reason": "",
                        "license_or_terms_note": "paid feed required",
                        "final_actionable_state": "paid_subscription_required",
                        "oxylabs_used": True,
                        "sample_attempted": True,
                        "normalized_records_found": 0,
                        "normalized_records_added": 0,
                    },
                    {
                        "sport": "basketball_wnba",
                        "lane_name": "lineup_on_off",
                        "source_category": "free_open_manual_import_needed",
                        "accepted_or_rejected": "accepted",
                        "rejection_reason": "",
                        "license_or_terms_note": "manual import required",
                        "final_actionable_state": "manual_import_required",
                        "oxylabs_used": True,
                        "sample_attempted": True,
                        "normalized_records_found": 2,
                        "normalized_records_added": 0,
                    },
                    {
                        "sport": "basketball_ncaab",
                        "lane_name": "restricted_reference_tables",
                        "source_category": "policy_blocked",
                        "accepted_or_rejected": "rejected",
                        "rejection_reason": "hard_policy_blocker",
                        "license_or_terms_note": "blocked reference site",
                        "final_actionable_state": "policy_blocked",
                        "oxylabs_used": False,
                        "sample_attempted": False,
                        "normalized_records_found": 0,
                        "normalized_records_added": 0,
                    },
                ]
            }
        )
        self.assertTrue(report["ok"])
        self.assertEqual(report["reclassification_row_count"], 3)
        self.assertEqual(report["paid_still_required_count"], 1)
        self.assertEqual(report["manual_import_still_required_count"], 1)
        self.assertEqual(report["policy_blocker_still_applies_count"], 1)

    def test_writer_creates_report_files(self):
        report = build_basketball_oxylabs_reclassification_report(
            source_exhaustion_report={
                "source_candidate_rows": [
                    {
                        "sport": "basketball_nba",
                        "lane_name": "injuries_availability",
                        "source_category": "paid_data_subscription_required",
                        "accepted_or_rejected": "accepted",
                        "rejection_reason": "",
                        "license_or_terms_note": "paid feed required",
                        "final_actionable_state": "paid_subscription_required",
                        "oxylabs_used": True,
                        "sample_attempted": True,
                        "normalized_records_found": 0,
                        "normalized_records_added": 0,
                    }
                ]
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_basketball_oxylabs_reclassification_report(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()

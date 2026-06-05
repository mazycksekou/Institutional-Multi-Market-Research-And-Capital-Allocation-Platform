import tempfile
import unittest
from pathlib import Path

from automation_scheduler.nhl_oxylabs_audit import build_nhl_oxylabs_reclassification_report, write_nhl_oxylabs_reclassification_report


SOURCE_REPORT = {
    "source_candidate_rows": [
        {"sport": "icehockey_nhl", "lane_name": "goalie_gsaax_dataset", "source_category": "paid_data_subscription_required", "oxylabs_transport_used": "web_scraper_api", "accepted_or_rejected": "accepted", "sample_attempted": False, "normalized_records_found": 0, "normalized_records_added": 0, "final_actionable_state": "paid_subscription_required", "rejection_reason": "", "license_or_terms_note": "paid"},
        {"sport": "icehockey_nhl", "lane_name": "injuries_availability", "source_category": "free_open_manual_import_needed", "oxylabs_transport_used": "web_scraper_api", "accepted_or_rejected": "accepted", "sample_attempted": False, "normalized_records_found": 0, "normalized_records_added": 0, "final_actionable_state": "manual_import_required", "rejection_reason": "", "license_or_terms_note": "manual"},
    ]
}


class TestNhlOxylabsReclassification(unittest.TestCase):
    def test_reclassification_counts_paid_and_manual(self):
        report = build_nhl_oxylabs_reclassification_report(source_exhaustion_report=SOURCE_REPORT)
        self.assertEqual(report["paid_still_required_count"], 1)
        self.assertEqual(report["manual_import_still_required_count"], 1)

    def test_writer_creates_files(self):
        report = build_nhl_oxylabs_reclassification_report(source_exhaustion_report=SOURCE_REPORT)
        with tempfile.TemporaryDirectory() as tmp:
            paths = write_nhl_oxylabs_reclassification_report(report, output_dir=Path(tmp) / "reports")
            self.assertTrue(Path(paths["latest_json_path"]).exists())
            self.assertTrue(Path(paths["latest_markdown_path"]).exists())


if __name__ == "__main__":
    unittest.main()

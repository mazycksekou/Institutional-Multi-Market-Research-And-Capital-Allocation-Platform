import unittest

from automation_scheduler.soccer_oxylabs_audit import build_soccer_oxylabs_reclassification_report


class TestSoccerOxylabsReclassification(unittest.TestCase):
    def test_reclassification_rows_are_built(self):
        report = build_soccer_oxylabs_reclassification_report(
            source_exhaustion_report={
                "source_candidate_rows": [
                    {"sport": "soccer", "lane_name": "injuries_availability", "source_category": "free_open_manual_import_needed", "oxylabs_transport_used": "web_scraper_api", "accepted_or_rejected": "accepted", "sample_attempted": False, "normalized_records_found": 0, "normalized_records_added": 0, "final_actionable_state": "manual_import_required", "rejection_reason": "", "license_or_terms_note": "manual"},
                    {"sport": "soccer", "lane_name": "tracking_360_context", "source_category": "paid_data_subscription_required", "oxylabs_transport_used": "web_scraper_api", "accepted_or_rejected": "accepted", "sample_attempted": False, "normalized_records_found": 0, "normalized_records_added": 0, "final_actionable_state": "paid_subscription_required", "rejection_reason": "", "license_or_terms_note": "paid"},
                ]
            }
        )
        self.assertEqual(report["reclassification_row_count"], 2)
        self.assertEqual(report["paid_still_required_count"], 1)


if __name__ == "__main__":
    unittest.main()

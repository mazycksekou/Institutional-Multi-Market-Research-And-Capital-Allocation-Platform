import unittest

from automation_scheduler.nfl_mlb_free_vs_paid_calibration import build_free_vs_paid_source_ledger


class TestNflMlbFreeVsPaidSourceLedger(unittest.TestCase):
    def test_source_ledger_exposes_summary_and_rows(self):
        sample = {
            "source_result_index": {
                "nflverse_schedules_results": {"sample_status": "sample_verified", "records_validated": 3, "fields_available": ["game_id"]},
                "retrosheet_schedules_results": {"sample_status": "sample_verified", "records_validated": 3, "fields_available": ["game_id"]},
                "nflverse_coaching_research": {"sample_status": "blocked", "blocked_reason": "terms_review_required", "records_validated": 0, "fields_available": []},
            },
            "provider_calls_attempted": 3,
            "downloads_attempted": 2,
            "downloads_succeeded": 2,
        }
        report = build_free_vs_paid_source_ledger(sample_verification_results=sample)
        self.assertTrue(report["ok"])
        self.assertIn("summary", report)
        self.assertGreater(report["summary"]["source_count"], 0)
        self.assertGreaterEqual(report["summary"]["sample_verified_source_count"], 2)
        self.assertIn("source_ledger_rows", report)
        self.assertTrue(any(row["source_id"] == "nflverse_schedules_results" for row in report["source_ledger_rows"]))


if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import patch

from automation_scheduler import nfl_mlb_free_vs_paid_calibration as mod


class TestNflMlbTargetedSampleVerification(unittest.TestCase):
    def test_aggregate_sample_verification_counts(self):
        with patch.object(mod, "build_mlb_retrosheet_sample_verification_report", return_value={"report_name": "MLB_RETROSHEET_SAMPLE_VERIFICATION_REPORT", "source_results": [{"source_id": "a", "sample_status": "sample_verified", "records_validated": 1, "fields_available": ["x"]}], "sample_verified_count": 1, "sample_blocked_count": 0, "sample_no_records_count": 0, "fields_verified_union": ["x"], "provider_calls_attempted": 1, "downloads_attempted": 1, "downloads_succeeded": 1}), patch.object(mod, "build_mlb_statcast_sample_verification_report", return_value={"report_name": "MLB_STATCAST_SAMPLE_VERIFICATION_REPORT", "source_results": [{"source_id": "b", "sample_status": "sample_verified", "records_validated": 1, "fields_available": ["y"]}], "sample_verified_count": 1, "sample_blocked_count": 0, "sample_no_records_count": 0, "fields_verified_union": ["y"], "provider_calls_attempted": 0, "downloads_attempted": 1, "downloads_succeeded": 1}), patch.object(mod, "build_mlb_official_public_web_sample_verification_report", return_value={"report_name": "MLB_OFFICIAL_PUBLIC_WEB_SAMPLE_VERIFICATION_REPORT", "source_results": [{"source_id": "c", "sample_status": "sample_verified", "records_validated": 1, "fields_available": ["z"]}], "sample_verified_count": 1, "sample_blocked_count": 0, "sample_no_records_count": 0, "fields_verified_union": ["z"], "provider_calls_attempted": 0, "downloads_attempted": 1, "downloads_succeeded": 1}), patch.object(mod, "build_mlb_draft_sample_verification_report", return_value={"report_name": "MLB_DRAFT_SAMPLE_VERIFICATION_REPORT", "source_results": [{"source_id": "d", "sample_status": "sample_verified_structure_only", "records_validated": 0, "fields_available": ["draft"]}], "sample_verified_count": 1, "sample_blocked_count": 0, "sample_no_records_count": 0, "fields_verified_union": ["draft"], "provider_calls_attempted": 1, "downloads_attempted": 1, "downloads_succeeded": 1}), patch.object(mod, "build_structured_wiki_sample_verification_report", return_value={"report_name": "STRUCTURED_WIKI_SAMPLE_VERIFICATION_REPORT", "source_results": [{"source_id": "e", "sample_status": "no_records", "records_validated": 0, "fields_available": []}], "sample_verified_count": 0, "sample_blocked_count": 0, "sample_no_records_count": 1, "fields_verified_union": [], "provider_calls_attempted": 1, "downloads_attempted": 0, "downloads_succeeded": 0}), patch.object(mod, "build_nflverse_sample_verification_report", return_value={"report_name": "NFLVERSE_SAMPLE_VERIFICATION_REPORT", "source_results": [{"source_id": "f", "sample_status": "sample_verified", "records_validated": 1, "fields_available": ["nfl"]}], "sample_verified_count": 1, "sample_blocked_count": 0, "sample_no_records_count": 0, "fields_verified_union": ["nfl"], "provider_calls_attempted": 1, "downloads_attempted": 1, "downloads_succeeded": 1}):
            report = mod.build_targeted_sample_verification_results()
        self.assertTrue(report["ok"])
        self.assertEqual(report["sample_verified_count"], 5)
        self.assertEqual(report["sample_no_records_count"], 1)
        self.assertIn("source_result_index", report)
        self.assertIn("a", report["source_result_index"])


if __name__ == "__main__":
    unittest.main()

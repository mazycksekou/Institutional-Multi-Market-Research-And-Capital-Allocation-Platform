import unittest
from unittest.mock import patch

from automation_scheduler.soccer_sample_verifier import build_soccer_targeted_sample_verification_results


class TestSoccerTargetedSampleVerification(unittest.TestCase):
    def test_targeted_report_records_total(self):
        with patch(
            "automation_scheduler.soccer_sample_verifier.load_soccer_lane_records",
            return_value={"ok": True, "normalized_records": [{"stable_match_key": "x", "division": "D1"}], "normalized_record_count": 1, "oxylabs_used": True, "oxylabs_transport_used": "residential_proxy", "source_name": "football-data.co.uk"},
        ):
            report = build_soccer_targeted_sample_verification_results()
        self.assertTrue(report["records_tested_total"] >= 1)


if __name__ == "__main__":
    unittest.main()

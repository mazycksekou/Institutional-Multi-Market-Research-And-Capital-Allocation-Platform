import unittest
from tests.ncaaf_test_support import ncaaf_artifacts

class TestNcaafSampleVerifier(unittest.TestCase):
    def test_sample_required_lanes_verified_or_blocked(self):
        report = ncaaf_artifacts()["sample_verification"]
        self.assertEqual(report["sample_failed_count"], 0)
        statuses = {row["lane_name"]: row["validation_status"] for row in report["sample_results"]}
        self.assertEqual(statuses["drive_summary_epa"], "sample_verified")
        self.assertEqual(statuses["play_by_play_epa"], "sample_verified")

if __name__ == "__main__":
    unittest.main()

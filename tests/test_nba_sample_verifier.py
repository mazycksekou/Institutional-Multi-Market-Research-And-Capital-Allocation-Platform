import unittest

from automation_scheduler.nba_sample_verifier import build_nba_sample_verification_report


class TestNbaSampleVerifier(unittest.TestCase):
    def test_nba_sample_report_is_distinct_and_verified(self):
        report = build_nba_sample_verification_report(run_live_samples=False)
        self.assertEqual(report["sport"], "basketball_nba")
        self.assertEqual(report["module"], "basketball_nba")
        self.assertGreater(report["sample_verified_count"], 0)
        self.assertTrue(any(row["lane_name"] == "schedule_results" for row in report["sample_results"]))


if __name__ == "__main__":
    unittest.main()

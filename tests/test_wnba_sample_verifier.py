import unittest

from automation_scheduler.wnba_sample_verifier import build_wnba_sample_verification_report


class TestWnbaSampleVerifier(unittest.TestCase):
    def test_wnba_sample_report_is_distinct_and_verified(self):
        report = build_wnba_sample_verification_report(run_live_samples=False)
        self.assertEqual(report["sport"], "basketball_wnba")
        self.assertEqual(report["module"], "basketball_wnba")
        self.assertGreater(report["sample_verified_count"], 0)
        self.assertTrue(any(row["lane_name"] == "lineup_on_off" for row in report["sample_results"]))


if __name__ == "__main__":
    unittest.main()

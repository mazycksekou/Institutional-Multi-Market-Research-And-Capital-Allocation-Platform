import unittest

from automation_scheduler.ncaaw_sample_verifier import build_ncaaw_sample_verification_report


class TestNcaawSampleVerifier(unittest.TestCase):
    def test_ncaaw_sample_report_is_distinct_and_verified(self):
        report = build_ncaaw_sample_verification_report(run_live_samples=False)
        self.assertEqual(report["sport"], "basketball_ncaaw")
        self.assertEqual(report["module"], "basketball_ncaaw")
        self.assertGreater(report["sample_verified_count"], 0)


if __name__ == "__main__":
    unittest.main()

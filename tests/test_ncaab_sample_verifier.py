import unittest

from automation_scheduler.ncaab_sample_verifier import build_ncaab_sample_verification_report


class TestNcaabSampleVerifier(unittest.TestCase):
    def test_ncaab_sample_report_is_distinct_and_verified(self):
        report = build_ncaab_sample_verification_report(run_live_samples=False)
        self.assertEqual(report["sport"], "basketball_ncaab")
        self.assertEqual(report["module"], "basketball_ncaab")
        self.assertGreater(report["sample_verified_count"], 0)


if __name__ == "__main__":
    unittest.main()

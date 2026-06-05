import unittest

from automation_scheduler.basketball_free_vs_paid_readiness import SPORTS, build_basketball_targeted_sample_verification_results


class TestBasketballTargetedSampleVerification(unittest.TestCase):
    def test_sample_required_lanes_attempted_or_hard_blocked(self):
        report = build_basketball_targeted_sample_verification_results(run_live_samples=False)
        self.assertTrue(report["ok"])
        self.assertEqual(set(report["by_sport"]), set(SPORTS))
        for row in report["sample_results"]:
            if row["sample_required"]:
                self.assertTrue(row["sample_attempted"] or row["hard_blocker"])
            if row["sample_type"] == "one_season":
                self.assertTrue(row["sample_attempted"])
        self.assertGreater(report["sample_verified_count"], 0)

    def test_no_raw_payload_or_secret_flags(self):
        report = build_basketball_targeted_sample_verification_results(run_live_samples=False)
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["raw_html_persisted"])
        self.assertFalse(report["secrets_included"])


if __name__ == "__main__":
    unittest.main()

import unittest

from tests.combat_test_support import combat_artifacts


class TestCombatSampleVerifier(unittest.TestCase):
    def test_sample_verification_runs(self):
        report = combat_artifacts()["sample_verification"]
        self.assertTrue(report["ok"])
        self.assertGreater(report["sample_verified_count"], 0)
        self.assertGreater(report["sample_blocked_count"], 0)
        self.assertEqual(report["sample_failed_count"], 0)
        statuses = {row["validation_status"] for row in report["sample_results"]}
        self.assertTrue(statuses.issubset({"sample_verified", "hard_blocked"}))


if __name__ == "__main__":
    unittest.main()

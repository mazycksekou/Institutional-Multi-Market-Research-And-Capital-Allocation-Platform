import unittest

from tests.tennis_test_support import tennis_artifacts


class TestTennisSampleVerifier(unittest.TestCase):
    def test_samples_are_only_verified_for_safe_or_metadata_paths(self):
        report = tennis_artifacts()["sample_verification"]
        self.assertGreaterEqual(report["sample_verified_count"], 1)
        blocked = [row for row in report["sample_results"] if row["validation_status"] == "hard_blocked"]
        self.assertTrue(blocked)
        metadata = [row for row in report["sample_results"] if row["final_actionable_state"] == "free_open_metadata_only"]
        self.assertTrue(metadata)


if __name__ == "__main__":
    unittest.main()

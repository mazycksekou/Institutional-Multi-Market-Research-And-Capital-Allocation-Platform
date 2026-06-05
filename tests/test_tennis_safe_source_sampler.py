import unittest

from tests.tennis_test_support import tennis_artifacts


class TestTennisSafeSourceSampler(unittest.TestCase):
    def test_only_accepted_sources_produce_sample_rows(self):
        report = tennis_artifacts()["safe_sample_report"]
        metadata_rows = [row for row in report["sample_rows"] if row["policy_decision"] == "accepted_for_metadata_only"]
        blocked_rows = [row for row in report["sample_rows"] if row["policy_decision"] == "license_terms_unclear"]
        self.assertTrue(metadata_rows)
        self.assertTrue(all(row["records_tested"] > 0 for row in metadata_rows))
        self.assertTrue(all(row["records_tested"] == 0 for row in blocked_rows))


if __name__ == "__main__":
    unittest.main()

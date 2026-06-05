import unittest

from tests.golf_test_support import golf_artifacts


class TestGolfSafeSourceSampler(unittest.TestCase):
    def test_sampling_is_policy_limited(self):
        report = golf_artifacts()["sample_report"]
        self.assertEqual(report["sample_row_count"], 15)
        self.assertGreaterEqual(report["metadata_only_records_added"], 2)
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["execution_allowed"])


if __name__ == "__main__":
    unittest.main()

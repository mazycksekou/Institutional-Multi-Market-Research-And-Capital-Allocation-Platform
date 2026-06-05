import unittest
from tests.ncaaf_test_support import ncaaf_artifacts

class TestNcaafSafeSourceSampler(unittest.TestCase):
    def test_sampler_is_policy_limited(self):
        report = ncaaf_artifacts()["sample_report"]
        self.assertEqual(report["sample_row_count"], 14)
        self.assertFalse(report["raw_payload_included"])
        self.assertFalse(report["execution_allowed"])

if __name__ == "__main__":
    unittest.main()

import unittest
from tests.ncaaf_test_support import ncaaf_artifacts

class TestNcaafFreeOpenExhaustionCertificate(unittest.TestCase):
    def test_certificate_gates(self):
        report = ncaaf_artifacts()["certificate"]
        self.assertTrue(report["all_candidate_paths_policy_reviewed"])
        self.assertTrue(report["all_loader_ready_lanes_backfilled_or_hard_blocked"])
        self.assertEqual(report["lanes_with_vague_status"], 0)
        self.assertEqual(report["unsafe_extraction_count"], 0)

if __name__ == "__main__":
    unittest.main()

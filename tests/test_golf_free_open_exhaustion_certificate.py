import unittest

from tests.golf_test_support import golf_artifacts


class TestGolfFreeOpenExhaustionCertificate(unittest.TestCase):
    def test_certificate_proves_finality(self):
        report = golf_artifacts()["certificate"]
        self.assertTrue(report["all_free_open_source_families_checked"])
        self.assertTrue(report["all_candidate_paths_policy_reviewed"])
        self.assertTrue(report["all_loader_ready_lanes_backfilled_or_hard_blocked"])
        self.assertEqual(report["lanes_with_vague_status"], 0)
        self.assertEqual(report["unsafe_extraction_count"], 0)


if __name__ == "__main__":
    unittest.main()

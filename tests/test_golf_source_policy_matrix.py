import unittest

from tests.golf_test_support import golf_artifacts


class TestGolfSourcePolicyMatrix(unittest.TestCase):
    def test_policy_decisions_are_final_and_safe(self):
        report = golf_artifacts()["policy_matrix"]
        self.assertEqual(report["candidate_paths_policy_reviewed_count"], 15)
        self.assertEqual(report["accepted_for_automated_normalized_backfill_count"], 1)
        self.assertEqual(report["accepted_for_manual_import_only_count"], 4)
        self.assertEqual(report["accepted_for_metadata_only_count"], 2)
        self.assertGreaterEqual(report["license_terms_unclear_count"], 3)
        self.assertFalse(report["raw_html_persisted"])
        self.assertFalse(report["secrets_included"])


if __name__ == "__main__":
    unittest.main()

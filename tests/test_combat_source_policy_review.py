import unittest

from automation_scheduler.combat_source_policy_review import combat_candidate_source_catalog
from tests.combat_test_support import combat_artifacts


class TestCombatSourcePolicyReview(unittest.TestCase):
    def test_every_candidate_has_one_final_policy_decision(self):
        report = combat_artifacts()["policy_matrix"]
        self.assertEqual(report["policy_matrix_row_count"], len(combat_candidate_source_catalog()))
        decisions = {row["path_level_decision"] for row in report["policy_matrix_rows"]}
        self.assertIn("accepted_for_automated_normalized_backfill", decisions)
        self.assertIn("accepted_for_manual_import_only", decisions)
        self.assertIn("accepted_for_metadata_only", decisions)
        self.assertIn("license_terms_unclear", decisions)
        self.assertNotIn("", decisions)
        self.assertEqual(report["candidate_paths_policy_reviewed_count"], len(combat_candidate_source_catalog()))


if __name__ == "__main__":
    unittest.main()

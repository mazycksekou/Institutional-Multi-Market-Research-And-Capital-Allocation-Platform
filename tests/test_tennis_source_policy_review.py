import unittest

from automation_scheduler.tennis_source_policy_review import tennis_candidate_source_catalog
from tests.tennis_test_support import tennis_artifacts


class TestTennisSourcePolicyReview(unittest.TestCase):
    def test_every_candidate_has_one_final_policy_decision(self):
        report = tennis_artifacts()["policy_matrix"]
        self.assertEqual(report["policy_matrix_row_count"], len(tennis_candidate_source_catalog()))
        decisions = {row["path_level_decision"] for row in report["policy_matrix_rows"]}
        self.assertIn("license_terms_unclear", decisions)
        self.assertIn("accepted_for_manual_import_only", decisions)
        self.assertIn("accepted_for_metadata_only", decisions)
        self.assertNotIn("", decisions)


if __name__ == "__main__":
    unittest.main()

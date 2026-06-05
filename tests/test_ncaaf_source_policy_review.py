import unittest
from tests.ncaaf_test_support import ncaaf_artifacts

class TestNcaafSourcePolicyReview(unittest.TestCase):
    def test_policy_review_docs_and_matrix_exist(self):
        artifacts = ncaaf_artifacts()
        self.assertTrue(artifacts["policy_docs_path"].exists())
        self.assertEqual(artifacts["policy_matrix"]["candidate_paths_policy_reviewed_count"], 14)

if __name__ == "__main__":
    unittest.main()

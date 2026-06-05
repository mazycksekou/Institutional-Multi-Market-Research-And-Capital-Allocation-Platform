import unittest
from tests.ncaaf_test_support import ncaaf_artifacts

class TestNcaafPolicyClassifier(unittest.TestCase):
    def test_key_decisions(self):
        rows = {row["source_id"]: row for row in ncaaf_artifacts()["policy_matrix"]["policy_matrix_rows"]}
        self.assertEqual(rows["ncaaf_cfbd_api_docs"]["path_level_decision"], "accepted_for_automated_normalized_backfill")
        self.assertEqual(rows["ncaaf_sports_reference_pages"]["final_state"], "policy_blocked")
        self.assertEqual(rows["ncaaf_paid_vendor"]["final_state"], "paid_subscription_required")

if __name__ == "__main__":
    unittest.main()

import unittest

from tests.golf_test_support import golf_artifacts


class TestGolfPolicyClassifier(unittest.TestCase):
    def test_classifier_outputs_expected_decision_mix(self):
        rows = golf_artifacts()["policy_matrix"]["policy_matrix_rows"]
        decisions = {row["source_id"]: row["path_level_decision"] for row in rows}
        self.assertEqual(decisions["golf_open_course_data"], "accepted_for_automated_normalized_backfill")
        self.assertEqual(decisions["golf_pga_tour_official_pages"], "accepted_for_manual_import_only")
        self.assertEqual(decisions["golf_wikidata_player_entities"], "accepted_for_metadata_only")
        self.assertEqual(decisions["golf_owgr_rankings"], "rejected_policy_blocked")


if __name__ == "__main__":
    unittest.main()

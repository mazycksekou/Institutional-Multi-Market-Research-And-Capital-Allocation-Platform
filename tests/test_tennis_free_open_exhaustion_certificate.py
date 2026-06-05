import unittest

from tests.tennis_test_support import tennis_artifacts


class TestTennisFreeOpenExhaustionCertificate(unittest.TestCase):
    def test_certificate_contains_required_success_flags(self):
        report = tennis_artifacts()["certificate"]
        self.assertTrue(report["no_more_free_open_search_required"])
        self.assertTrue(report["all_free_open_source_families_checked"])
        self.assertTrue(report["all_candidate_paths_policy_reviewed"])
        self.assertTrue(report["all_unresolved_lanes_oxylabs_checked_or_hard_blocked"])
        self.assertTrue(report["all_sample_required_lanes_verified_or_hard_blocked"])
        self.assertTrue(report["all_loader_ready_lanes_backfilled_or_hard_blocked"])
        self.assertTrue(report["all_paid_manual_policy_terms_lanes_rechecked"])
        self.assertTrue(report["all_lanes_have_final_actionable_state"])
        self.assertEqual(report["lanes_with_vague_status"], 0)
        self.assertEqual(report["unsafe_extraction_count"], 0)


if __name__ == "__main__":
    unittest.main()

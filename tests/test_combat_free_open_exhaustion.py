import unittest

from tests.combat_test_support import combat_artifacts


class TestCombatFreeOpenExhaustion(unittest.TestCase):
    def test_final_report_hits_required_finality_flags(self):
        report = combat_artifacts()["final_report"]
        self.assertIn(report["new_overall_verdict"], {"COMBAT_FINAL_FREE_OPEN_EXHAUSTED", "COMBAT_FINAL_NO_NEW_DATA_BUT_EXHAUSTED"})
        self.assertTrue(report["no_more_free_open_search_required"])
        self.assertTrue(report["all_free_open_source_families_checked"])
        self.assertTrue(report["all_candidate_paths_policy_reviewed"])
        self.assertTrue(report["all_unresolved_lanes_oxylabs_checked_or_hard_blocked"])
        self.assertTrue(report["all_sample_required_lanes_verified_or_hard_blocked"])
        self.assertTrue(report["all_loader_ready_lanes_backfilled_or_hard_blocked"])
        self.assertTrue(report["all_paid_manual_policy_terms_lanes_rechecked"])
        self.assertTrue(report["all_lanes_have_final_actionable_state"])
        self.assertTrue(report["remaining_actions_are_only_paid_manual_policy_or_acceptance"])
        self.assertTrue(report["free_open_sources_exhausted"])
        self.assertEqual(report["lanes_with_vague_status"], 0)
        self.assertEqual(report["unsafe_extraction_count"], 0)


if __name__ == "__main__":
    unittest.main()

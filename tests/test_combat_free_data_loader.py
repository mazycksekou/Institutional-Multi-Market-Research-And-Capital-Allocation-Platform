import unittest

from automation_scheduler.combat_free_data_loader import load_combat_lane_records
from automation_scheduler.combat_free_vs_paid_readiness import combat_lane_catalog
from tests.combat_test_support import combat_artifacts


class TestCombatFreeDataLoader(unittest.TestCase):
    def test_loader_returns_records_for_approved_lane_and_blocks_policy_lane(self):
        artifacts = combat_artifacts()
        approved_lane = next(lane for lane in combat_lane_catalog() if lane["lane_name"] == "boxing_bout_results")
        blocked_lane = next(lane for lane in combat_lane_catalog() if lane["lane_name"] == "mma_bout_results_context")
        approved_result = load_combat_lane_records(approved_lane, policy_matrix=artifacts["policy_matrix"])
        blocked_result = load_combat_lane_records(blocked_lane, policy_matrix=artifacts["policy_matrix"])
        self.assertTrue(approved_result["ok"])
        self.assertGreater(approved_result["normalized_record_count"], 0)
        self.assertFalse(blocked_result["ok"])
        self.assertEqual(blocked_result["status"], "blocked")


if __name__ == "__main__":
    unittest.main()

import unittest

from automation_scheduler.tennis_free_data_loader import load_tennis_lane_records
from automation_scheduler.tennis_free_vs_paid_readiness import default_tennis_loader_lanes
from tests.tennis_test_support import tennis_artifacts


class TestTennisFreeDataLoader(unittest.TestCase):
    def test_loader_refuses_unapproved_policy_states(self):
        lane = default_tennis_loader_lanes()[0]
        result = load_tennis_lane_records(lane, policy_matrix=tennis_artifacts()["policy_matrix"])
        self.assertFalse(result["ok"])
        self.assertIn("policy_final_state_", result["blocked_reason"])


if __name__ == "__main__":
    unittest.main()

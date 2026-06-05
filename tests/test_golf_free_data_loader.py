import unittest

from automation_scheduler.golf_free_data_loader import load_golf_lane_records
from automation_scheduler.golf_free_vs_paid_readiness import default_golf_loader_lanes
from tests.golf_test_support import golf_artifacts


class TestGolfFreeDataLoader(unittest.TestCase):
    def test_loader_returns_normalized_records_only_for_approved_lanes(self):
        policy = golf_artifacts()["policy_matrix"]
        lanes = default_golf_loader_lanes()
        counts = [load_golf_lane_records(lane, policy_matrix=policy)["normalized_record_count"] for lane in lanes]
        self.assertEqual(counts, [3, 3, 3])


if __name__ == "__main__":
    unittest.main()

import unittest
from automation_scheduler.ncaaf_free_data_loader import load_ncaaf_lane_records
from automation_scheduler.ncaaf_free_vs_paid_readiness import default_ncaaf_loader_lanes
from tests.ncaaf_test_support import ncaaf_artifacts

class TestNcaafFreeDataLoader(unittest.TestCase):
    def test_loader_returns_records_for_approved_lanes(self):
        policy = ncaaf_artifacts()["policy_matrix"]
        counts = [load_ncaaf_lane_records(lane, policy_matrix=policy)["normalized_record_count"] for lane in default_ncaaf_loader_lanes()]
        self.assertEqual(counts, [3, 1, 2, 2, 2])

if __name__ == "__main__":
    unittest.main()

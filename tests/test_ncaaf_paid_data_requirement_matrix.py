import unittest
from tests.ncaaf_test_support import ncaaf_artifacts

class TestNcaafPaidDataRequirementMatrix(unittest.TestCase):
    def test_paid_matrix_exists(self):
        report = ncaaf_artifacts()["paid_matrix"]
        self.assertEqual(report["paid_required_count"], 2)
        lanes = {row["lane_name"] for row in report["requirement_rows"]}
        self.assertIn("injury_availability_depth_chart_feed", lanes)

if __name__ == "__main__":
    unittest.main()

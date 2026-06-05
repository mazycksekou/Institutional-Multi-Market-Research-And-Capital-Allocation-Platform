import unittest

from tests.golf_test_support import golf_artifacts


class TestGolfPaidDataRequirementMatrix(unittest.TestCase):
    def test_paid_matrix_names_unresolved_vendor_lanes(self):
        report = golf_artifacts()["paid_matrix"]
        lanes = {row["lane_name"] for row in report["requirement_rows"]}
        self.assertEqual(report["paid_required_count"], 2)
        self.assertIn("strokes_gained_categories", lanes)
        self.assertIn("weather_wind_course_context", lanes)


if __name__ == "__main__":
    unittest.main()

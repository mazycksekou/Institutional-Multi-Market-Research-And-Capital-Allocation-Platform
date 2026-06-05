import unittest

from tests.golf_test_support import golf_artifacts


class TestGolfDataCalibrationReadinessReport(unittest.TestCase):
    def test_readiness_is_golf_specific_and_preserves_safety(self):
        model = golf_artifacts()["readiness"]["models"][0]
        self.assertEqual(model["model"], "strokes_gained_course_fit_monte_carlo_model")
        self.assertEqual(model["recommendation"], "manual_import_needed")
        self.assertIn("course_identity_metadata", model["model_inputs_strong"])
        self.assertEqual(model["player_prop_readiness"], "not_ready_without_paid_tracking_data")


if __name__ == "__main__":
    unittest.main()

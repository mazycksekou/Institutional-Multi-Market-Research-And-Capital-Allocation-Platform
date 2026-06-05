import unittest
from tests.ncaaf_test_support import ncaaf_artifacts

class TestNcaafDataCalibrationReadinessReport(unittest.TestCase):
    def test_readiness_model_and_safety(self):
        report = ncaaf_artifacts()["readiness"]
        model = report["models"][0]
        self.assertEqual(model["model"], "college_football_epa_drive_rating_monte_carlo_model")
        self.assertEqual(model["recommendation"], "manual_import_needed")
        self.assertIn("drive_summary_epa", model["model_inputs_strong"])
        self.assertFalse(report["provider_write"])

if __name__ == "__main__":
    unittest.main()

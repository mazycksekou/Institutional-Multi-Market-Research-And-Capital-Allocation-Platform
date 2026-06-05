import unittest

from tests.combat_test_support import combat_artifacts


class TestCombatDataCalibrationReadinessReport(unittest.TestCase):
    def test_readiness_report_has_model(self):
        report = combat_artifacts()["readiness_report"]
        model = report["models"][0]
        self.assertEqual(model["model"], "fighter_striking_grappling_finish_model")
        self.assertEqual(model["recommendation"], "manual_import_needed")
        self.assertIn("fighter_identity_readiness", model)
        self.assertFalse(report["provider_write"])
        self.assertFalse(report["execution_allowed"])


if __name__ == "__main__":
    unittest.main()

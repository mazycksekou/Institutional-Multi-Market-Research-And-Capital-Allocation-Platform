import unittest

from automation_scheduler.basketball_free_vs_paid_readiness import SPORTS, build_basketball_data_calibration_readiness_report


class TestBasketballDataCalibrationReadinessReport(unittest.TestCase):
    def test_readiness_report_covers_models_and_preserves_behavior(self):
        report = build_basketball_data_calibration_readiness_report()
        self.assertTrue(report["ok"])
        self.assertEqual({row["sport"] for row in report["models"]}, set(SPORTS))
        behavior = report["preserved_model_behavior"]
        self.assertTrue(behavior["odds_stability"])
        self.assertTrue(behavior["missing_partial_bad_input_no_500"])
        self.assertTrue(behavior["confirmed_bets_no_bets_mutual_exclusivity"])
        self.assertTrue(behavior["NO_BET_suggested_stake_zero"])
        self.assertTrue(behavior["screenshot_analysis_parity"])
        self.assertIn("probability_cap_reason", behavior["calibration_fields"])


if __name__ == "__main__":
    unittest.main()

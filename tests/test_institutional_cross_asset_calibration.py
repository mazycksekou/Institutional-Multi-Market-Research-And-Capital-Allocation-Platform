import unittest

from src.analytics.institutional_cross_asset_calibration import calibrate_asset_class


class TestInstitutionalCrossAssetCalibration(unittest.TestCase):
    def test_zero_outcomes_is_insufficient(self):
        report = calibrate_asset_class([], "prediction_market")
        self.assertEqual(report["status"], "insufficient_data")
        self.assertTrue(report["insufficient_sample"])
        self.assertEqual(report["metrics"], {})

    def test_partial_prediction_market_outcomes_emit_brier_only_for_labels(self):
        rows = [
            {
                "asset_class": "prediction_market",
                "outcome_status": "settled",
                "final_outcome": "yes",
                "implied_probability": 0.7,
                "liquidity_tier": "adequate_liquidity",
            },
            {
                "asset_class": "prediction_market",
                "outcome_status": "pending",
                "final_outcome": None,
                "implied_probability": 0.2,
            },
        ]
        report = calibrate_asset_class(rows, "prediction_market")
        self.assertEqual(report["status"], "partial_calibration")
        self.assertEqual(report["matched_outcomes_count"], 1)
        self.assertIn("brier_score", report["metrics"])

    def test_metrics_ready_only_after_threshold(self):
        rows = [
            {
                "asset_class": "prediction_market",
                "outcome_status": "settled",
                "final_outcome": "yes" if i % 2 else "no",
                "implied_probability": 0.55,
            }
            for i in range(30)
        ]
        report = calibrate_asset_class(rows, "prediction_market")
        self.assertEqual(report["status"], "metrics_ready")
        self.assertFalse(report["insufficient_sample"])

    def test_stock_metrics_require_final_price(self):
        missing = calibrate_asset_class(
            [{"asset_class": "stock", "observed_price": 100, "outcome_status": "completed"}],
            "stock",
        )
        self.assertEqual(missing["status"], "insufficient_data")
        self.assertEqual(missing["metrics"], {})
        ready = calibrate_asset_class(
            [{"asset_class": "stock", "observed_price": 100, "final_price": 105, "liquidity_tier": "high_liquidity"}],
            "stock",
        )
        self.assertEqual(ready["status"], "partial_calibration")
        self.assertIn("average_forward_return_pct", ready["metrics"])

    def test_sportsbook_requires_settled_result(self):
        missing = calibrate_asset_class(
            [{"asset_class": "sportsbook", "outcome_status": "pending", "final_outcome": None}],
            "sportsbook",
        )
        self.assertEqual(missing["status"], "insufficient_data")
        settled = calibrate_asset_class(
            [
                {"asset_class": "sportsbook", "outcome_status": "settled", "final_outcome": "win"},
                {"asset_class": "sportsbook", "outcome_status": "settled", "final_outcome": "push"},
            ],
            "sportsbook",
        )
        self.assertEqual(settled["matched_outcomes_count"], 2)
        self.assertIn("hit_rate", settled["metrics"])


if __name__ == "__main__":
    unittest.main()

import unittest

from automation_scheduler.institutional_risk_engine import RISK_CATEGORIES, assess_institutional_risk, sample_risk_output


class TestInstitutionalRiskEngine(unittest.TestCase):
    def test_risk_categories_and_hard_blocks(self):
        result = assess_institutional_risk(
            {
                "asset_class": "prediction_market",
                "provider": "kalshi_prediction_market",
                "liquidity_score": 10,
                "pricing_quality_score": 20,
                "market_structure_score": 30,
                "confidence_score": 25,
                "settlement_quality_score": 40,
                "risk_score": 80,
                "reason_codes": ["stale_price", "settlement_unknown"],
            },
            calibration_report={"asset_classes": {"prediction_market": {"matched_outcomes_count": 0}}},
        )
        for category in RISK_CATEGORIES:
            self.assertIn(category, result["risk_categories"])
        for block in ("low_liquidity", "low_pricing_quality", "missing_outcome_path", "high_risk_tier", "insufficient_calibration_sample"):
            self.assertIn(block, result["risk_blocks"])
        self.assertTrue(result["execution_blocked"])
        self.assertFalse(result["provider_write"])
        self.assertFalse(result["execution_allowed"])

    def test_sample_risk_output_is_compact_and_blocked(self):
        result = sample_risk_output()
        self.assertTrue(result["execution_blocked"])
        self.assertEqual(result["block_reason"], "simulation_only")


if __name__ == "__main__":
    unittest.main()

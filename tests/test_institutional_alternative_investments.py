import unittest

from src.analytics.institutional.alternative_investments import OUTPUT_FIELDS, get_models, run_model


class TestInstitutionalAlternativeInvestments(unittest.TestCase):
    def test_models_have_required_metadata(self):
        models = get_models()
        self.assertEqual(len(models), 12)
        for model in models.values():
            self.assertEqual(model["output_fields"], OUTPUT_FIELDS)

    def test_alternative_model_scores_illiquidity(self):
        result = run_model(
            "illiquidity_premium_model",
            {
                "target_allocation": 0.35,
                "available_liquidity": 5,
                "commitment_base": 20,
                "manager_quality_score": 82,
                "vintage_count": 3,
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertGreater(result["illiquidity_risk"], 0)


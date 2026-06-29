import unittest

from src.analytics.institutional.portfolio_construction import OUTPUT_FIELDS, get_models, run_model


class TestInstitutionalPortfolioConstruction(unittest.TestCase):
    def test_models_have_required_metadata_and_default_activation(self):
        models = get_models()
        self.assertEqual(len(models), 15)
        for model in models.values():
            self.assertEqual(model["activation_status"], "research_only")
            self.assertTrue(model["mathematical_purpose"])
            self.assertTrue(model["required_inputs"])
            self.assertEqual(model["output_fields"], OUTPUT_FIELDS)
            self.assertTrue(model["assumptions"])
            self.assertTrue(model["limitations"])

    def test_portfolio_model_outputs_required_fields(self):
        result = run_model(
            "mean_variance_optimization",
            {
                "expected_returns": [0.08, 0.06, 0.04],
                "volatility_estimates": [0.18, 0.12, 0.07],
                "constraints": ["max_weight:0.6"],
                "asset_universe": ["equity", "credit", "treasury"],
            },
        )
        self.assertEqual(result["status"], "ok")
        self.assertEqual(set(result.keys()) - {"status"}, set(OUTPUT_FIELDS))
        self.assertAlmostEqual(sum(result["portfolio_weights"].values()), 1.0, places=4)

